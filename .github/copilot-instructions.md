# Copilot Instructions for Outgassing MCP Server

## What This Is
A **Model Context Protocol (MCP) server** that exposes NASA's 12,859-material outgassing database through VS Code Copilot Chat. Built with FastMCP, containerized with Docker, production-ready.

**Architecture**: Single-file Python server ([main.py](main.py)) → Docker container → stdio transport → VS Code MCP client

## Critical Aerospace Domain Logic

### WVR Adjustment (NASA-STD-6016 Compliance)
**Non-negotiable pattern** in [main.py](main.py#L48-L56):
```python
def calculate_adjusted_tml(df):
    # Aerospace standard: TML compliance requires WVR adjustment
    conditions = [~pd.isna(df['WVR'])]
    choices = [df['TML'] - df['WVR']]  # Subtract water vapor
    default = df['TML']
    return np.select(conditions, choices, default=default)
```
- **Why**: Water vapor (WVR) is recoverable mass loss, doesn't indicate material degradation
- **Standard**: Adjusted TML ≤ 1.0% AND CVCM ≤ 0.1% for spacecraft use
- **Used in**: All compliance checks in `search_materials` and `search_by_application`

### Fuzzy Search Calibration
[main.py](main.py#L78-L81) uses `rapidfuzz.fuzz.WRatio` with 82/100 threshold:
```python
matched_materials = process.extract(material, choices, scorer=fuzz.WRatio, 
                                   processor=utils.default_process, limit=100)
matched_names = [match[0] for match in matched_materials if match[1] > MATCH_THRESHOLD]
```
- **82/100 threshold**: Empirically tuned for aerospace material naming conventions
- **WRatio scorer**: Handles partial matches ("RTV" finds "RTV-560", "Silicone RTV Adhesive")
- **100 result limit**: Prevents response truncation in MCP protocol

## Development Workflow

### The Build-Test-Clean Cycle
**Always** follow this sequence after editing [main.py](main.py):
```bash
docker build -t outgassing-mcp-server .
docker run -it --name test outgassing-mcp-server  # Verify tool count in banner
docker stop test && docker rm test
# Restart VS Code to reload MCP client
```

### Adding Tools
Use FastMCP decorator with JSON return:
```python
@app.tool()
def new_tool(param: str, max_val: float = 1.0) -> str:
    """Brief description - this appears in Copilot's tool picker"""
    df = load_outgassing_data()
    if isinstance(df, str): return df  # Error passthrough
    
    # pandas logic here
    return json.dumps({"results": [...], "total_found": N})
```

## Corporate Network Quirks

### SSL Context Workaround
[main.py](main.py#L11-L19) **must** disable SSL verification:
```python
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Required for corporate proxies
ssl_context.verify_mode = ssl.CERT_NONE
```
- **Why**: Zscaler/corporate proxies break certificate chains
- **Certificate**: Place `zscaler-root-ca.cer` in project root (auto-detected by [Dockerfile](Dockerfile#L6-L13))
- **Never remove this**: Data loading will fail behind corporate firewalls

### UV Package Manager
[Dockerfile](Dockerfile#L19-L20) uses `uv` not `pip`:
```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync  # NOT pip install
```
- **Why**: Faster dependency resolution, lockfile reliability
- **Lockfile**: `uv.lock` must exist; regenerate with `uv lock` if adding dependencies

## Data Loading Pattern
[main.py](main.py#L26-L45) implements online-first with local fallback:
1. Try `https://data.nasa.gov/.../Outgassing_Db_rows.csv` (12,859 rows)
2. Fall back to `Outgassing_Db_rows.csv` in repo root
3. Cache in global `outgassing_data` (loaded once per container lifecycle)

**Error handling**: Returns error string instead of DataFrame if both fail

## Key Files
- [main.py](main.py): Complete MCP server (203 lines, 3 tools)
- [Dockerfile](Dockerfile): Multi-stage build with certificate injection
- [pyproject.toml](pyproject.toml): Dependencies (fastmcp, pandas, rapidfuzz)
- `.gitignore`: Excludes `zscaler-root-ca.cer`, `Outgassing_Db_rows.csv`

## VS Code MCP Config
Located at `%APPDATA%\Code\User\mcp.json`:
```json
{
  "servers": {
    "outgassing-mcp-server": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "--network", "host", "outgassing-mcp-server"]
    }
  }
}
```
- `--network host`: Required for stdio transport
- `--rm`: Auto-cleanup (prevents container accumulation)

## Common Pitfalls
1. **Forgetting WVR adjustment**: Always use `calculate_adjusted_tml()` for compliance
2. **Removing SSL workaround**: Corporate networks require disabled verification
3. **Using pip instead of uv**: Dependencies managed via `pyproject.toml` + `uv.lock`
4. **Not restarting VS Code**: MCP client caches server configuration
5. **Wrong fuzzy threshold**: 82 is calibrated for aerospace naming; lower = noise, higher = misses