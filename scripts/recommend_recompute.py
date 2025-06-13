def run_acoustic_prediction(user_input):
    """
    Run acoustic comfort prediction and recommendations based on user input.
    """
    from scripts.recommend_recompute import recommend_recompute
    return recommend_recompute(user_input)
# recommend_recompute.py
import sys
import os
import json
import joblib
import sqlite3
import pandas as pd
from utils.infer_from_inputs import infer_features
from utils.reference_data import (
    DAY_RANGES, NIGHT_RANGES, material_directory,
    LAeq_target, LAeq_min, LAeq_max, RT60_target, RT60_max_dev
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.infer_from_inputs import infer_features


# === Paths ===
MODEL_PATH = "model/ecoform_acoustic_comfort_model.pkl"
GUIDANCE_JSON = "knowledge/compliance_guidance.json"
MATERIAL_DB_PATH = "sql/material-database.db"
COMPLIANCE_JSON = "knowledge/compliance_thresholds_extended.json"

# === Activity Thresholds ===
activity_thresholds = {
    "Sleeping": 0.85, "Working": 0.75, "Learning": 0.80, "Living": 0.70,
    "Healing": 0.80, "Co-working": 0.75, "Exercise": 0.60, "Dining": 0.65
}

def get_la_eq_range(zone, period='day'):
    if period.lower() == 'day':
        return DAY_RANGES.get(zone)
    else:
        return NIGHT_RANGES.get(zone)

def check_la_eq_compliance(zone, laeq, period='day'):
    db_range = get_la_eq_range(zone, period)
    if not db_range or laeq is None:
        return False, db_range
    min_db, max_db = db_range
    return min_db <= laeq <= max_db, db_range

def recommend_best_material(material_type, current_abs):
    # Recommend material with highest absorption better than current
    better = [mat for mat in material_directory[material_type] if mat[0] > current_abs]
    if better:
        # Sort by absorption descending, return the best
        return sorted(better, reverse=True)[0]
    return None

def recommend_recompute(user_input):
    model = joblib.load(MODEL_PATH)
    COMFORT_THRESHOLD = activity_thresholds.get(user_input["activity"], 0.70)
    time_period = user_input.get("Time_Period", "day")
    zone = user_input["Zone"]
    laeq = float(user_input.get("Laeq", 0))
    rt60 = float(user_input.get("rt60_s", 0)) if "rt60_s" in user_input else None

    # Infer features from dataset
    features, tier = infer_features(
        apartment_type=user_input["Apartment_Type"],
        zone=zone,
        element_material=f"{user_input['window_material']} and {user_input['wall_material']}",
        floor_level=user_input.get("Floor_Level")
    )

    # Predict comfort score
    try:
        X = pd.DataFrame([features])
        comfort_score = float(model.predict(X)[0])
    except Exception as e:
        comfort_score = None

    # LAeq compliance (reference_data, not just JSON)
    laeq_value = features.get('laeq_db', laeq)
    laeq_ok, db_range = check_la_eq_compliance(zone, laeq_value, time_period)

    # RT60 compliance
    rt60_value = features.get('rt60_s', rt60)
    rt60_ok = rt60_value is not None and RT60_target <= rt60_value <= RT60_max_dev

    compliance = {
        "status": "✅ Compliant" if laeq_ok and rt60_ok else "❌ Not Compliant",
        "reason": f"Zone: {zone}, Period: {time_period}, Range: {db_range}, RT60 Target: {RT60_target}-{RT60_max_dev}",
        "LAeq": f"{laeq_value} dB ∈ {db_range}",
        "RT60": f"{rt60_value} s (target {RT60_target}-{RT60_max_dev})"
    }

    # Material recommendations (example for 'wall')
    current_wall = user_input.get('wall_material')
    current_wall_abs = None
    for coef, name in material_directory['wall']:
        if name.lower() == current_wall.lower():
            current_wall_abs = coef
            break
    best_material = recommend_best_material('wall', current_wall_abs) if current_wall_abs else None

    result = {
        "comfort_score": round(comfort_score, 3) if comfort_score is not None else None,
        "source": tier,
        "compliance": compliance,
        "recommendations": {},
        "improved_score": None
    }

    # Recommendations for non-compliance
    if not laeq_ok or not rt60_ok:
        with open(GUIDANCE_JSON) as f:
            guidance = json.load(f)
        if not laeq_ok:
            result["recommendations"]["LAeq"] = guidance["LAeq_non_compliant"]["general_recommendations"]
        if not rt60_ok:
            result["recommendations"]["RT60"] = guidance["RT60_non_compliant"]["general_recommendations"]
        if best_material:
            result["recommendations"]["wall"] = f"Try upgrading to: {best_material[1]} (abs={best_material[0]})"

    return result
