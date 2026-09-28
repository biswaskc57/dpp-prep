"""The single workflow (service layer). Tests, the demo and any future review
screen all call these methods, so the rules cannot be bypassed by calling
steps in a different order.

    start_run()        load sources, fingerprint them, open a run in the diary
    prepare_product()  for every element: suggest -> fact-check -> rule-check
    review()           a reviewer chooses one proposal after seeing its evidence
    correct()          a reviewer enters a corrected value with its own evidence
    flag()             a reviewer or approver raises a problem
    approve()          a different person approves that exact version
    release()          a named approver exports approved, unchanged records
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable, Optional

from .audit import AuditStore
from .checks import all_passed, run_checks
from .export import Package, build_export
from .extract import StructuredImporter
from .models import (Actor, Evidence, Method, Proposal, Record, ReviewDecision,
                     Role, SourceDocument, State)
from .profile import load_profile
from .sources import load_sources
from .states import TransitionRefused, transition
from .verify import keep_grounded


class ActionRefused(Exception):
    pass


class PreparationService:
    def __init__(self, profile_path: str | Path, extractor, importer=None,
                 audit: Optional[AuditStore] = None):
        self.product, self.defs = load_profile(profile_path)
        self.extractor = extractor
        self.importer = importer or StructuredImporter()
        self.audit = audit or AuditStore()
        self.sources: dict[str, SourceDocument] = {}
        self.records: dict[str, Record] = {}
        self.run_id: Optional[str] = None

    # ------------------------------------------------------------ helpers
    def _event(self, r: Optional[Record], role: Role, action: str,
               actor_id: Optional[str] = None, detail=None) -> None:
        self.audit.add(self.run_id, role.value, action,
                       element_id=r.element_id if r else None, actor_id=actor_id,
                       record_version=r.version if r else None, detail=detail)

    def _move(self, r: Record, target: State, role: Role, detail: str = "",
              actor_id: Optional[str] = None) -> None:
        try:
            transition(r, target, role, detail, actor_id)
        except TransitionRefused as e:
            self._event(r, role, "refused", actor_id, str(e))
            raise
        self._event(r, role, f"-> {target.value}", actor_id, detail or None)

    def _require_role(self, actor: Actor, role: Role, action: str) -> None:
        if actor.role != role:
            self._event(None, actor.role, "refused", actor.id, f"{action} requires role {role.value}")
            raise ActionRefused(f"{action} requires role {role.value}, not {actor.role.value}")

    def _record(self, element_id: str) -> Record:
        if element_id not in self.records:
            raise ActionRefused(f"unknown element {element_id}")
        return self.records[element_id]

    def _check(self, r: Record) -> None:
        d = self.defs[r.element_id]
        r.checks = run_checks(d, r.proposals, self.product["id"], self.product.get("required_scope", "product"))
        r.checks_version = r.version
        failed = [f"{c.name}: {c.message}" for c in r.checks if not c.passed]
        self._event(r, Role.SYSTEM, "checks run", detail={"failed": failed})
        if all_passed(r.checks):
            self._move(r, State.CHECKED, Role.SYSTEM, "all checks passed")
        else:
            self._move(r, State.FLAGGED, Role.SYSTEM, "; ".join(failed))

    # ------------------------------------------------------------ workflow
    def start_run(self, source_paths: Iterable[str | Path]) -> str:
        self.sources = load_sources(source_paths)
        self.run_id = uuid.uuid4().hex[:12]
        self.records = {}
        self._event(None, Role.SYSTEM, "run started", detail={
            "profile_version": self.product["profile_version"],
            "extractor": getattr(self.extractor, "name", "unknown"),
            "importer": getattr(self.importer, "name", "unknown"),
            "sources": {n: d.sha256 for n, d in self.sources.items()},
        })
        return self.run_id

    def prepare_product(self) -> dict[str, Record]:
        for eid, d in self.defs.items():
            r = Record(element_id=eid)
            self.records[eid] = r
            raw: list[Proposal] = []
            if d.route == "import":
                for doc in self.sources.values():
                    raw += self.importer.propose(d, doc)
                role = Role.SYSTEM
            else:
                for doc in self.sources.values():
                    if doc.kind == "document":
                        raw += self.extractor.propose(d, doc)
                role = Role.AI
            kept, dropped = keep_grounded(raw, self.sources)
            for p, reason in dropped:
                r.rejected.append(p)
                r.note(Role.SYSTEM, "dropped unsupported proposal", f"{p.value!r}: {reason}")
                self._event(r, Role.SYSTEM, "dropped unsupported proposal",
                            detail={"value": p.value, "source": p.evidence.source, "reason": reason})
            if kept:
                r.proposals = kept
                self._move(r, State.PROPOSED, role, f"{len(kept)} supported proposal(s) via {d.route}")
                self._check(r)
            else:
                self._move(r, State.UNRESOLVED, role, "no supported value found")
        for entry in getattr(self.extractor, "raw_log", []):      # raw model output, for reproducibility
            self._event(None, Role.AI, "model output", detail=entry)
        return self.records

    def review(self, element_id: str, reviewer: Actor, selected_proposal_id: str,
               evidence_inspected: bool, note: str = "") -> Record:
        self._require_role(reviewer, Role.REVIEWER, "review")
        r = self._record(element_id)
        if r.state not in (State.CHECKED, State.FLAGGED):
            raise ActionRefused(f"{element_id} cannot be reviewed in state {r.state.value}")
        if not evidence_inspected:
            self._event(r, Role.REVIEWER, "refused", reviewer.id, "evidence not inspected")
            raise ActionRefused("the reviewer must inspect the evidence before accepting a value")
        selected = next((p for p in r.proposals if p.id == selected_proposal_id), None)
        if selected is None:
            raise ActionRefused(f"proposal {selected_proposal_id} not found for {element_id}")
        d = self.defs[element_id]
        trial = run_checks(d, [selected], self.product["id"], self.product.get("required_scope", "product"))
        if not all_passed(trial):
            failed = "; ".join(f"{c.name}: {c.message}" for c in trial if not c.passed)
            self._event(r, Role.REVIEWER, "refused", reviewer.id, f"selected value fails checks: {failed}")
            raise ActionRefused(f"the selected value fails checks ({failed}); correct or reject it instead")
        for p in [p for p in r.proposals if p.id != selected.id]:          # keep, never delete
            r.rejected.append(p)
            self._event(r, Role.REVIEWER, "proposal not selected", reviewer.id,
                        {"value": p.value, "source": p.evidence.source})
        r.proposals = [selected]
        r.checks, r.checks_version = trial, r.version
        r.review = ReviewDecision(reviewer_id=reviewer.id, selected_proposal_id=selected.id,
                                  evidence_inspected=True, record_version=r.version, note=note)
        self._move(r, State.REVIEWED, Role.REVIEWER, note or "value accepted after inspecting evidence", reviewer.id)
        return r

    def correct(self, element_id: str, reviewer: Actor, value: str, evidence: Evidence,
                unit: Optional[str] = None, scope: Optional[str] = None,
                product_id: Optional[str] = None) -> Record:
        """A correction needs its own evidence, and restarts checks, review and approval."""
        self._require_role(reviewer, Role.REVIEWER, "correct")
        r = self._record(element_id)
        p = Proposal(element_id=element_id, value=value, unit=unit, scope=scope,
                     product_id=product_id or self.product["id"], evidence=evidence,
                     method=Method.MANUAL, produced_by=reviewer.id)
        kept, dropped = keep_grounded([p], self.sources)
        if dropped:
            self._event(r, Role.REVIEWER, "refused", reviewer.id, f"correction not supported: {dropped[0][1]}")
            raise ActionRefused(f"correction not supported by its evidence: {dropped[0][1]}")
        r.rejected.extend(r.proposals)
        r.proposals = [p]
        self._move(r, State.PROPOSED, Role.REVIEWER, f"corrected to {value!r}", reviewer.id)
        self._check(r)
        return r

    def flag(self, element_id: str, actor: Actor, note: str) -> Record:
        r = self._record(element_id)
        self._move(r, State.FLAGGED, actor.role, note, actor.id)
        return r

    def approve(self, element_id: str, approver: Actor) -> Record:
        self._require_role(approver, Role.APPROVER, "approve")
        r = self._record(element_id)
        self._move(r, State.APPROVED, Role.APPROVER, "approved", approver.id)
        return r

    def release(self, approver: Actor, out_path: Optional[str | Path] = None) -> Package:
        self._require_role(approver, Role.APPROVER, "release")
        records = list(self.records.values())
        pkg = build_export(self.product["id"], records,
                           names={e: d.name for e, d in self.defs.items()},
                           run_id=self.run_id, profile_version=self.product["profile_version"],
                           released_by=approver.id)
        pkg.validate()
        for item in pkg.elements:
            self._move(self.records[item["element_id"]], State.RELEASED, Role.APPROVER, "released", approver.id)
        self._event(None, Role.APPROVER, "package released", approver.id,
                    {"included": [e["element_id"] for e in pkg.elements], "excluded": pkg.excluded})
        if out_path:
            pkg.write(out_path)
        return pkg
