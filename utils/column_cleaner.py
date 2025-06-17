# utils/column_cleaner.py

import pandas as pd

def clean_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s:]", "_", regex=True)
        .str.replace(r"[\(\)]", "", regex=True)
        .str.replace(r"__+", "_", regex=True)
        .str.replace(r"_(string)$", "string", regex=True)
        .str.replace(r"_(db)$", "db", regex=True)
        .str.replace(r"_(s)$", "s", regex=True)
        .str.replace(r"_(int)$", "int", regex=True)
        .str.replace(r"_(sqm)$", "sqm", regex=True)
        .str.replace(r"_(m)$", "m", regex=True)
    )
    return df

def rename_columns(df):
    rename_map = {
        'zone': 'zone_string',
        'apartment_type': 'apartment_type_string',
        'floor_heightm': 'floor_height_m',
        'laeq_db': 'l(a)eq_db',
        'daynightstring': 'day_night_string',
        'total_surface_sqm': 'total_surface_sqm',
        'element_materials_string': 'element_materials_string',
        'absorption_coefficient_by_aream': 'absorption_coefficient_by_area_m',
        'rt60_s': 'rt60_s',
        'nof_sound_sources_int': 'n_of_sound_sources_int',
        'average_sound_source_distancem': 'average_sound_source_distance_m',
        'spl_db': 'spl_db',
        'barrier_distancem': 'barrier_distance_m',
        'barrier_heightm': 'barrier_height_m',
        'spl_after_barrier_db': 'spl_after_barrier_db',
        'spl_after_façade_dampening_db': 'spl_after_façade_dampening_db',
        'comfort_index_float': 'comfort_index_float'
    }
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing)
    return df

def fully_standardize_dataframe(df):
    df = clean_columns(df)
    # Explicit mapping to expected names
    rename_map = {
        'zonestring': 'zone_string',
        'apartment_typestring': 'apartment_type_string',
        'floor_height_m': 'floor_height_m',
        'laeqdb': 'l(a)eq_db',
        'day/nightstring': 'day_night_string',
        'total_surfacesqm': 'total_surface_sqm',
        'element_materialsstring': 'element_materials_string',
        'absorption_coefficient_by_area_m': 'absorption_coefficient_by_area_m',
        'rt60s': 'rt60_s',
        'n._of_sound_sourcesint': 'n_of_sound_sources_int',
        'average_sound_source_distance_m': 'average_sound_source_distance_m',
        'spldb': 'spl_db',
        'barrier_distance_m': 'barrier_distance_m',
        'barrier_height_m': 'barrier_height_m',
        'spl_after_barrierdb': 'spl_after_barrier_db',
        'spl_after_façade_dampeningdb': 'spl_after_façade_dampening_db',
        'comfort_index_float': 'comfort_index_float'
    }
    df = df.rename(columns=rename_map)
    return df
