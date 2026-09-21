# Observability and Metrics

## Required per-turn telemetry
- raw candidate tokens/characters;
- candidates retrieved by each stage;
- post-filter/post-slice estimate;
- final packet tokens;
- visual assets and estimated visual cost;
- ContextOS preparation latency;
- each Ollama call/model/latency;
- codec selected;
- verification attempts/failures;
- Codex expansion/source calls;
- cache hits/misses;
- page faults and thrashing indicators;
- context commit ID.

## Core metrics
### Semantic Channel Efficiency
`SCE = correct task-relevant semantic assertions / inference cost`

### Semantic Integrity Score
`SIS = correctly decoded required assertions / required assertions`

### Compression ratio
Raw candidate context divided by delivered context. Never report this alone.

### Retrieval precision/recall
Measured against benchmark-required memory.

### Page-fault rate
High values suggest under-provisioned working context.

### Context thrash rate
Repeated loading/eviction of same semantic objects.

### Local offload ratio
Fraction of context-processing operations completed locally without Codex.

## Dashboards
Create views for:
- latency waterfall;
- context reduction waterfall;
- verification failure by codec/model;
- most frequently paged entities;
- stale-state incidents;
- retrieval miss cases;
- cost saved versus baseline.
