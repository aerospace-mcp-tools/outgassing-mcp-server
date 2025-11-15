# Outgassing MCP Server

A Model Context Protocol (MCP) server that provides access to NASA's outgassing database for aerospace material selection. This server enables querying of material outgassing properties (TML, CVCM, WVR) through VS Code's GitHub Copilot Chat.

## Overview

This production-ready MCP server is built with [FastMCP](https://gofastmcp.com) and containerized with Docker. It provides three tools for querying 12,859 aerospace materials from NASA's outgassing database, with intelligent fuzzy search and automatic compliance checking against NASA-STD-6016 standards.

## Features

- **Fuzzy Material Search**: Find materials by name using intelligent matching (rapidfuzz)
- **Application-Based Search**: Filter materials by usage type (ADHESIVE, POTTING, TAPE, etc.)
- **Compliance Checking**: Automatic TML/CVCM validation with WVR adjustment
- **VS Code Integration**: Seamless access through GitHub Copilot Chat
- **Corporate Network Support**: Built-in Zscaler certificate handling
- **Offline Capable**: Falls back to local CSV cache when online source unavailable

## Available Tools

### 1. `search_materials`
Search for materials by name with fuzzy matching and compliance validation.

**Parameters:**
- `material` (string): Material name to search for
- `max_tml` (float, optional): Maximum acceptable TML % (default: 1.0)
- `max_cvcm` (float, optional): Maximum acceptable CVCM % (default: 0.1)

**Returns:** Up to 100 matched materials with outgassing data and compliance flags

**Example usage in Copilot Chat:**
```
@outgassing-mcp-server search for RTV adhesives with TML under 0.5%
```

### 2. `get_applications`
Retrieve all unique application/usage types from the database.

**Parameters:** None

**Returns:** List of all available application categories (45 unique types)

**Example usage in Copilot Chat:**
```
@outgassing-mcp-server what application types are available?
```

### 3. `search_by_application`
Search materials by application type, returning only compliant materials.

**Parameters:**
- `application` (string): Application type (e.g., "ADHESIVE", "POTTING")
- `max_tml` (float, optional): Maximum acceptable TML % (default: 1.0)
- `max_cvcm` (float, optional): Maximum acceptable CVCM % (default: 0.1)

**Returns:** Only materials meeting both TML and CVCM limits for the specified application

**Example usage in Copilot Chat:**
```
@outgassing-mcp-server find compliant adhesives for spacecraft use
```

## Understanding Outgassing Data

- **TML (Total Mass Loss)**: Percentage of material mass lost in vacuum
- **CVCM (Collected Volatile Condensable Material)**: Percentage that condenses on surfaces
- **WVR (Water Vapor Regained)**: Water content that affects TML calculation
- **NASA-STD-6016**: Requires TML ≤ 1.0% and CVCM ≤ 0.1% (after WVR adjustment)
- **Adjusted TML**: TML - WVR (used for compliance when WVR is present)

## Prerequisites

- **Docker**: Ensure Docker is installed and running on your system
- **VS Code**: Latest version with GitHub Copilot extension enabled
- **Network Access**: Internet connectivity for downloading dependencies (corporate networks may require additional certificate setup)

## Installation & Setup

### 1. Certificate Setup (Corporate Networks Only)

If you're behind a corporate firewall using Zscaler or similar proxy:

1. Obtain your organization's root certificate
2. Copy the certificate file to the repository root
3. Rename it to `zscaler-root-ca.cer`

### 2. Build the Docker Image

Navigate to the repository directory and build the Docker image:

```bash
docker build -t outgassing-mcp-server .
```

This command:
- Downloads Python 3.14 base image
- Installs required dependencies using UV package manager
- Configures SSL certificates for corporate networks
- Sets up the FastMCP server environment

### 3. Verify Installation

Test that the server builds and runs correctly:

```bash
docker run -it --name test outgassing-mcp-server
```

You should see the FastMCP startup banner listing 3 tools:

```
                          ╭──────────────────────────────────────────────────────────────────────────────╮
                          │                                                                              │
                          │                         ▄▀▀ ▄▀█ █▀▀ ▀█▀ █▀▄▀█ █▀▀ █▀█                        │
                          │                         █▀  █▀█ ▄▄█  █  █ ▀ █ █▄▄ █▀▀                        │
                          │                                                                              │
                          │                               FastMCP 2.13.0.2                               │
                          │                                                                              │
                          │                                                                              │
                          │                    🖥  Server name: outgassing-mcp-server                    │
                          │                                                                              │
                          │                    📦 Transport:   STDIO                                     │
                          │                                                                              │
                          │                    🔧 Tools:       3                                         │
                          │                                                                              │
                          ╰──────────────────────────────────────────────────────────────────────────────╯
```

Stop the test container:
```bash
docker stop test && docker rm test
```

## VS Code Integration

### Method 1: Using VS Code Command Palette (Recommended)

1. Open VS Code and press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. Type and select **"MCP: Add Server"**
3. Choose **"Command (stdio)"** as the transport type
4. Enter the Docker command:
   ```
   docker run --rm -i --network host outgassing-mcp-server
   ```
5. Name the server: `outgassing-mcp-server`
6. The server will be automatically added to your MCP configuration

### Method 2: Manual Configuration

Alternatively, you can manually edit your MCP configuration file:

**Location**: `%APPDATA%\Code\User\mcp.json` (Windows) or `~/.config/Code/User/mcp.json` (Linux/macOS)

Add the following configuration:

```json
{
  "servers": {
    "outgassing-mcp-server": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network",
        "host",
        "outgassing-mcp-server"
      ]
    }
  }
}
```

### Verification

1. Restart VS Code after configuration
2. Open GitHub Copilot Chat
3. Type `@` and you should see `outgassing-mcp-server` in the available servers list
4. Test with a query like: `@outgassing-mcp-server search for Kapton materials`

## Usage Examples

Once integrated with VS Code, you can query the server through Copilot Chat:

**Find specific materials:**
```
@outgassing-mcp-server search for Kapton polyimide film
@outgassing-mcp-server find RTV silicone adhesives with strict limits
```

**Discover applications:**
```
@outgassing-mcp-server list all application categories
```

**Application-based search:**
```
@outgassing-mcp-server find compliant potting compounds
@outgassing-mcp-server show me aerospace-grade tapes
@outgassing-mcp-server which paints meet NASA standards?
```

**Custom compliance limits:**
```
@outgassing-mcp-server find adhesives with TML under 0.5% and CVCM under 0.05%
```

## Data Source

- **Database**: NASA Outgassing Database (12,859 materials)
- **Online Source**: https://data.nasa.gov/docs/legacy/Outgassing_Db/Outgassing_Db_rows.csv
- **Local Cache**: `Outgassing_Db_rows.csv` (automatic fallback)
- **Standards**: NASA-STD-6016 (Low-Outgassing Materials)
- **Compliance Rate**: ~45.9% of materials meet TML≤1.0% + CVCM≤0.1%

## Configuration Details

### Docker Run Parameters Explained

- `--rm`: Automatically remove container when it exits (prevents container buildup)
- `-i`: Keep STDIN open for interactive communication with MCP protocol
- `--network host`: Use host networking for seamless VS Code stdio communication
- `outgassing-mcp-server`: The Docker image name built in earlier steps

## Development

### Project Structure
```
outgassing-mcp-server/
├── main.py                    # FastMCP server with 3 tools
├── Dockerfile                 # Multi-stage build with cert support
├── pyproject.toml             # Dependencies (fastmcp, pandas, rapidfuzz)
├── Outgassing_Db_rows.csv    # Local data cache (12,859 materials)
├── README.md                  # This file
└── .github/
    └── copilot-instructions.md  # Development guidelines for LLMs
```

### Modifying the Server

To add new tools or modify existing functionality:

1. **Edit** `main.py` to add new `@app.tool()` decorated functions
2. **Rebuild** the Docker image: `docker build -t outgassing-mcp-server .`
3. **Test** the changes: `docker run -it --name test outgassing-mcp-server`
4. **Verify** tool count in FastMCP startup banner
5. **Clean up** test container: `docker stop test && docker rm test`
6. **Restart** VS Code to reload the MCP client connection

### Adding a New Tool Example

```python
@app.tool()
def get_manufacturers(application: str = None) -> str:
    """Get list of manufacturers, optionally filtered by application
    
    Args:
        application: Optional application type to filter by
        
    Returns:
        JSON string with manufacturer list
    """
    df = load_outgassing_data()
    if isinstance(df, str):
        return df
    
    if application:
        df = df[df['Material Usage'].str.contains(application, case=False, na=False)]
    
    manufacturers = df['MFR'].dropna().unique().tolist()
    return json.dumps({
        "application": application,
        "total_manufacturers": len(manufacturers),
        "manufacturers": manufacturers
    })
```

## Troubleshooting

### Container Issues

**Container fails to start:**
- Verify Docker is running: `docker --version`
- Check image exists: `docker images | grep outgassing-mcp-server`
- Review build logs for errors during image creation
- Test manually: `docker run -it --name test outgassing-mcp-server`

**Data loading errors:**
- Check internet connectivity for online CSV access
- Verify `Outgassing_Db_rows.csv` exists in project root for offline fallback
- Review container logs for SSL/certificate errors

### VS Code Integration Issues

**VS Code doesn't detect the server:**
- Confirm `mcp.json` configuration syntax is valid JSON
- Verify file location: `%APPDATA%\Code\User\mcp.json` (Windows)
- Restart VS Code after configuration changes
- Check VS Code Developer Console (`Help > Toggle Developer Tools`) for MCP-related errors
- Ensure Docker Desktop is running before starting VS Code

**Server appears but tools don't work:**
- Rebuild the Docker image to ensure latest code
- Check that FastMCP banner shows 3 tools on startup
- Verify network connectivity for NASA database access
- Test tools manually: `docker run -it --name test outgassing-mcp-server`

### Corporate Network Issues

**SSL certificate errors:**
- Ensure the correct root certificate is placed as `zscaler-root-ca.cer` in project root
- Verify certificate format is PEM/CRT compatible (text file starting with `-----BEGIN CERTIFICATE-----`)
- Contact your IT department for the correct certificate file
- Rebuild Docker image after adding certificate: `docker build -t outgassing-mcp-server .`

**Proxy blocking connections:**
- Some corporate proxies may block Docker container network access
- Try using `--network host` flag (already included in recommended command)
- Consult IT department about Docker networking policies

### Data Quality Issues

**No results found:**
- Use `get_applications` tool first to see available categories
- Try broader search terms (fuzzy matching requires 82/100 similarity)

**Unexpected compliance results:**
- Server accounts for WVR (Water Vapor Regained) in TML calculations
- Adjusted TML = TML - WVR when WVR is present
- Check individual `tml_pass` and `cvcm_pass` flags in results

## Technical Details

### Dependencies
- **Python**: 3.14 (slim-trixie base image)
- **FastMCP**: ≥2.13.0.2 (MCP protocol implementation)
- **pandas**: ≥2.3.3 (data processing)
- **rapidfuzz**: ≥3.14.3 (fuzzy string matching)
- **python-levenshtein**: ≥0.27.3 (string distance calculations)

### Security Considerations
- SSL verification disabled for corporate proxy compatibility
- No authentication required (local VS Code integration)
- No external network access required after data load (uses local cache)
- Container runs with default user (non-root when possible)

## Support & Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **MCP Protocol Specification**: https://modelcontextprotocol.io
- **Docker Documentation**: https://docs.docker.com
- **NASA Outgassing Database**: https://data.nasa.gov/docs/legacy/Outgassing_Db/
- **NASA-STD-6016**: Low-Outgassing Materials Standard

## License

See LICENSE file for details.

## Acknowledgments

- **Data Source**: NASA Outgassing Database
- **Framework**: FastMCP by the FastMCP team
- **Protocol**: Model Context Protocol (MCP) specification
