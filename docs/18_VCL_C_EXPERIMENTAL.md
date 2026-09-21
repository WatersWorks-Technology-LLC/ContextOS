# VCL-C — Dense Visual Context Code (Experimental)

## Goal
Explore QR-like density without encoding arbitrary prose bytes. VCL-C encodes semantic IDs and relationships directly.

## Packet concept
```text
HEADER | DICTIONARY | ENTITIES | RELATIONS | STATE | TIME | SOURCES | ECC
```

## Non-goal
Do not gzip 100k tokens into an image and then decode them back into 100k tokens. That compresses storage, not model context.

## Research hypothesis
A structured semantic packet may communicate more task-relevant information per visual token than rendered prose if symbols are optimized for the target vision encoder.

## Error correction
Use unequal protection:
- hard constraints/decisions: high redundancy;
- ordinary relations: normal redundancy;
- peripheral associations: low redundancy.

## Channel-capacity experiment
Measure correctly recovered semantic assertions per visual-token/image budget while progressively reducing cell size and redundancy.

## Production policy
Disabled by default. Never the only representation of L0/L1 information. Requires semantic checksum and source escape hatch.
