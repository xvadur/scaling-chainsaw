import lime
from lime.lime_text import LimeTextExplainer
from transformers import pipeline
import yaml
import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Move `classifier_fn` to the top level of the module for direct import
def classifier_fn(texts):
    """
    Takes a list of input texts, tokenizes them, and returns a 2D numpy array
    with probabilities for each emotion class.
    """
    # Initialize tokenizer and model
    model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    # Tokenize input texts
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
    # Pass through the model
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).numpy()
    return probs

class LIMEAnalyzer:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.explainer = LimeTextExplainer(class_names=["NEGATIVE", "POSITIVE"])

    def explain_prediction(self, text):
        """
        Generate LIME explanations for the given text.

        Args:
            text (str): The input text to analyze.

        Returns:
            dict: LIME explanation results.
        """
        sentiment_pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)

        explanation = self.explainer.explain_instance(
            text,
            classifier_fn=classifier_fn,
            num_features=10
        )
        return explanation

    def explain_and_visualize(self, yaml_input_path, output_image_path):
        """
        Generate LIME explanations and save visualizations for text in a YAML file.

        Args:
            yaml_input_path (str): Path to the input YAML file.
            output_image_path (str): Path to save the visualization image.
        """
        # Load text from YAML file
        with open(yaml_input_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            text = data.get('meta_analysis', {}).get('notes', '')

        if not text:
            print("No text found in the YAML file for analysis.")
            return

        # Generate LIME explanation
        explanation = self.explain_prediction(text)

        # Visualize explanation
        fig = explanation.as_pyplot_figure()
        plt.title("LIME Explanation")
        plt.savefig(output_image_path)
        plt.close()
        print(f"LIME explanation visualization saved to {output_image_path}")

# Add a function to save LIME explanation as an image
def save_lime_explanation(explanation, output_path):
    """
    Save the LIME explanation as a bar chart image.

    Args:
        explanation: LIME explanation object.
        output_path (str): Path to save the image.
    """
    fig = explanation.as_pyplot_figure()
    plt.title("LIME Explanation")
    plt.savefig(output_path)
    plt.close()
    print(f"LIME explanation saved to {output_path}")

# Ensure `classifier_fn` is accessible for import
__all__ = ['classifier_fn']
