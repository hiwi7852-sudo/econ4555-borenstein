# Airline competition replication: single-quarter pilot

This project updates Severin Borenstein’s 1989 paper, “Hubs and High Fares: Dominance and Market Power in the U.S. Airline Industry,” for one recent quarter. Deliverables are a modern **Table 1** and the **OLS columns of Table 2**. We will not estimate 2SLS models or Table 3.

The initial Question 1 plan is preserved unchanged in [docs/initial-plan-question-1.md](docs/initial-plan-question-1.md) and commit `35cdf82`.

## 1. Select and acquire the latest common quarter

Select the latest complete quarter publicly available for both the required origin–destination fare survey and all three months of T-100 operations. Verify official release coverage before selecting a period; do not infer availability from the calendar or mix periods.

The original paper used **DB1A**. Verify the applicable modern Origin and Destination Survey product, its relationship to **DB1B**, and subsequent reporting changes. Record the actual product name, sampling rate, coverage, and field changes rather than silently labeling a successor DB1A. Obtain ticket, market, and coupon/itinerary components as needed.

Acquire **T-100 Domestic Segment** data for performed departures, seats, passengers, aircraft information, and distances. Add **T-100 Domestic Market** where needed to distinguish on-flight markets and airport enplanements from nonstop segments. Restrict operations to scheduled passenger service.

Official sources: [BTS TranStats](https://www.transtats.bts.gov/) and [BTS](https://www.bts.gov/). The selected quarter remains unverified because network access is blocked; [acquisition status](docs/data-acquisition.md) records the evidence and next steps.

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
