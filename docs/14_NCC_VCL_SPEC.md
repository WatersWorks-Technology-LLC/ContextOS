# NCC-VCL Specification

## Definition
Neanderthal Context Compression is a controlled telegraphic English intermediate representation augmented with logical/mathematical symbols and VCL relation codes. The term describes stripped grammar only; it is not a claim about historical Neanderthal language.

## Principle
**Delete grammar before deleting meaning. Replace linguistic redundancy with explicit structure.**

## Operator precedence
1. grouping `()`
2. negation `¬`
3. state `[]`
4. relation operators
5. conjunction `∧`
6. disjunction `∨`
7. implication `⇒`
8. source `@`

## Core relations
Structural: `OWN CT IN USE DEP OUT ASN`
Requirement: `REQ PRO BLK RES CON SUP`
Causal: `CAU ENA PREV`
Evidence: `SRC EV+ EV- DER`
Temporal: `PRE FOL SUPR`
General: `REL PREF ABOUT`

`!` denotes hard/binding relation; `?` uncertainty.

## State codes
`CUR ACT PLAN PROP HIST DEPR REJ BLK DONE UNK FAIL OK WAIT`

## Confidence
`C5` canonical -> `C0` unknown.

## Controlled abbreviations
Examples: `auth cfg src dst ctx mem msg prev nxt err tok svc`.
Each token must have one canonical codec meaning. Familiar slang such as `b4` or `bc` may be tested but must not survive if it increases ambiguity or token cost.

## Examples
Natural:
> The current authentication service requires a valid token and deployment is blocked because the token service failed.

NCC-VCL:
```text
AUTH[CUR] REQ! TOK[val]
TOK_SVC[FAIL] CAU DEPLOY[BLK]
```

## Exact escape
Use `TXT{...}` or an exact source pointer for strings that may not be transformed.

## Density levels
- N0 natural English
- N1 telegraphic English
- N2 controlled abbreviations
- N3 NCC
- N4 NCC-VCL
- N5 symbol-heavy NCC-VCL
- N6 visual VCL

Compiler chooses the least aggressive level satisfying budget and verification.
