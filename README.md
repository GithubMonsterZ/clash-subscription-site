# Clash subscription builder

Dependency-free static subscription generator for Render. The repository contains no node credentials, subscription links, or deployment credentials.

Set `DMIT_NODE_JSON` to the VLESS REALITY node JSON and `SUBSCRIPTION_TOKEN` to a cryptographically random 43-character URL-safe token in the hosting environment. Run `python3 build.py`; publish `public/`.

The generated YAML supports Clash Verge Rev with Mihomo. It contains one node, loopback-only proxy access, and generic private-network/China direct routing. It does not enable TUN or bind a particular network adapter.

An optional second subscription accepts an explicitly authorized two-hop configuration from `FULL_CONFIG_JSON` and an independent `FULL_SUBSCRIPTION_TOKEN`. It preserves that export's complete routing and DNS policies. Both variables must be set together. The original single-node link and content remain unchanged. Machine-specific controller, TUN and adapter settings are excluded; existing process-path rules only match machines with the corresponding installation paths. Generated files use the client's compatible geodata databases.

The generated URL is a bearer link: anyone with the link can download the node credentials. Keep it private to intended recipients. Rotate the token and redeploy to revoke the old download link; already downloaded node credentials require separate server-side revocation.

Never commit generated output or environment values. Disable preview deployments. Configure `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow, noarchive`, and `Referrer-Policy: no-referrer` response headers on the hosting service.

An optional independent VPS38 single-node subscription uses `VPS38_NODE_JSON` and `VPS38_SUBSCRIPTION_TOKEN`. Both must be set together; all subscription paths must differ. It uses the same generic routing as the original single-node export and preserves the explicitly enabled `reality-opts.support-x25519mlkem768` compatibility setting. Existing subscriptions keep their original content.
