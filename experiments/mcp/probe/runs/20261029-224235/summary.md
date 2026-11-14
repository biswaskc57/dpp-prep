# Agent probe: scores (post hoc, illustrative)

| pool | element | prompt | run | outcome | final | submissions | wrong attempted | wrong reached checked | outdated/component docs read | not-relevant docs read | retry behaviour | B retry rule exceeded | tool calls | stop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basic | E03 | A | 1 | correct value | Pine wood 78 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 % doc_3(suitable) | 1 | 0 | 0 | 0 | 2 | - | - | 5 | final answer |
| basic | E03 | B | 1 | correct value | Pine wood 78 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 % doc_3(suitable) | 1 | 0 | 0 | 0 | 2 | - | no | 5 | final answer |
| basic | E06 | A | 1 | correct value | 1.1 doc_2(suitable) | 1 | 0 | 0 | 0 | 1 | - | - | 5 | final answer |
| basic | E06 | B | 1 | correct value | 1.1 doc_2(suitable) | 4 | 0 | 0 | 0 | 1 | identical resubmission x1; evidence-based correction x2 | yes | 8 | final answer |
| realistic | E03 | A | 1 | correct value, left flagged | Pine wood 78 %, aluminium 18 %, EPDM 3 %, steel 1 % doc_4(suitable) | 1 | 0 | 0 | 0 | 3 | - | - | 6 | final answer |
| realistic | E03 | B | 1 | correct value | pine wood 78 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 % doc_4(suitable) | 2 | 0 | 0 | 0 | 3 | unsupported resubmission x1 | no | 8 | final answer |
| realistic | E06 | A | 1 | correct value | 1.1 doc_1(suitable) | 1 | 0 | 0 | 0 | 0 | - | - | 3 | final answer |
| realistic | E06 | B | 1 | correct value | 1.1 doc_1(suitable) | 1 | 0 | 0 | 0 | 1 | - | no | 6 | final answer |
| sash | E03 | A | 1 | correct abstention (after a wrong submission) | None  | 1 | 1 | 0 | 1 | 3 | - | - | 7 | final answer |
| sash | E03 | B | 1 | correct abstention | None  | 0 | 0 | 0 | 1 | 3 | - | no | 6 | final answer |
| sash | E06 | A | 1 | conservative abstention | None  | 1 | 0 | 0 | 0 | 0 | - | - | 3 | final answer |
| sash | E06 | B | 1 | correct value | 1.1 doc_3(suitable) | 5 | 0 | 0 | 0 | 1 | unsupported resubmission x1; evidence-based correction x1; identical resubmission x1 | yes | 10 | final answer |
| stale | E03 | A | 1 | correct value, left flagged | Pine wood 78 %, aluminium 18 %, EPDM 3 %, steel 1 % doc_2(suitable) | 1 | 0 | 0 | 0 | 1 | - | - | 4 | final answer |
| stale | E03 | B | 1 | correct value | Pine wood 78 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 % doc_2(suitable) | 1 | 0 | 0 | 0 | 4 | - | no | 7 | final answer |
| stale | E06 | A | 1 | wrong value, left flagged | 1.2 doc_1(outdated) | 1 | 1 | 0 | 1 | 0 | - | - | 3 | final answer |
| stale | E06 | B | 1 | correct value | 1.1 doc_5(suitable) | 2 | 0 | 0 | 1 | 1 | - | no | 8 | final answer |

## Totals

- tasks: 16; outcomes: correct value: 10; correct value, left flagged: 2; correct abstention (after a wrong submission): 1; correct abstention: 1; conservative abstention: 1; wrong value, left flagged: 1
- wrong values attempted: 2; wrong values that reached checked: 0
- final answers relying on an unsuitable document: 1
- prompt B tasks exceeding the retry rule: 2

By prompt:
- A: correct value: 3; correct value, left flagged: 2; correct abstention (after a wrong submission): 1; conservative abstention: 1; wrong value, left flagged: 1; wrong reached checked: 0
- B: correct value: 7; correct abstention: 1; wrong reached checked: 0
