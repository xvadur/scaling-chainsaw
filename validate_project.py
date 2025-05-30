import os

# Očakávaná štruktúra
expected_structure = {
    "": ["README.md", "constitution_monumentum_veritas.md", ".gitignore", "CONTRIBUTING.md", "LICENSE"],
    "asl_samples": ["aeth_mem_001.yaml"],
    "docs": ["asl_overview.md"]
}

# Overenie štruktúry
def validate_structure():
    for folder, files in expected_structure.items():
        if folder and not os.path.exists(folder):
            return f"Missing folder: {folder}"
        for file in files:
            file_path = os.path.join(folder, file) if folder else file
            if not os.path.exists(file_path):
                return f"Missing file: {file_path}"
    return "Structure is valid!"

# Spustenie validácie
if __name__ == "__main__":
    result = validate_structure()
    print(result)