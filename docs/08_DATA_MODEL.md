# Data Model

## Workspace
Fields: `workspace_id`, canonical root, aliases, created_at, policy_profile.

## Event
Append-only historical observation.
Fields:
- event_id
- workspace_id
- session_id/turn_id
- event_type
- actor
- timestamp
- raw_payload or artifact pointer
- parent_event_ids
- content_hash

## Source
Addressable evidence object.
Fields:
- source_id
- source_type
- URI/path/reference
- hash
- created/observed timestamps
- sensitivity class
- content metadata

## Entity
Persistent semantic object.
Fields:
- entity_id
- type
- canonical_name
- aliases
- attributes
- provenance

## Assertion
Atomic semantic statement.
Fields:
- assertion_id
- subject_id
- relation
- object_id or literal
- lifecycle state
- strength
- confidence
- origin (`explicit|observed|derived|inferred`)
- valid_from/valid_until
- observed_at/asserted_at
- source_ids
- supersedes

## Relation
Graph edge optimized for traversal. It may be derived from an assertion but keeps graph-specific weighting and indexing fields.

## Episode
Clustered narrative/event object. Not assumed to be truth.

## Decision
Specialized semantic object containing alternatives, outcome, rationale, preconditions, temporal validity, and sources.

## Constraint
Specialized assertion with hardness and scope.

## Conflict
Links incompatible assertions and maintains resolution status.

## OpenQuestion
Tracks unresolved context, priority, related entities, and closure event.

## Capsule
Multi-resolution view of a semantic object. Must reference canonical IDs rather than become its own source of truth.

## ContextCommit
Semantic-state checkpoint with parent, diff, timestamp, cause, and verification status.

## ContextDelta
Compact changes from a base commit.

## RetrievalLog
Records query, candidates, filters, selected memory, model calls, and eventual usage.

## CodecArtifact
Stores generated NCC/VCL/VCL-A representations, source semantic hash, codec version, verification score, and target-model profile.
