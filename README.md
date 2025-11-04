# Outgassing MCP Server

A Model Context Protocol (MCP) server for querying outgassing properties of materials through approved aerospace sources. This server provides tools to access material outgassing data commonly used in spacecraft and satellite design.

## Overview

This MCP server is built using [FastMCP](https://gofastmcp.com) and containerized with Docker for easy deployment and integration with VS Code's GitHub Copilot Chat.

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

You should see the FastMCP startup banner:

```
                          ╭──────────────────────────────────────────────────────────────────────────────╮
                          │                                                                              │
                          │                         ▄▀▀ ▄▀█ █▀▀ ▀█▀ █▀▄▀█ █▀▀ █▀█                        │
                          │                         █▀  █▀█ ▄▄█  █  █ ▀ █ █▄▄ █▀▀                        │
                          │                                                                              │
                          │                               FastMCP 2.13.0.2                               │
                          │                                                                              │
                          │                                                                              │
                          │                    🖥  Server name: My MCP Server                             │
                          │                                                                              │
                          │                    📦 Transport:   STDIO                                     │
                          │                                                                              │
                          │                    📚 Docs:        https://gofastmcp.com                     │
                          │                    🚀 Hosting:     https://fastmcp.cloud                     │
                          │                                                                              │
                          ╰──────────────────────────────────────────────────────────────────────────────╯

[11/04/25 17:44:37] INFO     Starting MCP server 'My MCP Server' with transport 'stdio'
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
3. The outgassing-mcp-server should appear in the available MCP servers list
4. Test the connection by asking Copilot to use tools from the outgassing server

## Configuration Details

### Docker Run Parameters Explained

- `--rm`: Automatically remove container when it exits (prevents container buildup)
- `-i`: Keep STDIN open for interactive communication
- `--network host`: Use host networking for seamless VS Code communication
- `outgassing-mcp-server`: The image name we built

### Troubleshooting

**Container fails to start:**
- Verify Docker is running: `docker --version`
- Check image exists: `docker images | grep outgassing-mcp-server`
- Review Docker logs: `docker logs <container_id>`

**VS Code doesn't detect the server:**
- Confirm MCP configuration syntax is valid JSON
- Restart VS Code after configuration changes
- Check VS Code Developer Console for MCP-related errors

**Corporate network issues:**
- Ensure the correct root certificate is placed as `zscaler-root-ca.cer`
- Verify certificate format is PEM/CRT compatible
- Contact your IT department for the correct certificate file

## Development

The server is built with FastMCP and Python 3.14. To modify functionality:

1. Edit `main.py` to add new tools or modify existing ones
2. Rebuild the Docker image: `docker build -t outgassing-mcp-server .`
3. Restart the MCP server in VS Code

## Support

- **FastMCP Documentation**: https://gofastmcp.com
- **MCP Protocol Specification**: https://modelcontextprotocol.io
- **Docker Documentation**: https://docs.docker.com