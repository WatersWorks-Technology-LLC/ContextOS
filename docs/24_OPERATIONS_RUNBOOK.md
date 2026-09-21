# Operations Runbook

## Daily checks
- ContextOS health endpoint;
- Ollama availability;
- queue backlog;
- semantic verification failure rate;
- DB size and WAL health;
- context-preparation p50/p95;
- retrieval miss reports.

## If context is stale
1. inspect current context commit;
2. inspect relevant event/source history;
3. run projection rebuild for affected entities;
4. invalidate capsules/codecs;
5. rerun benchmark/regression question.

## If ContextOS injects incorrect context
1. retrieve exact source;
2. identify bad assertion/extraction;
3. append correction event;
4. mark bad assertion historical/rejected;
5. invalidate dependent capsules and embeddings where necessary;
6. add regression test.

## If latency spikes
Inspect:
- model escalation frequency;
- vector index latency;
- cache hit rate;
- hook synchronous work;
- DB locks;
- context packet size;
- repeated verification fallbacks.

Move heavy work off synchronous hooks before increasing timeouts.

## If retrieval misses known context
Check in order:
- workspace mismatch;
- entity aliases;
- lexical index;
- embedding index/model consistency;
- graph connectivity;
- temporal filter;
- dead-code elimination threshold.

## If semantic thrashing occurs
Pin repeatedly accessed capsules, increase working-set budget, or improve task-root prediction.

## Disaster recovery
The event/source store is authoritative. Rebuild semantic projections, graph, embeddings, capsules, VCL, and caches from events/sources plus explicit correction metadata.
