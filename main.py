# Import Python libraries
import os
import json

# Import third-party libraries
import pandas as pd
import numpy as np
from fastmcp import FastMCP
from rapidfuzz import fuzz, process, utils

app = FastMCP("outgassing-mcp-server")

# Set up global data cache
outgassing_data = None

def load_outgassing_data():
    """Load outgassing data from local CSV file to global cache
    """
    # Access global data cache
    global outgassing_data
    
    # Return cached data if already loaded
    if outgassing_data is not None:
        return
    # Load data from CSV file
    else:
        outgassing_data = pd.read_csv("data/Outgassing_Db_rows.csv")
    
        # Calculate adjusted TML
        calculate_adjusted_tml()
        return 

def calculate_adjusted_tml():
    """
    Calculate adjusted TML for compliance: (TML - WVR) if WVR present, else TML.
    """
    global outgassing_data
    
    # Vectorized calculation of adjusted TML
    conditions = [~pd.isna(outgassing_data['WVR'])]
    choices = [outgassing_data['TML'] - outgassing_data['WVR']]
    default = outgassing_data['TML']
    
    # Add adjusted_tml column
    outgassing_data['adjusted_tml'] = np.select(conditions, choices, default=default)
    return

@app.tool()
def query_materials(material: str, max_tml: float = 1.0, max_cvcm: float = 0.1, 
                    limit: int = 10) -> str:
    """Query materials from NASA outgassing database matching a material name and whether they meet TML and CVCM limits.
    
    Args:
        material: Material name to search
        max_tml: Maximum acceptable TML percentage accounting for WVR if present (default 1.0%)
        max_cvcm: Maximum acceptable CVCM percentage (default 0.1%)
        limit: Maximum number of results to return (default 10)        
    Returns:
        JSON string with materials matched in the database, sorted by match score (best first, 100 being exact match, less than 82 being a low quality match).
    """
    # Load outgassing data
    load_outgassing_data()
    
    # Fuzzy search on Sample Material column - get all materials with scores
    all_materials = outgassing_data['Sample Material'].to_list()
    matched_materials = process.extract(material, all_materials, scorer=fuzz.WRatio, processor=utils.default_process, limit=limit)
    
    # Create results dataframe with only matched materials
    matched_names = [match[0] for match in matched_materials]
    results = outgassing_data[outgassing_data['Sample Material'].isin(matched_names)].copy()
    
    # Add match scores to results
    score_map = {match[0]: match[1] for match in matched_materials}
    results['match_score'] = results['Sample Material'].map(score_map)
    
    # Create TML and CVCM pass/fail columns
    results['tml_pass'] = results['adjusted_tml'] <= max_tml
    results['cvcm_pass'] = results['CVCM'] <= max_cvcm
    
    # Sort results by match score descending (best matches first)
    results = results.sort_values(by='match_score', ascending=False)

    # Convert to list of dictionaries for JSON serialization
    materials_list = []
    for _, row in results.iterrows():
        materials_list.append({
            "sample_material": row['Sample Material'],
            "id": row['ID'],
            "match_score": int(row['match_score']),
            "tml_pass": bool(row['tml_pass']),
            "cvcm_pass": bool(row['cvcm_pass'])
        })
        
    # Return JSON
    return json.dumps({
            "query": material,
            "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
            "results": materials_list
        })
    
@app.tool()
def get_material(material_id: str) -> str:
    """Get material details by unique ID from the outgassing database.
    
    Integration pattern: Call query_materials() or query_application() to find material IDs before invoking this function.
    
    Args:
        material_id: Unique material ID in the outgassing database
    Returns:
        JSON string with material details or error message if ID not found
    """
    load_outgassing_data()
    
    material_row = outgassing_data[outgassing_data['ID'] == material_id]
    if material_row.empty:
        return json.dumps({
            "error": f"Material with ID '{material_id}' not found in the database."
        })
        
    # Convert the material row to a dictionary and then to JSON
    material_dict = material_row.iloc[0].to_dict()
    return json.dumps(material_dict)
    
@app.tool()
def get_applications() -> str:
    """Get a list of unique material application/usage types from the outgassing database.
    
    Returns:
        JSON string with list of unique material application/usage types
    """
    load_outgassing_data()
    
    unique_apps = outgassing_data['Material Usage'].dropna().unique().tolist()
    return json.dumps({
        "total_applications": len(unique_apps),
        "applications": unique_apps
    })

@app.tool()
def query_application(application: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Query materials by application/usage meeting specified TML and CVCM limits.
    
    Integration pattern: Call get_applications() to retrieve available application/usage types before invoking this function.
    
    Args:
        application: Application/usage type to search for (e.g., ADHESIVE, POTTING, TAPE)
        max_tml: Maximum acceptable TML percentage (default 1.0%)
        max_cvcm: Maximum acceptable CVCM percentage (default 0.1%)
        
    Returns:
        JSON string with materials meeting application and outgassing criteria sorted by adjusted TML with lowest values first.
    """
    load_outgassing_data()
    
    # Create results dataframe with only materials matching the application
    results = outgassing_data[outgassing_data['Material Usage'].str.contains(application, case=False, na=False)].copy()
    
    # Create TML and CVCM pass/fail columns
    results['tml_pass'] = results['adjusted_tml'] <= max_tml
    results['cvcm_pass'] = results['CVCM'] <= max_cvcm
    
    # Remove materials that do not meet criteria
    results = results[(results['tml_pass']) & (results['cvcm_pass'])].copy()
    
    # Sort results by adjusted TML ascending 
    results = results.sort_values(by='adjusted_tml', ascending=True)
    
    if results.empty:
        return json.dumps({
            "error": f"No materials found for application '{application}' meeting the specified criteria."
        })
    
    # Convert to list of dictionaries for JSON serialization
    materials_list = []
    for _, row in results.iterrows():
        materials_list.append({
            "sample_material": row['Sample Material'],
            "id": row['ID'],
            "tml_pass": bool(row['tml_pass']),
            "cvcm_pass": bool(row['cvcm_pass'])
        })
        
    # Return JSON
    return json.dumps({
            "query": application,
            "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
            "results": materials_list
        })

if __name__ == "__main__":
    app.run()