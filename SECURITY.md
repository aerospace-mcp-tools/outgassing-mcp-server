# Security Policy

## Supported Versions

As a small, single-developer project, only the latest release on the `main` branch is actively supported.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| older   | :x:                |

## Reporting a Vulnerability

**For security issues, please do NOT open a public GitHub issue.**

Instead:
1. Open a [Security Advisory](https://github.com/aerospace-mcp-tools/outgassing-mcp-server/security/advisories/new) on GitHub, or
2. Contact the maintainer through GitHub's private messaging

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

**Response timeline:**
- Initial response: Within 1 week
- Fix timeline: Depends on severity and complexity

## Security Considerations

### SSL Verification

This project **intentionally disables SSL certificate verification** to work behind corporate proxies:

```python
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

**Why this is necessary:**
- Corporate proxies (Zscaler, etc.) intercept HTTPS traffic
- Certificate chains are broken by man-in-the-middle proxies
- Data loading from NASA's servers would fail without this

**Risks and mitigations:**
- **Risk**: Susceptible to MITM attacks during data download
- **Mitigation**: Data source is public NASA database (non-sensitive)
- **Mitigation**: Data is read-only, no credentials transmitted
- **Alternative**: Users can place local `Outgassing_Db_rows.csv` in project root (fallback mechanism)

**If you need stricter SSL:**
1. Place your corporate root certificate (e.g., `zscaler-root-ca.cer`) in project root
2. The [Dockerfile](Dockerfile) will auto-install it during build
3. Submit a PR to make SSL verification configurable via environment variable

### Docker Security

- Container runs with default (non-root) user
- No privileged access required
- Only stdio transport used (no network ports exposed)
- `--rm` flag recommended for auto-cleanup after runs

### Data Privacy

- **No user data collected**: All processing is local
- **No telemetry**: No analytics or tracking
- **Public data only**: NASA's outgassing database is publicly available
- **No credentials**: No authentication or secrets required

### Dependencies

Dependencies are managed via `uv` and pinned in `uv.lock`:
- `fastmcp`: MCP server framework
- `pandas`: Data manipulation
- `rapidfuzz`: Fuzzy string matching
- `openpyxl`: Excel file support

Dependency updates are reviewed but may be infrequent due to free-time maintenance.

## Known Non-Issues

These are **not** security vulnerabilities:
- Disabled SSL verification (by design for corporate networks)
- Missing authentication (public data, no need)
- Missing rate limiting (local execution only)
- Docker container network access (required for stdio transport)

## Security Updates

Security patches will be applied to the `main` branch as needed. Watch the repository or enable notifications for security advisories.

---

*Last updated: January 11, 2026*
