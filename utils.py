import yaml

def save_yaml_output(data, output_path):
    """
    Save data to a YAML file.

    Args:
        data (dict): The data to save.
        output_path (str): The path to the output YAML file.
    """
    with open(output_path, "w", encoding="utf-8") as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
    print(f"[✓] YAML output saved to {output_path}")
