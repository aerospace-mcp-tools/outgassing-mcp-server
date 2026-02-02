# Outgassing MCP Server - AI Agent Instructions

## Project Overview
A FastMCP server providing NASA outgassing database access (13,582 materials) through Docker stdio transport. Single-file architecture ([main.py](../main.py)) with four tools: fuzzy material search, application filtering, and metadata retrieval.

## Architecture

### Core Components
- **Single entry point**: [main.py](../main.py) contains all server logic (no modules/packages)
- **FastMCP framework**: Uses `@app.tool()` decorator pattern for MCP tool registration
- **Data source**: NASA CSV downloaded at Docker build time to `/app/data/Outgassing_Db_rows.csv`
- **Global state**: `outgassing_data` cached in memory after first load (singleton pattern)

### Data Model (CSV columns)
- `Sample Material`: Primary search field (fuzzy matched)
- `Material Usage`: Application type filter (961 unique values)
- `TML`, `CVCM`, `WVR`: Outgassing percentages
- `ID`, `MFR`: Material identifiers

### Compliance Logic (NASA-STD-6016)
**Critical pattern**: TML compliance uses WVR adjustment when present:
```python
adjusted_tml = (TML - WVR) if WVR exists else TML
compliant = adjusted_tml <= max_tml AND CVCM <= max_cvcm
```
This logic appears in both `query_materials()` and `query_application()` via `calculate_adjusted_tml()`.

## Development Workflow

### Building & Testing
```bash
# Build Docker image
docker build -t outgassing-mcp-server .

# Test server startup
docker run -it --name test outgassing-mcp-server

# Cleanup
docker stop test && docker rm test
```

### Dependencies (uv-managed)
- `fastmcp>=2.13.0.2`: MCP server framework
- `pandas>=2.3.3`: CSV/data manipulation
- `rapidfuzz>=3.14.3`: Fuzzy string matching (fuzz.WRatio scorer)

**Add dependencies**: Edit [pyproject.toml](../pyproject.toml) dependencies array, then rebuild Docker image (no separate install step).

### Debugging
- Server runs in Docker stdio mode (no logs to terminal)
- Test tools via VS Code Copilot Chat: `"Check the outgassing-mcp-server for RTV adhesives"`
- Manual testing: Not easily testable outside MCP client (no HTTP/CLI mode)

## Code Conventions

### FastMCP Tool Pattern
```python
@app.tool()
def tool_name(param: type, optional: type = default) -> str:
    """Docstring becomes MCP tool description"""
    df = load_outgassing_data()  # Always check data loaded
    # ... logic ...
    return json.dumps(result_dict)  # Always JSON string
```

### Search Patterns
1. **Fuzzy search**: `rapidfuzz.process.extract()` with `MATCH_THRESHOLD = 82`, `limit=100`
2. **Application filter**: `str.contains(application, case=False, na=False)` - case-insensitive substring match
3. **Compliance**: Vectorized pandas operations (`df['tml_pass'] = adjusted_tml <= max_tml`)

### Return Format Standard
All query tools return JSON strings with this structure:
```json
{
  "query": "<input>",
  "limits": {"max_tml": float, "max_cvcm": float},
  "results": [array of material dicts]
}
```

## Corporate Network Support
- **Zscaler certificate**: Place `zscaler-root-ca.crt` in repo root before Docker build
- Dockerfile conditionally installs if file exists (see [Dockerfile](../Dockerfile) lines 7-15)
- Environment variables set: `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE`

## Key Constraints
- **No testing framework**: Changes must be validated via Docker rebuild + manual testing
- **No dev mode**: Every change requires full Docker rebuild (no hot reload)
- **Data immutability**: CSV downloaded at build time (stale until rebuild)
- **Python 3.14 required**: Uses features from latest Python (see `.python-version`)

## Common Tasks

### Adding a new tool
1. Define function with `@app.tool()` decorator in [main.py](../main.py)
2. Use type hints (appear in MCP schema)
3. Return JSON string matching standard format
4. Call `load_outgassing_data()` to access CSV
5. Rebuild Docker image to test

### Modifying search logic
- Fuzzy matching: Adjust `MATCH_THRESHOLD` constant (line 8)
- Match algorithm: Change `scorer=` in `process.extract()` calls