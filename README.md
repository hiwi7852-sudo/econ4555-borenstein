# Airline competition replication: single-quarter pilot

This project updates Severin Borenstein’s 1989 paper, “Hubs and High Fares: Dominance and Market Power in the U.S. Airline Industry,” for Spring 2025, targeting **2025 Q2 (April 1–June 30, 2025)**, the calendar quarter that most closely matches spring. Deliverables are a modern **Table 1** and the **OLS columns of Table 2**. We will not estimate 2SLS models or Table 3.

The initial Question 1 plan is preserved unchanged in [docs/initial-plan-question-1.md](docs/initial-plan-question-1.md) and commit `35cdf82`.

## 1. Acquire Spring 2025 DB1B and matching T-100

Use **DB1B for 2025 Q2**, subject to confirming its official availability, and matching April, May, and June 2025 T-100 observations. The professor has approved Spring 2025 DB1B; do not download DB1C or switch to a newer quarter. If Q2 is unavailable, verify adjacent quarters and choose the nearest common available quarter, reporting the substitution explicitly.

The paper used historical DB1A; this pilot deliberately uses DB1B. Begin with **DB1B Market** for market fares, passengers, endpoints, and market carriers. Inspect its schema before adding **DB1B Ticket** for ticket-level origins and trip structure. Download **DB1B Coupon** only if segment and carrier details needed for the pilot cannot be recovered from the smaller components. Distinguish market-level allocated fares from ticket fares when implementing the paper’s directional-fare definition.

Prioritize manageable files: inspect sizes before downloading; stream compressed archives and read CSVs in chunks rather than extracting every file or loading entire tables into memory. The downloader defaults to a **250 MiB compressed-size limit per archive** and stops oversized transfers. This is a practical pilot limit, not an assertion about actual source file sizes. Obtain quarter/month-filtered official downloads where available; if T-100 is distributed annually, retain only Q2 observations during preparation and report the annual archive’s coverage separately.

If full-quarter files remain impractical, define a reproducible subset of airport-pair markets selected by a predeclared traffic rule. Retain every eligible carrier and fare observation within those markets rather than randomly discarding fares or airlines. Compute airport shares from the broader quarter before restricting regression markets; otherwise label them as subset shares and explain the resulting limitation. A subset Table 1 must label its benchmark as a subset rather than national domestic traffic. Report the subset rule and coverage. Never treat a partial or truncated download as a usable subset.

Acquire **T-100 Domestic Segment** data for performed departures, seats, passengers, aircraft information, and distances. Add **T-100 Domestic Market** where needed to distinguish on-flight markets and airport enplanements from nonstop segments. Restrict operations to scheduled passenger service.

Official sources: [BTS TranStats](https://www.transtats.bts.gov/) and [BTS](https://www.bts.gov/). Q2 is the requested target; source availability and actual downloaded coverage remain unverified because network access is blocked; [acquisition status](docs/data-acquisition.md) records the evidence and next steps.

## 2. Construct a comparable sample

- Define airport-pair origin–destination markets. Connecting passengers are not local customers of the connecting airport.
- Normalize one-way and round-trip fares to directional travel using the modern survey’s documented structure, avoiding double-counting.
- Follow the original exclusions where fields permit: first class, interline travel, international itineraries, more than one plane change per direction, invalid fares, and unmatched operations. Document modern fare-class limitations and choose a defensible low-fare threshold rather than mechanically applying the nominal 1987 $10 cutoff.
- Map reporting/marketing and operating carriers, regional affiliates, and parent airlines consistently before joining fares and operations or computing shares.
- Include all eligible competitors in share and concentration denominators. Define regression-carrier coverage from modern data availability rather than retaining the nine historical airlines.
- Begin with the original Table 2 eligibility rule: at least ten passengers daily and 10% route share, accounting for survey sampling. Select one eligible carrier per route randomly with a fixed seed, matching the original design. An all-carrier analysis with route-clustered inference is a sensitivity check.

## 3. Produce a modern Table 1

Recreate the descriptive fare-per-mile comparisons using nonstop origin–destination distance and the original distance categories: under 200, 200–500, 500–1,000, 1,000–1,500, 1,500–2,000, and over 2,000 miles. Implement nonoverlapping boundaries and document passenger weighting and yield aggregation.

Include the domestic benchmark and selected modern dominant airline–airport pairs. For each pair, compare the airline’s fares away from that airport, its fares to/from that airport, and other airlines’ fares to/from that airport. Display both origination and enplanement shares. Declare dominance and traffic thresholds before examining fare premiums; do not automatically reuse the historical hub examples. These are descriptive comparisons.

## 4. Produce an updated Table 2 with OLS

Estimate separate log-fare equations for passenger-weighted 20th, 50th, and 80th percentile fares. These are percentiles of fares actually paid, not advertised fares or individual-level quantile regressions.

Preserve the distinction between carrier-specific dominance and overall concentration. Target the original controls: route distance, load factor, aircraft size, frequency, circuity, on-plane stops, plane changes, endpoint origination share (ORGSHARE), endpoint origination HHI (ORGHERF), route share (RUTSHARE), route HHI (RUTHERF), competitors’ standardized costs, tourism orientation, carrier effects, and airport scarcity controls. Follow the original log-versus-level specification where feasible.

Construct endpoint weights from where passengers originally began their tickets. Distinguish airport originations from enplanements, which include connecting traffic. Build service measures from itinerary segments, then aggregate with passenger weights; document limitations of joining modern itinerary records to monthly T-100 operations.

T-100 and fare data alone may not supply competitor financial costs, tourism measures, or credible airport scarcity indicators. Audit fields first, identify necessary supplementary sources, and maintain a crosswalk from each original variable to its modern counterpart. If controls are unavailable, report a clearly labeled reduced-control pilot specification with explicit omissions or proxies; do not call it an exact Table 2 replication.

Report coefficients, standard errors, sample sizes, fit statistics, and fare differences associated with percentage-point share changes. Use heteroskedasticity-robust standard errors for the one-carrier-per-route baseline. OLS estimates are conditional associations: fares, shares, and service choices are jointly determined. Fare premiums do not directly establish markups or welfare effects.

## 5. Validate and deliver

Keep raw downloads separate from code and record source URLs, retrieval times, release coverage, sizes, and SHA-256 hashes. Validate archive integrity, schemas, actual periods, carrier mappings, join coverage, duplicates, fares, passenger totals, share sums, and HHI bounds. Report sample attrition at each exclusion.

Deliver a reproducible preparation and OLS pipeline, data/variable crosswalk, updated Tables 1 and 2, and a short discussion of dominance premiums and comparability limits. Multi-quarter panels, Table 3, 2SLS, and causal extensions are outside this pilot.
