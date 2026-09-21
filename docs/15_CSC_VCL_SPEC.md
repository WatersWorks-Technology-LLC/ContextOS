# CSC-VCL Experimental Specification

## Purpose
Controlled Simplified Chinese is an alternative high-density semantic surface codec. It combines restricted Simplified Chinese concept tokens, logical/mathematical symbols, and the same VCL relation vocabulary.

## Status
Experimental. It must compete against NCC-VCL and structured English on actual target-model token cost, rendered area, and semantic decoding accuracy.

## Rules
- one canonical meaning per controlled token;
- proper names/IDs stay unchanged when translation reduces precision;
- relationships use VCL codes when Chinese shorthand is ambiguous;
- exact values remain exact;
- no reliance on natural-language pronouns;
- same operator precedence as NCC-VCL;
- compiler must be reversible to canonical IR.

## Example
```text
SYS[现] REQ! 源验
¬验 DAT PRO! OVR RAW
D22[现] SUPR! D14[史]
```

## Evaluation
CSC-VCL is enabled only for experimental model profiles until benchmark evidence shows higher semantic efficiency than NCC-VCL.
