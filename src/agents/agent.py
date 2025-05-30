import json
from typing import List, Dict

class MemoryTraversalAgent:
    """
    Agent na introspektívne spracovanie pamäťových záznamov.
    """

    def __init__(self, memory_batch: List[Dict]):
        self.memory_batch = memory_batch

    def analyze_memory(self):
        """
        Analyzuje pamäťové záznamy a generuje introspektívne výstupy.
        """
        results = []
        for entry in self.memory_batch:
            statement = entry.get("statement", "")
            mental_state = entry.get("mental_state", "neutral")
            certainty_level = entry.get("certainty_level", 0.5)
            cognitive_load = entry.get("cognitive_load", 0.5)

            # Diagnostika a návrh meta-tagov
            diagnostic = ""
            tags = []
            if cognitive_load > 0.7:
                diagnostic = "Vysoké kognitívne zaťaženie."
                tags.append("uncertainty_cycle")
            if certainty_level < 0.4:
                diagnostic += " Nízka úroveň istoty."
                tags.append("residual_noise")
            if mental_state == "reflective":
                diagnostic += " Reflexívny mentálny stav."
                tags.append("insight_node")

            # Výstup pre daný záznam
            results.append({
                "highlighted": statement,
                "diagnostic": diagnostic.strip(),
                "asl_tags_proposed": tags,
                "reflection_score": round(cognitive_load * certainty_level, 2)
            })
        return results

# Testovací vstup
if __name__ == "__main__":
    # Ukážkový pamäťový batch
    memory_batch = [
        {
            "statement": "Neviem, čo mám robiť.",
            "mental_state": "reflective",
            "certainty_level": 0.34,
            "cognitive_load": 0.79
        },
        {
            "statement": "Navrhol som novú funkciu pre AetheroOS.",
            "mental_state": "creative",
            "certainty_level": 0.8,
            "cognitive_load": 0.4
        }
    ]

    agent = MemoryTraversalAgent(memory_batch)
    results = agent.analyze_memory()

    # Uloženie výsledkov do JSON
    with open("memory_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Výsledky introspektívnej analýzy boli uložené do memory_analysis.json.")
