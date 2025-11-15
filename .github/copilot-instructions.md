# Copilot Instructions for Outgassing MCP Server

## Project Overview
This is a **Model Context Protocol (MCP) server** that provides outgassing material data for aerospace applications. It's built with **FastMCP** and containerized for VS Code GitHub Copilot integration.

**Key Architecture:**
- `main.py`: Fully implemented FastMCP server with three tools for querying outgassing data
- Docker-based deployment with corporate certificate support (Zscaler)
- Data source: NASA's outgassing database CSV (12,859 materials)
- Status: Production-ready MCP server integrated with VS Code Copilot Chat

## Implemented Tools

### Tool 1: `search_materials`
**Purpose**: Fuzzy search for materials by name with aerospace compliance checking

**Implementation Details:**
- Uses `rapidfuzz` library with WRatio scoring for intelligent matching
- Match threshold: 82/100 minimum score
- Parameters: `material` (string), `max_tml` (float, default 1.0), `max_cvcm` (float, default 0.1)
- Returns: JSON with up to 100 matched materials, sorted by match quality
- Includes: material name, ID, manufacturer, TML, CVCM, WVR, usage, compliance flags
- **WVR Handling**: Adjusted TML calculated as (TML - WVR) when WVR is present for accurate compliance

**Response Structure:**
```json
{
  "query": "search_term",
  "limits": {"max_tml": 1.0, "max_cvcm": 0.1},
  "results": [
    {
      "sample_material": "Material Name",
      "id": "ABC123",
      "manufacturer": "Manufacturer",
      "tml": 0.5,
      "cvcm": 0.05,
      "wvr": 0.1,
      "material_usage": "ADHESIVE",
      "tml_pass": true,
      "cvcm_pass": true
    }
  ],
  "total_found": 1,
  "message": "Status message"
}
```

### Tool 2: `get_applications`
**Purpose**: Retrieve all unique application/usage types from the database

**Implementation Details:**
- Returns list of all unique values in `Material Usage` column
- No parameters required
- Used to discover available application categories before searching

**Response Structure:**
```json
{
  "total_applications": 45,
  "applications": ["ADHESIVE", "POTTING", "TAPE", "PAINT", ...]
}
```

### Tool 3: `search_by_application`
**Purpose**: Search materials by application type with automatic compliance filtering

**Implementation Details:**
- Parameters: `application` (string), `max_tml` (float, default 1.0), `max_cvcm` (float, default 0.1)
- Case-insensitive substring matching on `Material Usage` column
- **Automatic filtering**: Returns ONLY materials meeting both TML and CVCM limits
- **WVR Handling**: Uses adjusted TML (TML - WVR) for compliance checks
- Provides top 10 available applications if search returns no results

**Response Structure:**
```json
{
  "query": "ADHESIVE",
  "limits": {"max_tml": 1.0, "max_cvcm": 0.1},
  "results": [...],  // Only compliant materials
  "total_found": 150,  // Total materials in category
  "showing_only_compliant": true
}
```

## Critical Implementation Patterns

### WVR (Water Vapor Regained) Handling
**Implemented in lines 48-55 of main.py:**
```python
def calculate_adjusted_tml(df):
    """
    Calculate adjusted TML for compliance: (TML - WVR) if WVR present, else TML.
    Returns a pandas Series.
    """
    conditions = [~pd.isna(df['WVR'])]
    choices = [df['TML'] - df['WVR']]
    default = df['TML']
    return np.select(conditions, choices, default=default)
```

**Aerospace Standard**: NASA-STD-6016 requires TML ≤ 1.0% and CVCM ≤ 0.1% after accounting for water content
- If WVR is present: Adjusted TML = TML - WVR
- If WVR is absent: Adjusted TML = TML
- This ensures accurate compliance determination

### Fuzzy Search Implementation
**Uses rapidfuzz library (lines 78-81):**
```python
from rapidfuzz import fuzz, process, utils

matched_materials = process.extract(material, choices, scorer=fuzz.WRatio, 
                                   processor=utils.default_process, limit=100)
matched_names = [match[0] for match in matched_materials if match[1] > MATCH_THRESHOLD]
```
- **Scorer**: WRatio (weighted ratio) for best general-purpose matching
- **Threshold**: 82/100 to balance precision and recall
- **Processor**: Default normalization (lowercasing, whitespace handling)
- **Limit**: Maximum 100 results returned

