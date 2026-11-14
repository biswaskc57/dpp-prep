# DMN readiness step on frozen run outputs (post hoc, illustrative)

Statuses: met · NOT MET · open = not yet assessed · n/a = not required. Readiness: ready = all applicable conditions met; not ready = any not met; undetermined otherwise.
## Overview: demonstrator state vs DMN readiness (element outcomes, all runs)

| proposer | tier | checked → ready | checked → undetermined | checked → not ready | flagged → not ready | flagged → other | unresolved → undetermined |
|---|---|---|---|---|---|---|---|
| oracle | simple | 0 | 44 | 0 | 4 | 0 | 1 |
| oracle | realistic | 0 | 15 | 0 | 5 | 0 | 1 |
| standin | simple | 0 | 44 | 0 | 4 | 0 | 1 |
| standin | realistic | 0 | 9 | 0 | 9 | 0 | 3 |
| ollama-gemma4-12b | simple | 0 | 117 | 0 | 27 | 0 | 3 |
| ollama-gemma4-12b | realistic | 0 | 39 | 0 | 24 | 0 | 0 |
| ollama-qwen3.5-9b | simple | 0 | 108 | 0 | 36 | 0 | 3 |
| ollama-qwen3.5-9b | realistic | 0 | 39 | 0 | 24 | 0 | 0 |
| ollama-qwen3.5-4b | simple | 0 | 117 | 0 | 27 | 0 | 3 |
| ollama-qwen3.5-4b | realistic | 0 | 27 | 0 | 36 | 0 | 0 |


## oracle, simple tier (49 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E06 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| uw_conflict | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| uw_other_size | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E06 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| uw_missing | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E03 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| composition_95 | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E03 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| wrong_product | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 44; flagged → not ready: 4; unresolved → undetermined: 1

## oracle, realistic tier (21 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real_baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E04 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E07 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E03 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| real_sash_only | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_sash_only | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 15; flagged → not ready: 5; unresolved → undetermined: 1

## standin, simple tier (49 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E06 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| uw_conflict | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| uw_other_size | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E06 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| uw_missing | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E03 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| composition_95 | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E03 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| wrong_product | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 44; flagged → not ready: 4; unresolved → undetermined: 1

## standin, realistic tier (21 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real_baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E03 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| real_baseline | E04 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_baseline | E07 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_stale_report | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E03 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| real_stale_report | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E06 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E07 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E03 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| real_sash_only | E04 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_sash_only | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_sash_only | E07 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |

Demonstrator state × readiness (all runs): checked → undetermined: 9; flagged → not ready: 9; unresolved → undetermined: 3

## ollama-gemma4-12b, simple tier (147 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_conflict | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E06 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| uw_conflict | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_other_size | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| uw_other_size | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_missing | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E06 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| uw_missing | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| ug_only_in_datasheet | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E03 | flagged | met | met | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| composition_95 | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| wrong_product | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 117; flagged → not ready: 27; unresolved → undetermined: 3

## ollama-gemma4-12b, realistic tier (63 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real_baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_baseline | E04 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E07 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E03 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| real_sash_only | E04 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 39; flagged → not ready: 24

## ollama-qwen3.5-9b, simple tier (147 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_conflict | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E06 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| uw_conflict | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_other_size | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| uw_other_size | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_missing | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E06 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| uw_missing | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| ug_only_in_datasheet | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E03 | flagged | met | met | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| composition_95 | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| composition_95 | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| wrong_product | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| wrong_product | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 108; flagged → not ready: 36; unresolved → undetermined: 3

## ollama-qwen3.5-9b, realistic tier (63 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real_baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_baseline | E04 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E03 | checked | met | met | met | met | open | met | open | open | undetermined |
| real_stale_report | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E07 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E03 | flagged | met | met | met | met | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E04 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 39; flagged → not ready: 24

## ollama-qwen3.5-4b, simple tier (147 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| baseline | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| baseline | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| baseline | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_conflict | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_conflict | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_conflict | E06 | flagged | met | met | met | NOT MET | open | NOT MET | open | open | not ready |
| uw_conflict | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_other_size | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_other_size | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_other_size | E06 | flagged | met | NOT MET | met | met | open | NOT MET | open | open | not ready |
| uw_other_size | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| uw_missing | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| uw_missing | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| uw_missing | E06 | unresolved | open | open | open | open | open | open | open | open | undetermined |
| uw_missing | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E03 | flagged | met | met | met | open | NOT MET | NOT MET | open | open | not ready |
| ug_only_in_datasheet | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| ug_only_in_datasheet | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| ug_only_in_datasheet | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E03 | flagged | met | met | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| composition_95 | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| composition_95 | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| composition_95 | E07 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| wrong_product | E04 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| wrong_product | E06 | checked | met | met | met | met | open | met | open | open | undetermined |
| wrong_product | E07 | checked | met | met | met | met | open | met | open | open | undetermined |

Demonstrator state × readiness (all runs): checked → undetermined: 117; flagged → not ready: 27; unresolved → undetermined: 3

## ollama-qwen3.5-4b, realistic tier (63 element outcomes)

| scenario | element | demonstrator | Available | Aligned | Representable | Of sufficient quality | Evidenced | Validated | Authorised | Current | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real_baseline | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| real_baseline | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_baseline | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_baseline | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_baseline | E07 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_stale_report | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_stale_report | E06 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_stale_report | E07 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E01 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E02 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E03 | flagged | met | NOT MET | met | open | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E04 | flagged | met | NOT MET | met | NOT MET | open | NOT MET | open | open | not ready |
| real_sash_only | E05 | checked | met | met | met | open | open | met | open | open | undetermined |
| real_sash_only | E06 | flagged | met | NOT MET | met | met | NOT MET | NOT MET | open | open | not ready |
| real_sash_only | E07 | flagged | met | NOT MET | met | NOT MET | NOT MET | NOT MET | open | open | not ready |

Demonstrator state × readiness (all runs): checked → undetermined: 27; flagged → not ready: 36
