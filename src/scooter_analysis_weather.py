from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta


def read_large_csv(file_path, sample_rate=100):
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=100000):
        chunks.append(chunk.iloc[::sample_rate])
    return pd.concat(chunks)


def simulate_temperature(df):
    """
    Simulate temperature based on timestamp:
    - Base temperature: 10°C
    - Daily variation: cooler at night, warmer during day (±5°C)
    - Seasonal variation: cooler in winter, warmer in summer (±10°C)
    """
    np.random.seed(4)

    timestamps = pd.to_datetime(df["timestamp"])

    # Temperature: Daily and seasonal variation
    day_of_year = timestamps.dt.dayofyear
    hour_of_day = timestamps.dt.hour

    # Base temperature with seasonal variation
    base_temp = 10 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)

    # Add hourly variation (peak at 2PM)
    hourly_temp = 5 * np.sin(2 * np.pi * (hour_of_day - 14) / 24)

    temperature = base_temp + hourly_temp + np.random.normal(0, 2, len(df))

    # Clipping to realistic range based on Stcokholm
    return pd.DataFrame({"temperature": np.clip(temperature, 0, 20)})


def create_acceleration_speed_analysis(scooters_data, output_dir):
    """Create speed vs acceleration analysis with temperature effects"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 20))
    fig.suptitle("Speed vs Acceleration Analysis with Temperature Impact", size=16)
    colors = ["#FF0000", "#00FF00", "#00FFFF"]

    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        axes[0, 0].scatter(
            df["speed"],
            df["acceleration"],
            alpha=0.1,
            color=colors[idx],
            label=f"Scooter {scooter_id}",
        )

        # Temperature impact
        temp_bins = pd.cut(df["temperature"], bins=5)
        for temp_bin in temp_bins.unique():
            temp_data = df[temp_bins == temp_bin]
            axes[0, 1].scatter(
                temp_data["speed"],
                temp_data["acceleration"],
                alpha=0.1,
                label=f"{scooter_id}-Temp:{temp_bin.left:.1f}-{temp_bin.right:.1f}°C",
            )

        # Temperature vs Acceleration
        axes[1, 0].scatter(
            df["temperature"],
            df["acceleration"],
            alpha=0.1,
            color=colors[idx],
            label=f"Scooter {scooter_id}",
        )

        # Average Acceleration by Temperature Range
        temp_bins = pd.cut(df["temperature"], bins=10)
        acc_by_temp = df.groupby(temp_bins, observed=False)["acceleration"].mean()
        axes[1, 1].plot(
            range(len(acc_by_temp)),
            acc_by_temp.values,
            marker="o",
            color=colors[idx],
            label=f"Scooter {scooter_id}",
        )

    axes[0, 0].set_title("Speed vs Acceleration (Overall)")
    axes[0, 0].set_xlabel("Speed (km/h)")
    axes[0, 0].set_ylabel("Acceleration (m/s²)")

    axes[0, 1].set_title("Speed vs Acceleration by Temperature Range")
    axes[0, 1].set_xlabel("Speed (km/h)")
    axes[0, 1].set_ylabel("Acceleration (m/s²)")

    axes[1, 0].set_title("Temperature Effect on Acceleration")
    axes[1, 0].set_xlabel("Temperature (°C)")
    axes[1, 0].set_ylabel("Acceleration (m/s²)")

    axes[1, 1].set_title("Average Acceleration Across Temperature Ranges")
    axes[1, 1].set_xlabel("Temperature Range (Low → High)")
    axes[1, 1].set_ylabel("Average Acceleration (m/s²)")

    for ax in axes.flat:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "speed_acceleration_temperature.png", bbox_inches="tight")
    plt.close()


def create_battery_performance_analysis(scooters_data, output_dir):
    """Create battery performance analysis with temperature impact"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 20))
    fig.suptitle("Battery Performance Analysis with Temperature", size=16)
    colors = ["#FF0000", "#00FF00", "#00FFFF"]

    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        # Battery Level vs Temperature
        axes[0, 0].scatter(
            df["temperature"],
            df["battery_level"],
            alpha=0.1,
            color=colors[idx],
            label=scooter_id,
        )

        # Battery Drain Rate by Temperature
        temp_bins = pd.cut(df["temperature"], bins=5)
        battery_drain = df.groupby(temp_bins, observed=False)["battery_level"].mean()
        axes[0, 1].plot(
            range(len(battery_drain)),
            battery_drain.values,
            marker="o",
            color=colors[idx],
            label=scooter_id,
        )

        # Energy Impact vs Temperature
        df["energy_impact"] = np.abs(df["acceleration"])
        temp_bins = pd.cut(df["temperature"], bins=10)
        energy_by_temp = df.groupby(temp_bins, observed=False)["energy_impact"].mean()
        axes[1, 0].plot(
            range(len(energy_by_temp)),
            energy_by_temp.values,
            marker="o",
            color=colors[idx],
            label=scooter_id,
        )

        # Battery Efficiency vs Temperature
        df["battery_efficiency"] = df["battery_level"].diff() / (df["speed"] + 0.1)
        efficiency_by_temp = df.groupby(temp_bins, observed=False)[
            "battery_efficiency"
        ].mean()
        axes[1, 1].plot(
            range(len(efficiency_by_temp)),
            efficiency_by_temp.values,
            marker="o",
            color=colors[idx],
            label=scooter_id,
        )

    axes[0, 0].set_title("Battery Level vs Temperature")
    axes[0, 0].set_xlabel("Temperature (°C)")
    axes[0, 0].set_ylabel("Battery Level (%)")

    axes[0, 1].set_title("Average Battery Level by Temperature Range")
    axes[0, 1].set_xlabel("Temperature Range (Low → High)")
    axes[0, 1].set_ylabel("Average Battery Level (%)")

    axes[1, 0].set_title("Energy Consumption vs Temperature")
    axes[1, 0].set_xlabel("Temperature Range (Low → High)")
    axes[1, 0].set_ylabel("Average Energy Consumption (Absolute Acceleration)")

    axes[1, 1].set_title("Battery Efficiency vs Temperature")
    axes[1, 1].set_xlabel("Temperature Range (Low → High)")
    axes[1, 1].set_ylabel("Battery Efficiency (Δ% per speed unit)")

    for ax in axes.flat:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "battery_performance_temperature.png", bbox_inches="tight")
    plt.close()


