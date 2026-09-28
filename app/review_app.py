"""Review screen for dpp-prep (Streamlit).

Run from the project root:   streamlit run app/review_app.py

Design (automation-bias measures from thesis section 1.5):
  * every proposed value is shown beside its source sentence, highlighted in context
  * no value is pre-selected; the reviewer must choose
  * "I compared the value with its source" starts unticked and is required
  * the screen only calls the service; every rule is enforced underneath,
    so the screen cannot bypass anything

Identities are simulated (pick a user in the sidebar); there is no real login.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.extract import StandInExtractor                  # noqa: E402
from dpp_prep.models import Actor, Role, State                 # noqa: E402
from dpp_prep.service import ActionRefused, PreparationService  # noqa: E402
from dpp_prep.states import TransitionRefused                  # noqa: E402

SCENARIOS = {
    "Baseline (all consistent)": {},
    "Uw conflict between documents": {"D3_performance_report": "V2_D3_uw_conflict"},
    "Uw declared for another size": {"D3_performance_report": "V3_D3_uw_other_size"},
    "Composition adds up to 95 %": {"D2_supplier_declaration": "V5_D2_composition_95"},
    "Supplier document for another product": {"D2_supplier_declaration": "V4_D2_wrong_product"},
    "Uw missing from all documents": {"D1_datasheet": "V1_D1_uw_missing",
                                      "D3_performance_report": "V1_D3_uw_missing"},
}
USERS = {
    "rita — reviewer": Actor(id="rita", role=Role.REVIEWER),
    "aki — approver": Actor(id="aki", role=Role.APPROVER),
    "rita — trying to approve": Actor(id="rita", role=Role.APPROVER),
}
STATE_ICON = {"checked": "🟢", "flagged": "🟠", "unresolved": "⚪", "reviewed": "🔵",
              "approved": "✅", "released": "📦", "proposed": "🟡", "required": "⚪"}


def source_paths(fmt: str, swap: dict) -> list[Path]:
    names = ["D1_datasheet", "D2_supplier_declaration", "D3_performance_report"]
    if fmt == "PDF":
        folder = lambda n: ROOT / "data/w100/pdf" / f"{n}.pdf"                      # noqa: E731
        paths = [folder(swap.get(n, n)) for n in names]
    else:
        paths = [(ROOT / "data/w100/variants" / f"{swap[n]}.md") if n in swap
                 else (ROOT / "data/w100/baseline" / f"{n}.md") for n in names]
    return paths + [ROOT / "data/w100/structured/erp_product_record.json"]


def new_service(scenario: str, fmt: str) -> PreparationService:
    svc = PreparationService(ROOT / "config/elements_w100.yaml",
                             StandInExtractor(ROOT / "config/standin_patterns_w100.yaml"))
    svc.start_run(source_paths(fmt, SCENARIOS[scenario]))
    svc.prepare_product()
    return svc


def evidence_html(svc: PreparationService, p) -> str:
    """The quote, highlighted, with one line of context before and after."""
    doc = svc.sources.get(p.evidence.source)
    quote = p.evidence.quote.strip()
    if doc is None or doc.kind != "document":
        return f"<mark>{html.escape(quote)}</mark>"
    lines = [l for l in doc.text.splitlines() if l.strip()]
    idx = next((i for i, l in enumerate(lines) if quote in l or l.strip() in quote and l.strip()), None)
    if idx is None:
        return f"<mark>{html.escape(quote)}</mark>"
    before = html.escape(lines[idx - 1]) if idx > 0 else ""
    after = html.escape(lines[idx + 1]) if idx + 1 < len(lines) else ""
    return (f"<div style='font-family:monospace;font-size:0.9em;line-height:1.6'>"
            f"<span style='opacity:0.6'>{before}</span><br>"
            f"<mark>{html.escape(lines[idx])}</mark><br>"
            f"<span style='opacity:0.6'>{after}</span></div>")


def act(fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
        st.session_state["flash"] = ("success", "Done.")
    except (ActionRefused, TransitionRefused) as e:
        st.session_state["flash"] = ("error", f"Refused: {e}")


# ------------------------------------------------------------------ page
st.set_page_config(page_title="dpp-prep review", layout="wide")
st.title("W-100 information review")
st.caption("Fictitious product and documents. Illustrative research data only.")

with st.sidebar:
    scenario = st.selectbox("Scenario", list(SCENARIOS), key="scenario")
    fmt = st.radio("Document format", ["Markdown", "PDF"], key="fmt", horizontal=True)
    user_label = st.selectbox("Acting as", list(USERS), key="user")
    user = USERS[user_label]
    if st.session_state.get("loaded") != (scenario, fmt) or st.button("Restart run", key="restart"):
        st.session_state["svc"] = new_service(scenario, fmt)
        st.session_state["loaded"] = (scenario, fmt)
        st.session_state.pop("package", None)
    svc: PreparationService = st.session_state["svc"]
    st.markdown(f"**Run** `{svc.run_id}`")
    st.markdown("Only ordinary code and people can move a value forward. The AI only suggests.")

flash = st.session_state.pop("flash", None)
if flash:
    (st.success if flash[0] == "success" else st.error)(flash[1])

# overview
rows = []
for eid, r in svc.records.items():
    d = svc.defs[eid]
    rows.append({"Element": eid, "Information": d.name, "Obtained by": "import (no AI)" if d.route == "import" else "AI suggestion",
                 "State": f"{STATE_ICON.get(r.state.value, '')} {r.state.value}",
                 "Value(s)": ", ".join(sorted({p.value[:40] for p in r.proposals})) or "—"})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# one panel per element
for eid, r in svc.records.items():
    d = svc.defs[eid]
    open_it = r.state in (State.CHECKED, State.FLAGGED, State.REVIEWED)
    with st.expander(f"{STATE_ICON.get(r.state.value, '')} {eid} · {d.description} — {r.state.value}", expanded=open_it):
        if r.state == State.UNRESOLVED:
            st.info("No supported value was found in the sources. Nothing has been invented.")
        for p in r.proposals:
            left, right = st.columns([1, 2])
            with left:
                st.markdown(f"**Value:** `{p.value}` {p.unit or ''}")
                st.caption(f"{p.method.value} · {p.evidence.source}"
                           + (f" · page {p.evidence.page}" if p.evidence.page else "")
                           + (f" · scope {p.scope}" if p.scope else ""))
            with right:
                st.markdown(evidence_html(svc, p), unsafe_allow_html=True)
        failed = [c for c in r.checks if not c.passed]
        if r.checks:
            st.markdown("**Checks:** " + (" ".join(f"✗ {c.name}: {c.message}" for c in failed)
                                          if failed else "all passed ✓"))
        if r.rejected:
            st.caption("Kept but not used: " + "; ".join(f"{p.value[:30]} ({p.evidence.source})" for p in r.rejected))
        if r.review:
            st.caption(f"Reviewed by {r.review.reviewer_id}" + (f": {r.review.note}" if r.review.note else ""))
        if r.approval:
            st.caption(f"Approved by {r.approval.approver_id} for version {r.approval.record_version}")

        if user.role == Role.REVIEWER and r.state in (State.CHECKED, State.FLAGGED) and r.proposals:
            choice = st.radio("Which value is correct?", [p.id for p in r.proposals], index=None,
                              format_func=lambda pid, r=r: next(f"{p.value[:50]} — {p.evidence.source}"
                                                                for p in r.proposals if p.id == pid),
                              key=f"sel_{eid}")
            inspected = st.checkbox("I compared the value with its source", value=False, key=f"insp_{eid}")
            note = st.text_input("Note (optional)", key=f"note_{eid}")
            if st.button("Accept selected value", key=f"accept_{eid}"):
                if choice is None:
                    st.session_state["flash"] = ("error", "Choose a value first.")
                else:
                    act(svc.review, eid, user, choice, evidence_inspected=inspected, note=note)
                st.rerun()
        if user.role == Role.APPROVER and r.state == State.REVIEWED:
            if st.button(f"Approve {eid}", key=f"approve_{eid}"):
                act(svc.approve, eid, user)
                st.rerun()

# release
st.divider()
st.subheader("Handover package")
if user.role == Role.APPROVER:
    if st.button("Release approved information", key="release"):
        try:
            st.session_state["package"] = dict(svc.release(user))
        except (ActionRefused, TransitionRefused) as e:
            st.error(f"Refused: {e}")
else:
    st.caption("Only an approver can release.")
pkg = st.session_state.get("package")
if pkg:
    st.write(f"Released: {', '.join(e['element_id'] for e in pkg['elements']) or 'nothing'}")
    for eid, why in pkg["excluded"].items():
        st.write(f"Not released {eid}: {why}")
    st.download_button("Download handover.json", json.dumps(pkg, indent=2, ensure_ascii=False),
                       file_name="handover.json", mime="application/json", key="download")

with st.expander("Diary (every step, including refusals)"):
    events = svc.audit.events(svc.run_id)
    st.dataframe(pd.DataFrame([{k: e[k] for k in ("seq", "time", "element_id", "actor_role", "actor_id", "action")}
                               for e in events]), hide_index=True, width="stretch")
