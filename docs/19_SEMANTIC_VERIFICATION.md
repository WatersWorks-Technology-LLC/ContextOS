# Semantic Verification

## Purpose
Compression must be measurable, reversible enough to validate, and capable of falling back.

## Loss classes
- L0 exact: identifiers, hashes, exact numbers, code, quotes
- L1 critical semantic: hard requirement, prohibition, permission, primary decision
- L2 relational: dependency/topology/current state
- L3 contextual: background and approximate context

Target preservation:
- L0 100%
- L1 100%
- L2 >=99% benchmark target
- L3 configurable

## Semantic checksum
Before encoding, derive the propositions that must remain recoverable. After encoding, decode/quiz and compare.

## Round-trip verification
`IR -> codec -> decoded IR -> semantic diff`

Reject if subject, relation, object, hardness, state, negation, temporal validity, or provenance changes for protected assertions.

## Dual extraction
For important ambiguous source passages, run two independent local extraction passes. Agreement raises confidence; disagreement creates a conflict and retains more raw evidence.

## Fallback ladder
1. chosen compact codec
2. less aggressive same codec
3. structured English/native structure
4. direct source excerpts

## Verification cache
Cache successful codec artifacts by canonical semantic hash + codec version + target-model profile.

## No silent repair
The verifier may reject or downgrade an encoding. It may not invent missing semantics in order to make the compressed packet pass.
