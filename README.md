Borenstein’s *“Hubs and High Fares: Dominance and Market Power in the U.S. Airline Industry”* asks whether an airline’s dominance on a route and at its endpoint airports helps it charge higher fares. I recommend organizing this project around a close replication with recent data, followed by clearly separated extensions.

The key distinction to preserve is **an airline’s own market share versus overall market concentration**. Borenstein finds that dominant airlines can sustain higher fares without creating an equivalent price “umbrella” for smaller competitors. His results also suggest that airport dominance matters beyond dominance on individual routes, although separating these effects precisely is difficult.

**1. Establish the replication benchmarks**

The original study uses third-quarter 1987 data and two complementary approaches:

- A fare equation relating an airline’s prices to its route share, endpoint-airport shares, concentration, and cost and service characteristics.
- A relative-price equation comparing two airlines serving the same route, which removes characteristics common to that route.

Both approaches examine passenger-weighted **20th, 50th, and 80th percentile fares**. These are percentiles of fares actually paid, rather than advertised prices or separate regressions on individual passengers.

Our central questions would be whether, in recent data:

- Airlines with larger route shares charge higher fares, holding concentration constant.
- Airlines with larger endpoint-airport shares charge higher fares, holding route share constant.
- These relationships differ across the fare distribution.
- Smaller competitors share in dominant airlines’ fare premiums.

**2. Define a comparable sample and market**

Start with domestic airport-pair origin–destination markets, keeping connecting itineraries distinct from the individual flight segments they use. A passenger connecting through a hub should not count as a local customer of that hub.

The original analysis covers nine major airlines, excludes first-class and interline travel, and permits at most one plane change per directional trip. Its regression eligibility thresholds require a carrier to carry at least ten passengers daily and have at least 10% route share. We should document these rules and decide which can be reproduced faithfully.

For modern data, carrier ownership, regional affiliates, codeshares, and marketing versus operating carriers will require explicit treatment. Market shares should include eligible competitors beyond the airlines selected for regression observations.

**3. Build the data around the paper’s concepts**

We can leave source selection open while establishing the required information:

| Information | Purpose |
|---|---|
| Fares, passenger counts, ticket origins, destinations, and itineraries | Construct fare percentiles, route shares, and airport origination shares |
| Flight operations, seats, passengers, and distances | Measure frequency, load factors, aircraft size, connections, and circuity |
| Carrier financial information | Construct cost controls and competitors’ cost measures |
| Airport and local-market characteristics | Account for congestion, tourism, and demand differences |

A particularly important distinction is **airport originations versus enplanements**: the latter includes connecting passengers. Borenstein primarily measures airport dominance using originations, weighting the endpoints by where travelers originally began their tickets.

We should also determine whether modern reported fares adequately capture ancillary charges and differences in fare products. Any limitations would be documented before interpreting changes since 1987.

**4. Reproduce descriptive patterns before estimating models**

First produce sample counts, exclusion summaries, market-share distributions, and fare distributions. Then recreate the logic of the paper’s descriptive comparisons: dominant airlines’ fares at their hubs, their fares elsewhere, and competitors’ fares at those hubs, accounting for distance.

These checks will help identify construction errors and establish whether the basic hub-premium pattern appears in the newer sample.

**5. Estimate the two core models and assess identification**

Begin with the original log-fare specifications and carrier effects. Present ordinary least squares alongside an assessment of the original instrumental-variable approach.

Borenstein recognizes that fares and route shares are jointly determined. His instruments use carriers’ presence at both endpoint airports to predict route share and construct an instrument for route concentration. We should evaluate their relevance and exclusion assumptions in the modern industry rather than assume they remain valid.

The original study also acknowledges potentially endogenous service choices and airport dominance. Consequently, the baseline results should be interpreted as conditional relationships unless a stronger identification strategy is justified.

**6. Add focused modern robustness checks**

After establishing the comparable baseline:

- Use multiple quarters, accounting for seasonality and separating pandemic disruption if relevant.
- Retain all eligible carrier observations with appropriate clustered inference, alongside the original random-selection approach.
- Compare airport-pair and metropolitan-area market definitions.
- Examine sensitivity to carrier grouping, sample thresholds, and nonstop versus connecting service.
- Assess whether low-cost-carrier presence changes dominance premiums.

Panel fixed effects or an entry, merger, or airport-capacity event could support a later causal extension, subject to available data and credible assumptions.

The initial deliverables should be a variable crosswalk to the paper, a reproducible cleaning pipeline, descriptive tables, and counterparts to its two main regression tables. The final interpretation should distinguish fare premiums from directly measured markups and welfare effects: higher hub fares alone do not establish whether hub networks’ costs outweigh their service benefits.
