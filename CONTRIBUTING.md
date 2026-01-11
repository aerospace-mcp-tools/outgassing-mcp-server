# Contributing to Outgassing MCP Server

Thanks for your interest in contributing! This is a small project maintained by a single developer in their free time, so contributions are welcome but please be patient with response times.

## How to Contribute

1. **Fork the repository** and create a branch for your changes
2. **Make your changes** following the patterns in the existing code
3. **Test thoroughly** test code changes after editing (see manual testing details below)
4. **Submit a pull request** with a clear description of what you've changed and why

## Development Setup

### Prerequisites
- Docker installed and running
- VS Code with MCP support
- (Optional) Corporate certificate if behind a proxy (see SSL Verification below)

### Testing

Manually test changes after editing [main.py](main.py) following this sequence:
```bash
docker build -t outgassing-mcp-server .
docker run -it --name test outgassing-mcp-server  # Verify tool count in banner
docker stop test && docker rm test
# Restart VS Code to reload MCP client
```

## Code Guidelines

- **Use FastMCP patterns**: Follow existing decorator structure for new tools

## What to Contribute

### Welcome Contributions
- Bug fixes
- Performance improvements
- Better fuzzy matching for material names
- Additional search/filter tools
- Documentation improvements
- Test coverage

### Please Discuss First (Open an Issue)
- Major architectural changes
- New dependencies
- Breaking changes to existing tools
- Alternative data sources

## Questions?

Open an issue! Response times may vary, but all questions are welcome.

## License

By contributing, you agree that your contributions will be licensed under the project license.
