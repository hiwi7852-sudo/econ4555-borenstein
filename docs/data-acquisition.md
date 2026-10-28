# Spring 2025 pilot: acquisition status

## Target dates and scope

The requested target is **2025 Q2: April 1–June 30, 2025**, the calendar quarter most closely matching Spring 2025. This is a requested period, not verified file coverage. Use **DB1B**, approved by the professor, and matching T-100; do not acquire DB1C. If Q2 is unavailable, verify neighboring periods and report the nearest common-quarter substitution explicitly.

## Dataset inventory

| Dataset | Intended coverage | Obtained | Size / rows verified |
|---|---|---|---|
| DB1B Market | 2025 Q2 | No | Unknown |
| DB1B Ticket, if required for ticket origins and trip structure | 2025 Q2 | No | Unknown |
| DB1B Coupon, only if needed for itinerary details | 2025 Q2 | No | Unknown |
| T-100 Domestic Segment | April, May, June 2025 | No | Unknown |
| T-100 Domestic Market, if needed | April, May, June 2025 | No | Unknown |

**No research datasets were obtained.** No source availability, archive size, actual date coverage, schema, or row counts have been established. No DB1C files were requested. No subset has been selected, and no Tables 1 or 2 or OLS estimates have been produced.

## Access evidence and remaining blocker

On October 28, 2026, HTTPS requests to the official BTS TranStats portal and candidate DB1B Q2 and annual T-100 archive locations failed at the environment proxy with `403 Forbidden` / `Tunnel connection failed`. See [acquisition-attempts.json](acquisition-attempts.json). The candidate archive paths are unverified naming patterns, not confirmed available files. These failures do not demonstrate that Spring 2025 data are unavailable; BTS was not reached.

The current environment reports an enforced restricted policy without BTS domains. The saved draft (revision 2) includes `www.transtats.bts.gov`, `transtats.bts.gov`, and `www.bts.gov`, preserving existing package-manager presets. Thus the prior draft save succeeded, but the running policy has not incorporated these additions. Review and save the changes in environment settings, then publish the environment to activate them. No token or additional secret is required by the evidence so far.

## Completed work

- Updated README to Spring 2025 DB1B and matching T-100, Tables 1 and 2, OLS only.
- Preserved the original Question 1 plan unchanged in `docs/initial-plan-question-1.md` and commit `35cdf82`.
- Defined a manageable acquisition order: Market first, Ticket as needed, Coupon only if necessary; exclude DB1C.
- Added a 250 MiB per-archive compressed-size guard to the streaming downloader, enforced against both declared and actual transfer sizes. Oversized/invalid downloads are removed rather than retained as subsets.
- Defined memory-conscious processing and a reproducible market-based subset strategy that preserves within-market competitors and documents the coverage of airport-share denominators.
- Recorded source-access attempts. Raw data remain outside Git.

## Resume after network activation

1. Recheck https://www.transtats.bts.gov/ through the existing proxy with TLS verification enabled.
2. Inspect official DB1B and T-100 listings to confirm Q2 coverage and download links; inspect archive sizes before transfers. Do not substitute DB1C.
3. Download Q2 DB1B Market first. Inspect schema before adding Ticket or Coupon. Request quarter/month-filtered T-100 if supported; if an annual archive is needed, record its coverage and retain only April–June during preparation.
4. Use verified official ZIP links with the existing helper:

   ```sh
   python3 scripts/fetch_bts.py --year 2025 --quarter 2 --url VERIFIED_OFFICIAL_ZIP_URL
   ```

   Repeat `--url` for multiple archives. The default compressed limit is 250 MiB per archive; the limit is a chosen workflow constraint, not a measured file size. Seek smaller official exports before raising it. The helper does not yet automate portal form submissions or column/month filters.
5. Validate ZIP integrity, CSV schemas, actual dates, keys, passenger totals, and join coverage. The manifest's requested quarter is a label, not proof of coverage. Record provenance and SHA-256 hashes.
6. Process CSVs in chunks. If needed, select complete airport-pair markets by a predeclared traffic rule, retaining all eligible carriers/fares within them and computing airport shares from broader data where feasible. Do not use a truncated download as a subset.
7. Prepare the Table 1 yield comparisons and Table 2 OLS analysis. Audit supplementary controls: financial costs, tourism, and scarcity may require other sources or a clearly identified reduced-control specification.
