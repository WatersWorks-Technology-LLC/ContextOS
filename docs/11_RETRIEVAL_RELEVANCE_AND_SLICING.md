# Retrieval, Relevance, and Semantic Slicing

## Retrieval cascade
1. Exact ID/name/alias lookup
2. Lexical/BM25/FTS
3. Embedding similarity
4. Metadata filters
5. Knowledge-graph distance
6. Temporal relevance
7. Recurrence/importance weighting
8. Optional local reranker

No single retrieval mechanism is authoritative.

## Candidate scoring
A practical initial score:

`score = 0.28 lexical + 0.24 embedding + 0.22 graph + 0.10 temporal + 0.08 importance + 0.08 recurrence`

Treat values as tunable, not doctrine.

## Semantic dead-code elimination
The current task defines semantic roots. Traverse only relations capable of influencing the task—typically `REQ`, `DEP`, `BLK`, `CAU`, `CON`, `SUPR`, `SRC`, plus domain-approved edges. Remove disconnected information.

## Semantic program slicing
For causal questions, prefer paths that explain the requested result rather than every fact about the same entities.

Example:
```text
TOKEN_FAIL -> AUTH_FAIL -> DEPLOY_BLOCKED
```

## Semantic Bloom filters
Partition large archives and maintain Bloom filters over normalized concept IDs. Use only to prove probable irrelevance: a negative can skip a partition; a positive still requires ordinary retrieval.

## Minimal evidence set
Once required assertions are known, solve an approximate weighted set-cover problem over source fragments. Select sources maximizing newly covered required assertions per context cost.

## Answerability index
For large documents/episodes, maintain the classes of questions and entities they can answer. Use it for routing, not as substitute evidence.
