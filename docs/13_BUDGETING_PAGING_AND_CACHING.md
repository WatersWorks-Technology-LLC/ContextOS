# Budgeting, Paging, Deltas, and Caching

## Context budget auction
Every candidate capsule offers multiple resolutions and estimated costs. Rank alternatives by marginal semantic utility per cost.

Suggested utility inputs:
- task relevance;
- semantic importance;
- uncertainty/conflict;
- expected near-term use;
- recency;
- risk if omitted.

Hard invariants are pinned outside the auction.

## Semantic resolutions
- Z0 identity
- Z1 current state
- Z2 key relationships
- Z3 detailed semantic capsule
- Z4 raw evidence

## Demand paging
Codex starts with selected Z0–Z3 memory. An MCP `expand` or `source` call acts as a semantic page fault.

## Promotion
Repeated page faults promote an object to a hotter memory tier.

## Thrashing
If an object is loaded/evicted repeatedly inside a time window, temporarily pin it.

## Prefetch
After task classification, prefetch likely neighbors into local cache but do not automatically inject them.

## Semantic deltas
For continuing sessions send changes relative to a known context commit:
```text
@BASE c812
@Δ
T17:ACT→DONE
+D31
C9:soft→hard
```

## Keyframes
Generate a full semantic checkpoint when any of these hold:
- delta chain > configured count;
- cumulative delta > configured fraction of keyframe;
- major state transition;
- verification failure;
- explicit debug request.

## Stable prefix
Keep dictionaries/protocol/invariants stable and dynamic task material at the tail to maximize cacheability and reduce needless prompt churn.
