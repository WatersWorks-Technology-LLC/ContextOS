# ADR-006: Compression failures degrade toward explicit context

**Status:** Accepted

If verification fails, ContextOS emits a less compressed representation or direct evidence. It never silently drops protected semantics to satisfy a budget.
