# recommend_recompute.py

import sys
import os
import json
import joblib
import pandas as pd
import numpy as np

# === Add root path for package imports ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.infer_from_inputs import infer_features
from utils.reference_data import (
    DAY_RANGES, NIGHT_RANGES, material_directory,
    RT60_target, RT60_max_dev
)
from utils.format_interpreter import standardize_input

# === Paths ===
MODEL_PATH = "model/ecoform_acoustic_comfort_model.pkl"
GUIDANCE_JSON = "knowledge/compliance_guidance.json"
COMPLIANCE_JSON = "knowledge/compliance_thresholds_extended.json"

# === Load model once ===
model = joblib.load(MODEL_PATH)

# === Load compliance JSON (WHO/ISO fallback) ===
with open(COMPLIANCE_JSON) as f:
    loaded = json.load(f)
    compliance_thresholds = {entry["use"]: entry for entry in loaded}

# === Activity comfort thresholds ===
activity_thresholds = {
    "Sleeping": 0.85, "Working": 0.75, "Learning": 0.80, "Living": 0.70,
    "Healing": 0.80, "Co-working": 0.75, "Exercise": 0.60, "Dining": 0.65
}

# === Helper: LAeq compliance check ===
def check_la_eq_compliance(zone, laeq, period='day'):
    db_range = DAY_RANGES.get(zone) if period.lower() == 'day' else NIGHT_RANGES.get(zone)
    if not db_range or laeq is None:
        return False, db_range
    min_db, max_db = db_range
    return min_db <= laeq <= max_db, db_range

# === Helper: Best material upgrade ===
def recommend_best_material(material_type, current_abs):
    better = [mat for mat in material_directory[material_type] if mat[0] > current_abs]
    if better:
        return sorted(better, reverse=True)[0]
    return None