### Data Loading Pattern
**Online-first with local fallback (lines 26-44):**
```python
def load_outgassing_data():
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
```
- **Caching**: Data loaded once and stored in global variable
- **Fallback**: Tries online source first, then local CSV
- **Error handling**: Returns descriptive error messages with both failure reasons

### Corporate Network Handling
**Critical**: SSL context setup is required for corporate environments:
- Always disable SSL verification for internal corporate proxies
- The pattern in current `main.py` (lines 6-12) must be preserved
- Certificate handling via `zscaler-root-ca.cer` is implemented in Dockerfile

### Docker Integration Workflow
**Build & Test Pattern:**
```bash
# Required build command
docker build -t outgassing-mcp-server .

# Required test pattern  
docker run -it --name test outgassing-mcp-server
docker stop test && docker rm test
```

**VS Code MCP Configuration:**
- Transport: `stdio` 
- Command: `docker run --rm -i --network host outgassing-mcp-server`
- Server name: `outgassing-mcp-server`

## Data Architecture
- **Source**: `https://data.nasa.gov/docs/legacy/Outgassing_Db/Outgassing_Db_rows.csv`
- **Local Cache**: `Outgassing_Db_rows.csv` (fallback when online unavailable)
- **Database Size**: 12,859 materials with TML range 0.00-100.00%, CVCM range 0.00-99.99%
- **Aerospace Standards**: ~45.9% of materials meet TML≤1.0% + CVCM≤0.1%
- **Key Columns**: `Sample Material`, `TML`, `CVCM`, `WVR`, `Material Usage`, `ID`, `MFR`
- **Top Applications**: ADHESIVE (1774), POTTING (845), TAPE (550), PAINT (459)
- **Processing**: pandas DataFrame with SSL context workarounds
- **Error Handling**: Graceful fallback to cached data, descriptive error messages

## Development Workflow
1. **Modify Tools**: Edit `main.py` to add new tools or modify existing ones
2. **Rebuild Docker**: Always rebuild after changes: `docker build -t outgassing-mcp-server .`
3. **Test Container**: Run test container to verify: `docker run -it --name test outgassing-mcp-server`
4. **Verify Tools**: Check FastMCP startup banner shows correct tool count
5. **Clean Up Test**: Stop and remove test container: `docker stop test && docker rm test`
6. **VS Code Integration**: Restart VS Code after server changes to reload MCP client

## Implementation Guidelines

### Adding New Tools
Follow the FastMCP decorator pattern:
```python
@app.tool()
def tool_name(param1: type, param2: type = default) -> str:
    """Tool description for LLM context
    
    Args:
        param1: Description of parameter
        param2: Description with default value
        
    Returns:
        JSON string with structured response
    """
    df = load_outgassing_data()
    if isinstance(df, str):  # Error message
        return df
    
    # Implementation logic
    return json.dumps(response_dict)
```

### Response Format Pattern
Always return JSON strings with consistent structure:
```python
return json.dumps({
    "query": user_input,
    "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
    "results": materials_list,
    "total_found": len(materials_list),
    "message": "Human-readable status message"
})
```

## Container Architecture Notes
- Base: `python:3.14-slim-trixie`
- Package manager: `uv` (not pip)
- Certificate chain: Auto-handles corporate certs if `zscaler-root-ca.cer` exists
- Network: `--network host` required for VS Code stdio communication
- Data loading: Online-first with local CSV fallback for reliability

## File Responsibilities
- `main.py`: MCP server entry point with FastMCP app and tools
- `Dockerfile`: Multi-stage build with certificate handling
- `pyproject.toml`: Dependencies (fastmcp>=2.13.0.2, pandas>=2.3.3)
- `zscaler-root-ca.cer`: Optional corporate certificate (gitignored)

## Key Integration Points
**MCP Protocol**: Server provides tools to VS Code Copilot Chat for querying aerospace material outgassing properties
**Data Flow**: NASA CSV → pandas → FastMCP tools → VS Code Copilot responses
**Deployment**: Docker container → stdio transport → VS Code MCP client