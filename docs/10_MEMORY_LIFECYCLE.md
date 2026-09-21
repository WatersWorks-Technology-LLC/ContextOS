# Memory Lifecycle

## Memory classes
### Raw event memory
Lossless history.

### Episodic memory
What happened in a bounded interaction/event cluster.

### Semantic memory
What the system currently believes or knows.

### Working memory
The task-specific packet currently supplied to Codex.

## Temperature
- HOT — frequently relevant to current work
- WARM — likely to recur
- COLD — retained but not routinely loaded
- ARCHIVE — source/evidence only unless explicitly retrieved

## Promotion signals
- repeated retrieval;
- recurrence across episodes;
- direct task dependency;
- high semantic importance;
- open decision/constraint/question;
- surprise or prediction error.

## Demotion signals
- resolved and old;
- superseded;
- low access frequency;
- graph-disconnected from active work;
- redundant with canonical state.

## Consolidation
Do not deeply summarize every turn. Create episodes cheaply. Promote recurrent or high-value clusters into semantic memory.

## Surprise-based retention
Events that change predictions, state, decisions, constraints, ownership, deadlines, or future commitments should receive elevated retention even if they occur once.

## Forgetting
Forgetting means removal from high-cost working layers. The source remains archived unless an explicit deletion policy applies.

## Replay testing
After major consolidation, replay benchmark questions against the new semantic state. If previously answerable high-value questions fail, retain more structure or source links.
