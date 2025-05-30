import gradio as gr
from aslr_analyzer import ASLAnalyzer

def analyze_text_with_visuals(input_text):
    """
    Analyze the input text and generate visualizations.

    Args:
        input_text (str): The text to analyze.

    Returns:
        str: Path to the generated radar chart.
    """
    analyzer = ASLAnalyzer(input_text)
    analysis = analyzer.analyze_text()

    # Generate radar chart
    from plot_emotions import plot_radar_chart
    radar_chart_path = "outputs/visualizations/radar_chart.png"
    plot_radar_chart(analysis["emotion_map"], radar_chart_path)

    return radar_chart_path

iface = gr.Interface(
    fn=analyze_text_with_visuals,
    inputs="text",
    outputs="image",
    title="Aethero Emotion Analyzer",
    description="Analyze text and visualize emotions with radar charts."
)

if __name__ == "__main__":
    iface.launch()
