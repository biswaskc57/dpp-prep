# Post-hoc probe: sash-only composition (E03)

**Status: post hoc.** This probe was designed on 18 October 2026, after inspecting the results of the 17–18 October model runs. It was not part of the pre-registered evaluation protocol (ADR 0002) and its result is reported separately from the evaluation results.

## Question

In the production-like scenario `real_sash_only`, gemma4:12b proposed the supplier's sash composition ("Sash profile set, share of sash mass: pine wood 74 %, aluminium 21 %, EPDM seals 4 %, steel fittings 1 %.") as the whole-window material composition (E03). The element was flagged, not left unresolved as expected. Which check stopped it, and would the frozen controls have stopped it without that check?

## Method

`scripts/probe_sash.py` re-runs the frozen evidence check and rule checks of dpp-prep v0.3.2 (commit 2be1ea5, unchanged) on the recorded proposal, twice:

1. **Recorded:** the proposal as the model returned it, with product id `PP-SA-100` (the sash part number).
2. **Counterfactual:** the same proposal with product id `W-100`; everything else unchanged.

The recorded proposal is taken from `model_outputs_ollama-gemma4-12b_realistic_md_20261018-023008.jsonl` (identical in all three runs). Tests: `tests/test_probe_sash.py` (PR01, PR02).

## Result

Saved in `probe_sash_result.json`.

| Condition | Quote located | Failed checks | State |
|---|---|---|---|
| Recorded (`PP-SA-100`) | yes | identity | flagged (as in the evaluation run) |
| Counterfactual (`W-100`) | yes | none | **checked** |

## Interpretation and limits

The sash composition passed the evidence, support and composition-sum checks. It was stopped only because the reported product id did not match. With the expected product id, the frozen controls would have accepted a component-level composition as the whole-window composition. No rule in the element profile distinguishes a component's composition from the product's.

The probe shows that the recorded checks can be satisfied by this altered proposal. It does not show that the sash composition is correct for the window; that is the limitation being demonstrated. One manipulated input, chosen after seeing the results, is an illustration of a control gap, not a measurement of how often it occurs.
