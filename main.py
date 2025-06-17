# main.py

import sys
import os

# Ensure local path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.llm_calls import extract_variables, build_answer
from scripts.sql_calls import query_or_recommend
from utils.format_interpreter import standardize_input

# === CONFIG: Choose input mode ===
use_structured_input = True

# === INPUT BLOCK ===
if use_structured_input:
    print("🟢 Using structured input...")
    user_input = {
        "Apartment_Type": "2Bed",
        "Zone": "HD-Urban-V0",
        "Element": "Living",
        "wall_material": "Rammed Earth",
        "window_material": "Single Glazing",
        "Floor_Level": 1,
        "activity": "Sleeping"
    }
    user_question = (
        f"Evaluate acoustic comfort and compliance for a {user_input['Apartment_Type']} apartment "
        f"in {user_input['Zone']} with {user_input['wall_material']} walls and "
        f"{user_input['window_material']} windows on floor {user_input['Floor_Level']}."
    )

else:
    print("🔵 Using free-form question...")
    user_question = (
        "How can I improve acoustic comfort in a 1Bed apartment in HD-Urban-V1 "
        "with single glazing and concrete walls on the 3rd floor?"
    )
    print("🤖 Extracting structured parameters from question...")
    user_input = extract_variables(user_question)

    if not user_input:
        print("❌ Failed to extract parameters from question.")
        sys.exit(1)

    print("✅ Extracted input:", user_input)
    user_input.setdefault("activity", "Living")

# 🔑 ✅ CRITICAL: Standardize all keys before pipeline
user_input = standardize_input(user_input)

# === Acoustic Evaluation ===
print("🔍 Evaluating acoustic comfort...")
try:
    print("📝 Input parameters:", user_input)
    result = query_or_recommend(user_input)
    print("📦 Raw result:", result)
except Exception as e:
    print(f"❌ Acoustic evaluation failed: {e}")
    sys.exit(1)

# === Print Structured Output ===
print("\n==== Acoustic Comfort Evaluation ====")
print(f"Comfort Score: {result.get('comfort_score', 'N/A')}")
compliance = result.get('compliance', {})
print(f"Compliant: {compliance.get('status', 'N/A')}")
print(f"Reason: {compliance.get('reason', 'N/A')}")

# Print detailed compliance metrics
print("\nDetailed Compliance Metrics:")
print("----------------------------")
if compliance.get('metrics'):
    for metric, value in compliance.get('metrics', {}).items():
        print(f"{metric}: {value}")
else:
    print("No detailed metrics available in database match")

# Print thresholds if available
if compliance.get('thresholds'):
    print("\nCompliance Thresholds:")
    print("---------------------")
    for metric, threshold in compliance.get('thresholds', {}).items():
        print(f"{metric}: {threshold}")

recommendations = result.get('recommendations', {})
if recommendations:
    print("Material Recommendations:")
    if isinstance(recommendations, dict):
        for key, recs in recommendations.items():
            if isinstance(recs, list):
                for rec in recs:
                    print(f"- {rec}")
            elif isinstance(recs, str):
                print(f"- {recs}")
            else:
                print(f"- {recs}")
    else:
        print(f"- {recommendations}")
else:
    print("Material Recommendations: None needed")

if result.get('improved_score'):
    print(f"Improved Score (if upgraded): {result['improved_score']}")
print("====================================\n")

# === Generate LLM Summary ===
print("\n🧠 Generating summary...")
try:
    summary = build_answer(user_question, result)
    print("\n" + summary)
except Exception as e:
    print(f"❌ Failed to generate summary: {e}")
