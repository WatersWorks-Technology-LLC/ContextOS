# VCL — Visual Context Language

## Purpose
VCL is a deterministic visual semantic grammar for relationships, hierarchy, state, chronology, uncertainty, and provenance. It is not a screenshot format.

## Source of truth
The canonical semantic graph. VCL is a compiled representation.

## Core node classes
`PER ORG SYS PRJ CMP GOAL DEC CON TSK DAT ART EVT QST FACT EXT MET`

## Rendering rule
Every significant visual semantic is redundant with a compact textual cue. Color must never be the sole carrier of meaning.

Examples:
```text
A ══ REQ! ══▶ B
A ══ PRO! ══┤ B
A - - CAU? C2 - -▶ B
```

## Spatial conventions
- up: goals/parents/abstraction
- left: sources/inputs/predecessors
- center: focus
- right: outputs/successors
- down: dependencies/implementation/constraints

Timeline always flows left-to-right.

## Deterministic rendering stack
Canonical graph -> NetworkX -> Graphviz layout -> SVG master -> PNG if target requires raster.

Do not use generative image models for canonical VCL.

## Visual quality constraints
- no gradients or decorative backgrounds;
- horizontal text only;
- generous gutters;
- minimum font/line sizes defined by target render profile;
- minimize edge crossings;
- split frames before making labels microscopic.

## Semantic zoom
Z0 identity; Z1 architecture/state; Z2 subsystem/relationships; Z3 operational detail; Z4 source expansion.

## Machine readability optimization
Renderer parameters must be benchmarked empirically. Human aesthetics are secondary to semantic decoding accuracy per visual-context cost.
