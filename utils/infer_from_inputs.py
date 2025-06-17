# utils/infer_from_inputs.py

import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.column_cleaner import fully_standardize_dataframe

DATA_PATH = "sql/Ecoform_Dataset_v1.csv"
df = pd.read_csv(DATA_PATH)
df = fully_standardize_dataframe(df)
print('DEBUG: Standardized DataFrame columns:', df.columns.tolist())

model_features = [
    'zone_string',
    'apartment_type_string',
    'floor_height_m',
    'l(a)eq_db',
    'day_night_string',
    'total_surface_sqm',
    'element_materials_string',
    'absorption_coefficient_by_area_m',
    'rt60_s',
    'n_of_sound_sources_int',
    'average_sound_source_distance_m',
    'spl_db',
    'barrier_distance_m',
    'barrier_height_m',
    'spl_after_barrier_db',
    'spl_after_façade_dampening_db'
]

def infer_features(apartment_type, zone, element=None, element_material=None, floor_level=None):
    """
    Infer missing features based on available input parameters.
    Returns a complete feature vector for model prediction.
    """
    if not apartment_type or not zone:
        raise ValueError("Both apartment_type and zone are required")
    
    # Preserve original case for model compatibility
    apartment_type_original = str(apartment_type)
    zone_original = str(zone)
    apartment_type = apartment_type_original.lower()
    zone = zone_original.lower()
    
    # Match input against DataFrame
    df = pd.read_csv(DATA_PATH)
    df = fully_standardize_dataframe(df)
    print('DEBUG: DataFrame columns:', df.columns.tolist())
    
    # Use original case for model compatibility
    features = {
        'zone_(string)': zone_original,
        'apartment_type_(string)': apartment_type_original,
        'floor_height_(m)': 3.0,  # Default value
        'l(a)eq_(db)': 0.0,
        'day/night(string)': 'day',  # Default to day
        'total_surface_(sqm)': 0.0,
        'element:_materials_(string)': element_material if element_material else 'Unknown',
        'absorption_coefficient_by_area_(m)': 0.0,
        'rt60_(s)': 0.0,
        'n._of_sound_sources_(int)': 0,
        'average_sound_source_distance_(m)': 0.0,
        'spl_(db)': 0.0,
        'barrier_distance_(m)': 0.0,
        'barrier_height_(m)': 0.0,
        'spl_after_barrier_(db)': 0.0,
        'spl_after_façade_dampening_(db)': 0.0
    }

    # Try exact match first
    match = df[
        (df['apartment_type_string'].str.lower() == apartment_type) &
        (df['zone_string'].str.lower() == zone)
    ]

    tier = None
    if not match.empty:
        tier = "Tier 1: Exact apartment + zone match"
    else:
        # Try partial match for apartment type
        match = df[
            (df['apartment_type_string'].str.lower().str.contains(apartment_type)) &
            (df['zone_string'].str.lower().str.contains(zone))
        ]
        if not match.empty:
            tier = "Tier 2: Partial apartment + zone match"
        else:
            # Try apartment type only
            match = df[df['apartment_type_string'].str.lower().str.contains(apartment_type)]
            if not match.empty:
                tier = "Tier 3: Apartment only match"
            else:
                # Fallback to global mean
                match = df.copy()
                tier = "Tier 4: Global mean fallback"

    # Calculate mean values for numeric features
    numeric_features = match.select_dtypes(include=['float64', 'int64']).columns
    for feature in numeric_features:
        if feature in model_features:
            features[feature] = float(match[feature].mean())

    # Handle floor level
    if floor_level is not None:
        features['floor_height_m'] = round(float(floor_level) * 3.0, 2)

    # Ensure all required features are present and have valid values
    for feature in model_features:
        if feature not in features or pd.isna(features[feature]):
            if feature.endswith('_string'):
                features[feature] = 'unknown'
            else:
                features[feature] = 0.0

    return features, tier
