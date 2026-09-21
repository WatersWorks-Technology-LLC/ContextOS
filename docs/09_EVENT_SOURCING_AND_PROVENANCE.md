# Event Sourcing and Provenance

## Rule
Historical inputs are append-only. Any correction is a new event referencing what it corrects.

## Why
Semantic projections and summaries can be wrong. Event sourcing preserves recoverability and auditability.

## Event examples
- USER_PROMPT
- ASSISTANT_RESPONSE
- TOOL_CALL
- TOOL_RESULT
- FILE_WRITE
- GIT_COMMIT
- DECISION_DECLARED
- CONSTRAINT_CHANGED
- CORRECTION
- SOURCE_ADDED

## Projection workflow
```text
event -> extraction candidate -> validation -> semantic projection -> context commit
```

## Provenance requirements
L0/L1 assertions must have at least one source unless they are deterministic system observations generated directly by ContextOS.

## Source precedence
1. original source payload
2. deterministic observation of current environment
3. verified semantic assertion
4. derived/inferred memory
5. compact codec

## Temporal provenance
Track separately:
- event time;
- observed time;
- validity start/end;
- assertion time;
- supersession time.

## Correction example
Do not edit:
`A12: architecture=A`

Append:
`EV91 correction of A12`

Project:
`A12[HIST]`
`A44[CUR]: architecture=B`
`A44 SUPR A12`
