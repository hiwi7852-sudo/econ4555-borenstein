# Data acquisition status

The latest complete quarter common to BTS origin–destination fares (historical DB1A and the applicable modern successor) and T-100 domestic operations remains **unverified**. No raw datasets have been downloaded.

On October 28, 2026, an HTTPS request to https://www.transtats.bts.gov/ failed at the environment proxy with `403 Forbidden` / `CONNECT tunnel failed`. The request did not reach BTS release listings.

The environment configuration service confirmed a saved draft adding `www.transtats.bts.gov`, `transtats.bts.gov`, and `www.bts.gov`, preserving existing package-manager presets. It requires publication: review and save the changes in environment settings, then publish the environment. A saved draft does not grant live access.

## Resume acquisition

1. Recheck the official portal through the existing proxy with TLS verification enabled.
2. Inspect official release listings and documentation for the current fare product and T-100. Verify ticket/market/coupon equivalents, sampling design, and complete period coverage.
3. Select the latest quarter shared by all required files, including all three months of operations. Record listing URLs and observed coverage here.
4. Download from verified official links with `scripts/fetch_bts.py`. Do not guess filenames or mistake HTML responses for archives. Add a new official download hostname through environment settings if documented redirects require one.
5. Check CSV schemas and actual year/quarter/month fields before declaring acquisition complete.

After verifying the quarter and links:

```sh
python3 scripts/fetch_bts.py --year YEAR --quarter QUARTER --url VERIFIED_OFFICIAL_ZIP_URL
```

Repeat `--url` for multiple archives. The helper validates ZIP integrity and CSV presence and records SHA-256 provenance. The selected quarter in its manifest is a requested label, not automatic verification of the data's period. Schema and period validation remain required. Raw downloads are ignored by Git.
