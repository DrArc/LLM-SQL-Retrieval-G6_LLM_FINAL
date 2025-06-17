# sql_calls.py

import sqlite3
import pandas as pd
import os
import sys

# ✅ Allow relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.format_interpreter import standardize_input
from scripts.recommend_recompute import recommend_recompute

# === Path to SQLite DB ===
DB_PATH = "sql/comfort-database.db"

# === Main SQL Call Function ===
def query_or_recommend(user_input):
    """
    Try to retrieve comfort score from SQL based on zone/apartment.
    If not found, fallback to ML + recommendation pipeline.
    """

    # ✅ Standardize input keys first
    user_input = standardize_input(user_input)
    print("🔍 Standardized input:", user_input)

    abs_db_path = os.path.abspath(DB_PATH)
    print(f"🔍 Using database file: {abs_db_path}")
    conn = sqlite3.connect(abs_db_path)

    # Build WHERE clause — only use what SQL can easily match
    conditions = []
    params = []

    # Handle apartment type with more flexibility
    if "apartment_type_string" in user_input:
        apt_type = user_input["apartment_type_string"].lower()
        # Try exact match first
        conditions.append("(LOWER(apartment_type_string) = ? OR LOWER(apartment_type_string) LIKE ?)")
        params.extend([apt_type, f"%{apt_type}%"])
        print(f"🔍 Added apartment type condition: {apt_type}")

    if "zone_string" in user_input:
        zone = user_input["zone_string"].lower()
        # Try exact match first, then partial match
        conditions.append("(LOWER(zone_string) = ? OR LOWER(zone_string) LIKE ?)")
        params.extend([zone, f"%{zone}%"])
        print(f"🔍 Added zone condition: {zone}")

    # If no minimal keys available, skip SQL entirely
    if not conditions:
        print("⚠️ Not enough keys to query SQL — switching to model...")
        return recommend_recompute(user_input)

    sql_query = f"""
    SELECT 
        comfort_index_float,
        apartment_type_string,
        zone_string,
        "l(a)eq_db" as laeq_db,
        "rt60_s" as rt60_s,
        "spl_db" as spl_db,
        "absorption_coefficient_by_aream" as absorption_coefficient,
        "total_surface_sqm" as surface_area
    FROM comfort_lookup
    WHERE {' AND '.join(conditions)}
    ORDER BY comfort_index_float DESC
    LIMIT 1;
    """
    print("📝 SQL Query:", sql_query)
    print("📝 SQL Parameters:", params)

    try:
        result = pd.read_sql_query(sql_query, conn, params=params)
        print("📦 SQL Result DataFrame:")
        print(result)
        print("\n📦 First row of data:")
        print(result.iloc[0])
        print("\n📦 DataFrame columns:")
        print(result.columns.tolist())
        
        if not result.empty:
            print("✅ Match found in SQL database.")
            
            # Get compliance thresholds for the activity
            activity = user_input.get('activity', 'Living')
            
            # Extract metrics from the first row
            metrics = {
                "LAeq (dB)": float(result.iloc[0]['laeq_db']),
                "RT60 (s)": float(result.iloc[0]['rt60_s']),
                "SPL (dB)": float(result.iloc[0]['spl_db']),
                "Absorption Coefficient": float(result.iloc[0]['absorption_coefficient']),
                "Surface Area (m²)": float(result.iloc[0]['surface_area'])
            }
            
            compliance_info = {
                "status": "compliant",
                "reason": "Matched from database",
                "metrics": metrics,
                "thresholds": {
                    "LAeq (dB)": 35 if activity == "Sleeping" else 40,
                    "RT60 (s)": 0.5 if activity == "Sleeping" else 0.6
                }
            }
            
            return {
                "comfort_score": round(result.iloc[0]["comfort_index_float"], 3),
                "source": "SQL Match",
                "compliance": compliance_info,
                "recommendations": {},
                "improved_score": None
            }
        else:
            print("⚠️ No match found in SQL database")
            print("🔄 Switching to model + compliance + recommendation...")
            return recommend_recompute(user_input)
    except Exception as e:
        print("⚠️ SQL lookup failed:", str(e))
        print("🔄 Switching to model + compliance + recommendation...")
        return recommend_recompute(user_input)
    finally:
        conn.close()
