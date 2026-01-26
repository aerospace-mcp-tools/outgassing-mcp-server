import os
import pandas as pd
import numpy as np
import json
from fastmcp import FastMCP
from rapidfuzz import fuzz, process, utils

# Set constants
MATCH_THRESHOLD = 82  # Minimum score for fuzzy matching

app = FastMCP("outgassing-mcp-server")

# Global data cache
outgassing_data = None

def load_outgassing_data():
    """Load data."""
    global outgassing_data
    if outgassing_data is not None:
        return outgassing_data
    
    local_file = "data/Outgassing_Db_rows.csv"
    
    try:
        outgassing_data = pd.read_csv(local_file)
        print("Loaded outgassing data from local cache")
    except Exception as e:
        return f"Error: Unable to load outgassing data - {str(e)}"

    return outgassing_data

def calculate_adjusted_tml(df):
    """
    Calculate adjusted TML for compliance: (TML - WVR) if WVR present, else TML.
    Returns a pandas Series.
    """
    conditions = [~pd.isna(df['WVR'])]
    choices = [df['TML'] - df['WVR']]
    default = df['TML']
    return np.select(conditions, choices, default=default)

@app.tool()
def search_materials(material: str, max_tml: float = 1.0, max_cvcm: float = 0.1, 
                    limit: int = 10, compliant_only: bool = True, include_details: bool = True) -> str:
    """Search for materials by name with outgassing limits
    
    Args:
        material: Material name to search for (rapidfuzz matching)
        max_tml: Maximum acceptable TML percentage accounting for WVR if present (default 1.0%)
        max_cvcm: Maximum acceptable CVCM percentage (default 0.1%)
        limit: Maximum number of results to return (default 10)
        compliant_only: Only return materials that pass both TML and CVCM limits (default True)
        include_details: Include id, manufacturer, and wvr fields in results (default True)
        
    Returns:
        JSON string with materials matched in the database, sorted by match score (best first, 100 being exact match).
    """
    df = load_outgassing_data()
    if isinstance(df, str):  # Error message
        return df
    
    # Fuzzy search on Sample Material column
    choices = df['Sample Material'].to_list()
    matched_materials = process.extract(material, choices, scorer=fuzz.WRatio, processor=utils.default_process, limit=100)
    
    # Create mapping of material name to match score
    match_scores = {match[0]: match[1] for match in matched_materials if match[1] > MATCH_THRESHOLD}
    
    results = df[df['Sample Material'].isin(match_scores.keys())].copy()
    
    # Add match score column
    results['match_score'] = results['Sample Material'].map(match_scores)
    
    if len(results) == 0:
        return json.dumps({
            "query": material,
            "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
            "results": [],
            "total_matched": 0,
            "total_compliant": 0,
            "results_returned": 0,
            "message": "No materials found matching the search term"
        })
    
    # Add compliance indicators
    adjusted_tml = calculate_adjusted_tml(results)
    results['adjusted_tml'] = adjusted_tml
    results['tml_pass'] = adjusted_tml <= max_tml
    results['cvcm_pass'] = results['CVCM'] <= max_cvcm
    
    # Sort by match score (descending - higher is better)
    results = results.sort_values('match_score', ascending=False)
    
    # Track statistics before filtering
    total_matched = len(results)
    total_compliant = len(results[results['tml_pass'] & results['cvcm_pass']])
    
    # Filter to compliant materials only if requested
    if compliant_only:
        results = results[results['tml_pass'] & results['cvcm_pass']].copy()
        if len(results) == 0:
            return json.dumps({
                "query": material,
                "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
                "results": [],
                "total_matched": total_matched,
                "total_compliant": 0,
                "results_returned": 0,
                "message": f"Found {total_matched} materials matching '{material}', but none meet compliance limits"
            })
    
    # Apply limit
    results_truncated = len(results) > limit
    results = results.head(limit)
    
    # Convert to list of dictionaries for JSON serialization
    materials_list = []
    for _, row in results.iterrows():
        material_dict = {
            "sample_material": row['Sample Material'],
            "match_score": int(row['match_score']),
            "tml": float(row['TML']),
            "cvcm": float(row['CVCM']),
            "material_usage": row['Material Usage'],
            "tml_pass": bool(row['tml_pass']),
            "cvcm_pass": bool(row['cvcm_pass'])
        }
        
        # Add detailed fields if requested
        if include_details:
            material_dict["id"] = row['ID']
            material_dict["manufacturer"] = row['MFR']
            material_dict["wvr"] = float(row['WVR']) if not pd.isna(row['WVR']) else None
        
        materials_list.append(material_dict)
    
    return json.dumps({
        "query": material,
        "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
        "results": materials_list,
        "total_matched": total_matched,
        "total_compliant": total_compliant,
        "results_returned": len(materials_list),
        "results_truncated": results_truncated,
        "compliant_only": compliant_only,
        "message": f"Found {total_matched} materials matching '{material}' ({total_compliant} compliant)"
    })
    
@app.tool()
def get_applications() -> str:
    """Get a list of unique material application/usage types from the outgassing database.
    
    Returns:
        JSON string with list of unique material application/usage types
    """
    df = load_outgassing_data()
    if isinstance(df, str):  # Error message
        return df
    
    unique_apps = df['Material Usage'].dropna().unique().tolist()
    return json.dumps({
        "total_applications": len(unique_apps),
        "applications": unique_apps
    })

@app.tool()
def search_by_application(application: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Search materials by application/usage with outgassing limits.
    
    Integration pattern: Call get_applications() to retrieve available application/usage types before invoking this function.
    
    Args:
        application: Application/usage type to search for (e.g., ADHESIVE, POTTING, TAPE)
        max_tml: Maximum acceptable TML percentage (default 1.0%)
        max_cvcm: Maximum acceptable CVCM percentage (default 0.1%)
        
    Returns:
        JSON string with materials meeting application and outgassing criteria
    """
    df = load_outgassing_data()
    if isinstance(df, str):  # Error message
        return df
    
    # Filter by application (case-insensitive)
    app_mask = df['Material Usage'].str.contains(application, case=False, na=False)
    results = df[app_mask].copy()
    
    if len(results) == 0:
        # Get available applications for user reference
        available_apps = df['Material Usage'].value_counts().head(10).index.tolist()
        return json.dumps({
            "query": application,
            "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
            "results": [],
            "total_found": 0,
            "message": f"No materials found for application '{application}'",
            "available_applications": available_apps
        })
    
    # Add compliance indicators
    adjusted_tml = calculate_adjusted_tml(results)
    results['tml_pass'] = adjusted_tml <= max_tml
    # Vectorized approach for CVCM     
    results['cvcm_pass'] = results['CVCM'] <= max_cvcm
    
    # Filter to only compliant materials for better results
    compliant_results = results[results['tml_pass'] & results['cvcm_pass']].copy()

    # Convert to list of dictionaries for JSON serialization
    materials_list = []
    for _, row in compliant_results.iterrows():
        materials_list.append({
            "sample_material": row['Sample Material'],
            "id": row['ID'],
            "manufacturer": row['MFR'],
            "tml": float(row['TML']),
            "cvcm": float(row['CVCM']),
            "wvr": float(row['WVR']) if not pd.isna(row['WVR']) else None,
            "material_usage": row['Material Usage'],
            "tml_pass": bool(row['tml_pass']),
            "cvcm_pass": bool(row['cvcm_pass'])
        })
    
    return json.dumps({
        "query": application,
        "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
        "results": materials_list,
        "total_found": len(results),
        "showing_only_compliant": True
    })

if __name__ == "__main__":
    app.run()