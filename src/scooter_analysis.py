from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def read_large_csv(file_path, sample_rate=100):
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=100000):
        chunks.append(chunk.iloc[::sample_rate])
    return pd.concat(chunks)


def analyze_scooter_data(file_paths):
    # plt.style.use('classic')
    output_dir = Path() / "analysis_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    scooters_data = {}
    for file_path in file_paths:
        print(f"Processing {file_path}...")

        df = read_large_csv(file_path)

        # Extracting scooter ID from the data
        scooter_id = df["scooter_id"].iloc[0]

        # Convert the timestamp column to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Storing the dataframe in the dictionary with scooter ID as the key
        scooters_data[scooter_id] = df

    # Create plots
    create_acceleration_speed_analysis(scooters_data, output_dir)
    create_wheel_analysis(scooters_data, output_dir)
    create_battery_performance_analysis(scooters_data, output_dir)
    create_battery_state_smoothed(scooters_data, output_dir)


def create_acceleration_speed_analysis(scooters_data, output_dir):
    plt.figure(figsize=(15, 10))

    colors = ["#FF0000", "#00FF00", "#00FFFF", "#800080", "#FF00FF", "#56B4E9"]

    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]

        plt.scatter(
            df["speed"],
            df["acceleration"],
            alpha=0.1,
            color=color,
            label=f"Scooter {scooter_id}",
        )

    plt.title("Speed vs Acceleration")
    plt.xlabel("Speed")
    plt.ylabel("Acceleration")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "speed_vs_acceleration.png")
    plt.close()


def create_wheel_analysis(scooters_data, output_dir):
    """Create wheel rotation analysis to understand wheel size"""
    plt.figure(figsize=(15, 10))
    colors = ["#FF0000", "#00FF00", "#00FFFF", "#800080", "#FF00FF", "#56B4E9"]
    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]
        plt.scatter(
            df["speed"],
            df["wheel_rotation"],
            alpha=0.1,
            color=color,
            label=f"Scooter {scooter_id}",
        )

    plt.title("Speed vs Wheel Rotation")
    plt.xlabel("Speed")
    plt.ylabel("Wheel Rotation")
    plt.grid(True)
    plt.legend()
    plt.savefig(output_dir / "wheel_rotation_analysis.png")
    plt.close()


def create_battery_state_smoothed(scooters_data, output_dir, window=20):
    """
    Analyzing the smoothed and aggregated battery levels for each state of the scooters
    """
    for scooter_id, df in scooters_data.items():
        # Unique states
        states = df["state"].unique()
        num_states = len(states)

        # Subplots for each state
        fig, axes = plt.subplots(
            num_states, 1, figsize=(15, 5 * num_states), sharex=True
        )

        for i, state in enumerate(states):
            # Filtering dataframe for the current state
            state_df = df[df["state"] == state].copy()

            # Applying rolling average to smooth battery level
            state_df.loc[:, "battery_level_smoothed"] = (
                state_df["battery_level"].rolling(window=window).mean()
            )

            # Aggregating battery level into hourly bins
            state_df_hourly = (
                state_df[["timestamp", "battery_level"]]
                .resample("h", on="timestamp")
                .mean()
            )

            # Plotting smoothed battery level
            axes[i].plot(
                state_df["timestamp"],
                state_df["battery_level_smoothed"],
                label=f"{state} (smoothed)",
            )
            # Plotting hourly average battery level
            axes[i].plot(
                state_df_hourly.index,
                state_df_hourly["battery_level"],
                label=f"{state} (hourly average)",
            )

            axes[i].set_title(f"Battery Level during {state}")
            axes[i].set_ylabel("Battery Level")
            axes[i].grid(True)
            axes[i].legend()

        axes[-1].set_xlabel("Timestamp")
        fig.suptitle(
            f"Scooter {scooter_id}: Battery Level over Time by State (Smoothed and Aggregated)",
            size=16,
        )
        fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.savefig((output_dir / f"battery_state_smoothed_{scooter_id}.png"))
        plt.close(fig)


def create_battery_performance_analysis(scooters_data, output_dir):
    """
    Analyzing how acceleration and braking affect battery level
    """
    plt.figure(figsize=(20, 15))
    colors = ["#FF0000", "#00FF00", "#00FFFF", "#800080", "#FF00FF", "#56B4E9"]

    # Battery Level vs Acceleration
    plt.subplot(2, 2, 1)
    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]
        accelerate_df = df[df["acceleration"] > 0]
        plt.scatter(
            accelerate_df["acceleration"],
            accelerate_df["battery_level"],
            alpha=0.1,
            color=color,
            label=f"Scooter {scooter_id}",
        )

    plt.title("Battery Level vs Acceleration")
    plt.xlabel("Acceleration")
    plt.ylabel("Battery Level (%)")
    plt.legend()

    # Battery Level vs Deceleration (Negative Acceleration)
    plt.subplot(2, 2, 2)
    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]
        # Filter for negative acceleration (braking)
        brake_df = df[df["acceleration"] < 0]
        plt.scatter(
            brake_df["acceleration"],
            brake_df["battery_level"],
            alpha=0.1,
            color=color,
            label=f"Scooter {scooter_id}",
        )

    plt.title("Battery Level vs Braking (Negative Acceleration)")
    plt.xlabel("Deceleration")
    plt.ylabel("Battery Level (%)")
    plt.legend()

    # Speed vs Deceleration Line Plot
    plt.subplot(2, 2, 3)
    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]

        # Grouping by speed ranges and calculating average deceleration
        df["speed_bin"] = pd.cut(df["speed"], bins=10)
        decel_by_speed = (
            df[df["acceleration"] < 0]
            .groupby("speed_bin", observed=False)["acceleration"]
            .mean()
        )
        plt.plot(
            range(len(decel_by_speed)),
            decel_by_speed.values,
            color=color,
            marker="o",
            label=f"Scooter {scooter_id}",
        )

    plt.title("Average Deceleration by Speed Range")
    plt.xlabel("Speed Bin")
    plt.ylabel("Average Deceleration")
    plt.legend()

    # Cumulative Energy Impact
    plt.subplot(2, 2, 4)
    for idx, (scooter_id, df) in enumerate(scooters_data.items()):
        color = colors[idx % len(colors)]
        # Calculate cumulative energy impact
        # Assumed energy consumption is related to absolute acceleration
        df["energy_impact"] = np.abs(df["acceleration"])

        # Group by battery level ranges and calculate mean energy impact
        df["battery_level_bin"] = pd.cut(df["battery_level"], bins=10)
        energy_by_battery = df.groupby("battery_level_bin", observed=False)[
            "energy_impact"
        ].mean()

        plt.plot(
            range(len(energy_by_battery)),
            energy_by_battery.values,
            color=color,
            marker="o",
            label=f"Scooter {scooter_id}",
        )

    plt.title("Average Energy Impact by Battery Level Range")
    plt.xlabel("Battery Level Range")
    plt.ylabel("Average Absolute Acceleration")
    plt.legend()

    plt.tight_layout()
    plt.savefig((output_dir / "battery_performance_analysis.png"), dpi=300)
    plt.close()


def main():
    file_paths = [
        Path() / "data/telemetry_data_001.csv",
        Path() / "data/telemetry_data_002.csv",
        Path() / "data/telemetry_data_003.csv",
    ]

    # Run analysis
    try:
        print("Starting analysis...")
        analyze_scooter_data(file_paths)
        print("\n...Analysis complete! Check the 'analysis_output'.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