def create_battery_state_smoothed(scooters_data, output_dir, window=20):
    """Create battery state analysis with temperature overlay"""
    for scooter_id, df in scooters_data.items():
        states = df["state"].unique()
        fig, axes = plt.subplots(
            len(states), 1, figsize=(15, 5 * len(states)), sharex=True
        )
        if len(states) == 1:
            axes = [axes]

        fig.suptitle(
            f"Scooter {scooter_id}: Battery Level and Temperature Time Series Analysis",
            size=16,
        )

        for i, state in enumerate(states):
            state_df = df[df["state"] == state].copy()

            # Battery level plot with time
            state_df["battery_level_smoothed"] = (
                state_df["battery_level"].rolling(window=window).mean()
            )
            axes[i].plot(
                state_df["timestamp"],
                state_df["battery_level_smoothed"],
                label=f"{state} (smoothed)",
                color="blue",
            )

            # Temperature overlay with time
            ax2 = axes[i].twinx()
            ax2.plot(
                state_df["timestamp"],
                state_df["temperature"],
                color="red",
                alpha=0.3,
                label="Temperature",
            )

            axes[i].set_title(
                f"Battery Level During {state} State with Temperature Overlay"
            )
            axes[i].set_xlabel("Time (UTC)")
            axes[i].set_ylabel("Battery Level (%)", color="blue")
            ax2.set_ylabel("Temperature (°C)", color="red")
            axes[i].grid(True)

            lines1, labels1 = axes[i].get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        plt.tight_layout()
        plt.savefig(
            output_dir / f"battery_state_temperature_{scooter_id}.png",
            bbox_inches="tight",
        )
        plt.close()


def analyze_scooter_data(file_paths):
    output_dir = Path() / "analysis_output_temperature"
    output_dir.mkdir(parents=True, exist_ok=True)

    scooters_data = {}
    for file_path in file_paths:
        print(f"Processing {file_path}...")
        df = read_large_csv(file_path)
        scooter_id = df["scooter_id"].iloc[0]
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Add simulated temperature data
        df = pd.concat([df, simulate_temperature(df)], axis=1)

        scooters_data[scooter_id] = df

    create_acceleration_speed_analysis(scooters_data, output_dir)
    create_battery_performance_analysis(scooters_data, output_dir)
    create_battery_state_smoothed(scooters_data, output_dir)


def main():
    file_paths = [
        Path() / "data/telemetry_data_001.csv",
        Path() / "data/telemetry_data_002.csv",
        Path() / "data/telemetry_data_003.csv",
    ]

    try:
        print("Starting analysis with temperature simulation...")
        analyze_scooter_data(file_paths)
        print("\nAnalysis complete! Check the 'analysis_output_temperature' directory.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
