# Copilot Instructions for Outgassing MCP Server

## Project Overview
This is a **Model Context Protocol (MCP) server** that provides outgassing material data for aerospace applications. It's built with **FastMCP** and containerized for VS Code GitHub Copilot integration.

**Key Architecture:**
- `main.py`: Currently a data exploration script, should be converted to a FastMCP server
- Docker-based deployment with corporate certificate support (Zscaler)
- Data source: NASA's outgassing database CSV
- Target: Integration with VS Code Copilot Chat as an MCP tool provider

## Critical Development Patterns

### FastMCP Server Structure
The `main.py` file needs FastMCP server implementation. Expected pattern:
```python
from fastmcp import FastMCP
import pandas as pd
import ssl
import urllib.request

app = FastMCP("outgassing-mcp-server")

# Global data cache
outgassing_data = None

def load_outgassing_data():
    """Load data with online/local fallback pattern"""
    global outgassing_data
    if outgassing_data is not None:
        return outgassing_data
    
    # SSL setup for corporate networks
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    url = "https://data.nasa.gov/docs/legacy/Outgassing_Db/Outgassing_Db_rows.csv"
    local_file = "Outgassing_Db_rows.csv"
    
    try:
        outgassing_data = pd.read_csv(url)
    except Exception:
        try:
            outgassing_data = pd.read_csv(local_file)
        except Exception as e:
            return f"Error: Unable to load outgassing data - {str(e)}"
    
    return outgassing_data

@app.tool()
def search_materials(material: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Search for materials by name with outgassing limits"""
    # Fuzzy search implementation with TML/CVCM compliance indicators
    
@app.tool()
def search_by_application(application: str, max_tml: float = 1.0, max_cvcm: float = 0.1) -> str:
    """Search materials by application/usage with outgassing limits"""
    # Application-based filtering with compliance checking

if __name__ == "__main__":
    app.run()
```

### Required Tool Specifications

**Tool 1: `search_materials`**
- Parameters: `material` (string), `max_tml` (float, default 1.0), `max_cvcm` (float, default 0.1)
- Returns: JSON string with materials array containing: name, TML, CVCM, usage, tml_pass, cvcm_pass
- Fuzzy matching on `Sample Material` column
- Boolean compliance indicators for aerospace standards

**Tool 2: `search_by_application`**
- Parameters: `application` (string), `max_tml` (float, default 1.0), `max_cvcm` (float, default 0.1)  
- Returns: JSON string with filtered materials meeting application and outgassing criteria
- Searches `Material Usage` column (categories: ADHESIVE, POTTING, TAPE, PAINT, etc.)
- Pre-filters for compliance before returning results

### Data Architecture Details
- **Database**: 12,859 materials with TML range 0.00-100.00%, CVCM range 0.00-99.99%
- **Aerospace Standards**: ~45.9% of materials meet TML≤1.0% + CVCM≤0.1%
- **Key Columns**: `Sample Material`, `TML`, `CVCM`, `Material Usage`, `ID`, `MFR`
- **Top Applications**: ADHESIVE (1774), POTTING (845), TAPE (550), PAINT (459)

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
- **Processing**: pandas DataFrame with SSL context workarounds
- **Error Handling**: Graceful fallback to cached data, descriptive error messages
- **Data Validation**: Check for required columns and reasonable TML/CVCM ranges

## Development Workflow
1. **Test Data Access**: Run current `main.py` to verify data loading works
2. **Implement FastMCP**: Convert exploration script to server with required tools
3. **Build Docker**: Always rebuild after changes: `docker build -t outgassing-mcp-server .`
4. **Test Tools**: Verify FastMCP startup banner and tool registration
5. **VS Code Integration**: Restart VS Code after server changes to reload MCP client

## Implementation Guidelines

### Fuzzy Search Pattern
Use pandas string operations for material name matching:
```python
# Case-insensitive partial matching
mask = df['Sample Material'].str.contains(material, case=False, na=False)
```

### Compliance Checking Pattern  
Always include pass/fail indicators in results:
```python
result['tml_pass'] = result['TML'] <= max_tml
result['cvcm_pass'] = result['CVCM'] <= max_cvcm
result['aerospace_compliant'] = result['tml_pass'] & result['cvcm_pass']
```

### JSON Response Format
Return structured data as JSON strings:
```python
return json.dumps({
    "query": material,
    "limits": {"max_tml": max_tml, "max_cvcm": max_cvcm},
    "results": materials_list,
    "total_found": len(materials_list)
})
```

## Development Workflow
1. **Test Data Access**: Run current `main.py` to verify data loading works
2. **Implement FastMCP**: Convert exploration script to server with required tools
3. **Build Docker**: Always rebuild after changes: `docker build -t outgassing-mcp-server .`
4. **Test Tools**: Verify FastMCP startup banner and tool registration
5. **VS Code Integration**: Restart VS Code after server changes to reload MCP client

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