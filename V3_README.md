# EV Charging Intelligence V3

V3 is built directly on V2.3 and keeps the TDX ingestion architecture.

## V3 product direction
- Map-first charging discovery
- Live connector status dashboard
- Charging cost calculator
- Station Health Score
- Recommended stations
- Local favorites via localStorage
- PWA/service worker shell
- Existing OCPP Log Analyzer retained

## Data architecture
V3 continues to consume:
- `data/stations.json`
- `data/charging_points.json`
- `data/connectors.json`
- `data/live_status.json`
- `data/tdx_meta.json`
- `data/pricing.json`
- `data/market.json`

No TDX credentials are exposed in the browser. GitHub Actions remains responsible for ingestion.

## Health Score
This is a front-end analytical score, not an official CPO SLA:
- 75% live available ratio
- 15% penalty protection based on fault/offline ratio
- 10% station master-data completeness

Power and availability are also used for the station recommendation score.

## Deployment
1. Replace repository files with this V3 package.
2. Keep GitHub Secrets `TDX_CLIENT_ID` and `TDX_CLIENT_SECRET`.
3. Keep existing TDX workflows.
4. GitHub Pages can serve the site as a static application.

## Notes
The map uses Leaflet and OpenStreetMap tiles. Pricing values remain informational and should be labeled as verified only when backed by an official source.
