# VCL-A — Visual Context Atlas

## Purpose
Pack multiple VCL frames into a single structured visual surface while allocating more pixels to higher-value context.

## Tile structure
Each tile has:
- address (`A1`, `B2`, ...);
- semantic type (`STATE`, `DEC`, `CONFLICT`, ...);
- zoom level;
- source semantic hash.

## Variable-resolution packing
Allocate area approximately by:
`relevance × importance × required_detail × uncertainty_weight`

High-priority working state may receive 4x the area of peripheral historical context.

## Layout algorithms
Start with deterministic treemap/guillotine packing. Prefer stable tile ordering across adjacent turns to reduce position churn.

## Neighbor leakage safeguards
- explicit tile borders;
- gutters;
- tile headers;
- no edges crossing tile boundaries unless the atlas explicitly represents a cross-tile relation;
- semantic checks after rendering.

## Expansion
Codex can request `expand B2` via MCP, causing ContextOS to return a higher-resolution semantic or visual representation.

## When to use
Only when target-model vision support and benchmark results show a benefit over compact text/native tables.