# === Main full pipeline ===
def recommend_recompute(user_input):
    """
    Compute comfort score using ML model and provide recommendations.
    """
    try:
        # === Clean input keys ===
        user_input = standardize_input(user_input)
        print("🔍 Standardized input for ML:", user_input)

        # Extract required parameters
        zone = user_input.get("zone_string")
        apartment_type = user_input.get("apartment_type_string")
        element_material = user_input.get("element_materials_string")
        wall_material = user_input.get("wall_material")
        window_material = user_input.get("window_material")
        floor_level = user_input.get("floor_level")
        activity = user_input.get("activity", "Living")
        period = user_input.get("time_period", "day")

        if not zone or not apartment_type:
            raise ValueError("Both zone and apartment_type are required")

        print(f"🔍 Running ML inference for: {apartment_type} in {zone}")
        
        # === Run inference for missing features ===
        features, tier = infer_features(
            apartment_type=apartment_type,
            zone=zone,
            element=element_material,
            element_material=wall_material,
            floor_level=floor_level
        )
        print(f"✅ Features inferred using {tier}")
        print("📦 Inferred features:", features)

        # === Model prediction ===
        try:
            # Create DataFrame with all required features
            df = pd.DataFrame([features])
            
            # Ensure exact column names and order as in training
            categorical = [
                'zone_(string)',
                'apartment_type_(string)',
                'day/night(string)',
                'element:_materials_(string)'
            ]
            numeric = [
                'floor_height_(m)',
                'l(a)eq_(db)',
                'total_surface_(sqm)',
                'absorption_coefficient_by_area_(m)',
                'rt60_(s)',
                'n._of_sound_sources_(int)',
                'average_sound_source_distance_(m)',
                'spl_(db)',
                'barrier_distance_(m)',
                'barrier_height_(m)',
                'spl_after_barrier_(db)',
                'spl_after_façade_dampening_(db)'
            ]
            
            # Reorder columns to match training data
            df = df[categorical + numeric]
            
            # Ensure correct dtypes
            for col in categorical:
                df[col] = df[col].astype(str)
            for col in numeric:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            print("📦 DataFrame dtypes before prediction:", df.dtypes)
            print("📦 DataFrame values before prediction:", df.iloc[0].to_dict())
            print("📦 DataFrame before prediction:", df)
            
            # Make prediction
            comfort_score = round(float(model.predict(df)[0]), 3)
            print(f"✅ Predicted comfort score: {comfort_score}")
        except Exception as e:
            print(f"❌ Error in model prediction: {str(e)}")
            print("📦 DataFrame columns:", df.columns.tolist())
            print("📦 DataFrame shape:", df.shape)
            raise

        # === LAeq compliance ===
        laeq_value = features.get("laeq_db") or features.get("l(a)eq_db") or None
        laeq_ok, db_range = check_la_eq_compliance(zone, laeq_value, period)

        # === RT60 compliance ===
        rt60_value = features.get("rt60_s", None)
        rt60_ok = rt60_value is not None and RT60_target <= rt60_value <= RT60_max_dev

        # === Overall ISO compliance fallback ===
        iso_rule = compliance_thresholds.get(activity)
        iso_failures = []
        if iso_rule:
            if laeq_value and laeq_value > iso_rule.get("laeq_max", np.inf):
                iso_failures.append(f"LAeq > {iso_rule['laeq_max']} dB")
            if rt60_value and rt60_value > iso_rule.get("rt60_max", np.inf):
                iso_failures.append(f"RT60 > {iso_rule['rt60_max']} s")

        is_compliant = (laeq_ok and rt60_ok and not iso_failures)

        # === Load guidance JSON for general recommendations ===
        with open(GUIDANCE_JSON) as f:
            guidance = json.load(f)

        recommendations = {}

        if not laeq_ok:
            recommendations["LAeq_zone"] = guidance["LAeq_non_compliant"]["general_recommendations"]

        if not rt60_ok:
            recommendations["RT60"] = guidance["RT60_non_compliant"]["general_recommendations"]

        if iso_failures:
            recommendations["ISO"] = guidance["LAeq_non_compliant"]["general_recommendations"]

        # === Material substitution (absorption driven) ===
        current_wall = wall_material or features.get("wall_material", None)
        wall_abs = None
        for coef, name in material_directory['wall']:
            if name.lower() == (current_wall or "").lower():
                wall_abs = coef
                break

        best_wall = recommend_best_material('wall', wall_abs) if wall_abs else None

        # === Re-run model after material substitution ===
        improved_score = None
        if best_wall:
            try:
                features["wall_material"] = best_wall[1].lower()
                df_new = pd.DataFrame([features])
                improved_score = round(float(model.predict(df_new)[0]), 3)
                recommendations["Wall Upgrade"] = f"Try upgrading to: {best_wall[1]} (abs={best_wall[0]})"
            except Exception as e:
                print(f"❌ Error in improved score prediction: {str(e)}")
                improved_score = None

        # === Build final output ===
        # Ensure compliance and recommendations are always dicts
        compliance_result = {
            "status": "✅ Compliant" if is_compliant else "❌ Not Compliant",
            "reason": f"Zone: {zone}, Period: {period}, Range: {db_range}, ISO Check: {', '.join(iso_failures) if iso_failures else 'OK'}"
        }

        # Ensure recommendations is always a dict
        if not recommendations:
            recommendations = {}
        elif not isinstance(recommendations, dict):
            recommendations = {"general": recommendations}

        result = {
            "comfort_score": comfort_score,
            "source": f"Inference Tier: {tier}",
            "compliance": compliance_result,
            "recommendations": recommendations,
            "best_materials": {
                "wall_material": best_wall[1] if best_wall else current_wall,
            },
            "best_score": improved_score,
            "improved_score": improved_score
        }
        return result

    except Exception as e:
        print(f"❌ Error in recommend_recompute: {str(e)}")
        raise

def run_acoustic_prediction(user_input):
    try:
        return recommend_recompute(user_input)
    except Exception as e:
        print(f"❌ Error in run_acoustic_prediction: {str(e)}")
        raise