# Clash subscription builder

Dependency-free static subscription generator for Render. The repository contains no node credentials, subscription links, or deployment credentials.

Set `DMIT_NODE_JSON` to the VLESS REALITY node JSON and `SUBSCRIPTION_TOKEN` to a cryptographically random 43-character URL-safe token in the hosting environment. Run `python3 build.py`; publish `public/`.

The generated YAML supports Clash Verge Rev with Mihomo. It contains one node, loopback-only proxy access, and generic private-network/China direct routing. It does not enable TUN or bind a particular network adapter.

The generated URL is a bearer link: anyone with the link can download the node credentials. Keep it private to intended recipients. Rotate the token and redeploy to revoke the old download link; already downloaded node credentials require separate server-side revocation.

Never commit generated output or environment values. Disable preview deployments. Configure `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow, noarchive`, and `Referrer-Policy: no-referrer` response headers on the hosting service.
