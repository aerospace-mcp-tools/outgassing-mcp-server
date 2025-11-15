import ssl
import urllib.request
import pandas as pd
import numpy as np
import json
from fastmcp import FastMCP
from rapidfuzz import fuzz, process, utils

# Set constants
MATCH_THRESHOLD = 90  # Minimum score for fuzzy matching

# Create SSL context that will work with corporate certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Install custom HTTPS handler
https_handler = urllib.request.HTTPSHandler(context=ssl_context)
opener = urllib.request.build_opener(https_handler)
urllib.request.install_opener(opener)

app = FastMCP("outgassing-mcp-server")

# Global data cache
outgassing_data = None

def load_outgassing_data():
    """Load data with online/local fallback pattern"""
    global outgassing_data
    if outgassing_data is not None:
        return outgassing_data
    
    url = "https://data.nasa.gov/docs/legacy/Outgassing_Db/Outgassing_Db_rows.csv"
    local_file = "Outgassing_Db_rows.csv"
    
    try:
        outgassing_data = pd.read_csv(url)
        print("Loaded outgassing data from online source")
    except Exception as e:
        try:
            outgassing_data = pd.read_csv(local_file)
            print("Loaded outgassing data from local cache")
        except Exception as local_e:
            return f"Error: Unable to load outgassing data - Online: {str(e)}, Local: {str(local_e)}"
    
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
def search_materials(material: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Search for materials by name with outgassing limits
    
    Args:
        material: Material name to search for (rapidfuzz matching)
        max_tml: Maximum acceptable TML percentage accounting for WVR if present (default 1.0%)
        max_cvcm: Maximum acceptable CVCM percentage (default 0.1%)
        
    matched_names = [match[0] for match in matched_materials if match[1] > MATCH_THRESHOLD]
        JSON string with materials matched in the database in order of match quality, outgassing values and TML and CVCM compliance. Maximum 100 results.
    """
    df = load_outgassing_data()
    if isinstance(df, str):  # Error message
        return df
    
    # Fuzzy search on Sample Material column
    choices = df['Sample Material'].to_list()
    matched_materials = process.extract(material, choices, scorer=fuzz.WRatio, processor=utils.default_process, limit=100)
    matched_names = [match[0] for match in matched_materials if match[1] > MATCH_THRESHOLD]  # Threshold for match quality
    
    results = df[df['Sample Material'].isin(matched_names)].copy()
    
    if len(results) == 0:
        return json.dumps({
            "query": material,
            "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
            "results": [],
            "total_found": 0,
            "message": "No materials found matching the search term"
        })
    
    # Add compliance indicators
    adjusted_tml = calculate_adjusted_tml(results)
    results['tml_pass'] = adjusted_tml <= max_tml
    # Vectorized approach for CVCM     
    results['cvcm_pass'] = results['CVCM'] <= max_cvcm
    
    # Convert to list of dictionaries for JSON serialization
    materials_list = []
    for _, row in results.iterrows():
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
        "query": material,
        "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
        "results": materials_list,
        "total_found": len(materials_list),
        "message": f"Found {len(materials_list)} materials matching the search term"
    })

@app.tool()
def search_by_application(application: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Search materials by application/usage with outgassing limits. Check database properties prior to calling this function. 
    
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