import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def plot_emotion_map(yaml_file, output_dir="outputs/visualizations"):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the YAML file
    with open(yaml_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    # Extract emotion map
    emotion_map = data.get("emotion_map", {})
    if not emotion_map:
        print(f"No emotion map found in {yaml_file}")
        return

    # Plot the emotion map
    emotions = list(emotion_map.keys())
    values = list(emotion_map.values())

    plt.figure(figsize=(8, 6))
    plt.bar(emotions, values, color="skyblue")
    plt.title("Emotion Map")
    plt.xlabel("Emotions")
    plt.ylabel("Intensity")
    plt.ylim(0, 1)

    # Save the plot
    base_name = os.path.splitext(os.path.basename(yaml_file))[0]
    output_path = os.path.join(output_dir, f"{base_name}_emotion_map.png")
    plt.savefig(output_path)
    plt.close()

    print(f"Emotion map saved to {output_path}")

def plot_combined_emotion_maps(yaml_dir="outputs/", output_file="outputs/visualizations/combined_emotion_map.png"):
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    combined_emotions = {}

    # Iterate through all YAML files in the directory
    for filename in os.listdir(yaml_dir):
        if filename.endswith(".yaml"):
            yaml_file = os.path.join(yaml_dir, filename)
            with open(yaml_file, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            # Extract emotion map
            emotion_map = data.get("emotion_map", {})
            for emotion, value in emotion_map.items():
                if emotion not in combined_emotions:
                    combined_emotions[emotion] = []
                combined_emotions[emotion].append(value)

    # Prepare data for plotting
    emotions = list(combined_emotions.keys())
    values = [sum(combined_emotions[emotion]) / len(combined_emotions[emotion]) for emotion in emotions]

    # Plot the combined emotion map
    plt.figure(figsize=(10, 8))
    plt.bar(emotions, values, color="lightcoral")
    plt.title("Combined Emotion Map")
    plt.xlabel("Emotions")
    plt.ylabel("Average Intensity")
    plt.ylim(0, 1)

    # Save the plot
    plt.savefig(output_file)
    plt.close()

    print(f"Combined emotion map saved to {output_file}")

def plot_emotion_bar(yaml_path, output_dir="outputs/visualizations"):
    """Plot a bar chart for the emotion spectrum of a single YAML file."""
    plot_emotion_map(yaml_path, output_dir)

def plot_all_emotions(dir_path="outputs", output_dir="outputs/visualizations"):
    """Iterate through all YAML files in a directory and generate bar charts."""
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(dir_path):
        if filename.endswith(".yaml"):
            yaml_path = os.path.join(dir_path, filename)
            plot_emotion_bar(yaml_path, output_dir)

def plot_emotion_heatmap(dir_path="outputs", output_file="outputs/visualizations/emotion_heatmap.png"):
    """Generate a heatmap for aggregated emotions across multiple YAML files."""
    combined_emotions = {}

    # Aggregate emotion data
    for filename in os.listdir(dir_path):
        if filename.endswith(".yaml"):
            yaml_path = os.path.join(dir_path, filename)
            with open(yaml_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            emotion_map = data.get("emotion_map", {})
            for emotion, value in emotion_map.items():
                if emotion not in combined_emotions:
                    combined_emotions[emotion] = []
                combined_emotions[emotion].append(value)

    # Prepare data for heatmap
    emotions = list(combined_emotions.keys())
    files = [f for f in os.listdir(dir_path) if f.endswith(".yaml")]
    heatmap_data = np.zeros((len(emotions), len(files)))

    for col, filename in enumerate(files):
        yaml_path = os.path.join(dir_path, filename)
        with open(yaml_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        emotion_map = data.get("emotion_map", {})
        for row, emotion in enumerate(emotions):
            heatmap_data[row, col] = emotion_map.get(emotion, 0)

    # Plot heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, annot=True, xticklabels=files, yticklabels=emotions, cmap="coolwarm", cbar=True)
    plt.title("Emotion Heatmap")
    plt.xlabel("Files")
    plt.ylabel("Emotions")

    # Save heatmap
    plt.savefig(output_file)
    plt.close()

    print(f"Emotion heatmap saved to {output_file}")

def plot_radar_chart(emotion_map, output_file="outputs/visualizations/radar_chart.png"):
    """
    Generate a radar chart for the emotion map.

    Args:
        emotion_map (dict): A dictionary of emotions and their intensities.
        output_file (str): Path to save the radar chart.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    labels = list(emotion_map.keys())
    values = list(emotion_map.values())

    # Add the first value to close the radar chart
    values += values[:1]
    labels += labels[:1]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color="skyblue", alpha=0.4)
    ax.plot(angles, values, color="blue", linewidth=2)
    ax.set_yticks([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    plt.title("Emotion Radar Chart", size=20, color="blue", y=1.1)
    plt.savefig(output_file)
    plt.close()

    print(f"Radar chart saved to {output_file}")

if __name__ == "__main__":
    yaml_dir = "outputs/"
    for filename in os.listdir(yaml_dir):
        if filename.endswith(".yaml"):
            plot_emotion_map(os.path.join(yaml_dir, filename))
    plot_combined_emotion_maps(yaml_dir)
