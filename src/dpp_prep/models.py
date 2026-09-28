"""Data model for DPP information preparation (v0.2).

Plain-language map:
  ElementDefinition  one line of the wish list
  SourceDocument     a document or structured record, with its fingerprint (SHA-256)
  Evidence           where a value came from: document, exact quote, position
  Proposal           one candidate value for one element, with its evidence
  ReviewDecision     a named reviewer chose one proposal and confirmed seeing the evidence
  Approval           a different, named approver approved that exact version
  Record             everything known about one element, and its current state
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class State(str, Enum):
    REQUIRED = "required"      # on the wish list, nothing found yet
    PROPOSED = "proposed"      # at least one supported candidate value exists
    CHECKED = "checked"        # all rule checks passed
    FLAGGED = "flagged"        # a check failed, or a person raised a problem
    REVIEWED = "reviewed"      # a reviewer chose one value after seeing its evidence
    APPROVED = "approved"      # a different person approved that exact version
    RELEASED = "released"      # exported for DPP-related handover
    UNRESOLVED = "unresolved"  # no supported value found; nothing is invented


class Role(str, Enum):
    AI = "ai"
    SYSTEM = "system"          # ordinary software, e.g. rule checks
    REVIEWER = "reviewer"
    APPROVER = "approver"


class Method(str, Enum):
    AI = "ai"                  # proposed by an extractor from a document
    IMPORT = "import"          # taken directly from a structured record, no AI
    MANUAL = "manual"          # entered by a reviewer as a correction


class Actor(BaseModel):
    """A named person or component. Identities are simulated in this demonstrator,
    not connected to real authentication."""
    id: str
    role: Role


class ElementDefinition(BaseModel):
    id: str
    name: str
    description: str
    route: str = "extract"                 # extract | import
    import_field: Optional[str] = None
    unit: Optional[str] = None
    value_type: str = "text"               # text | number
    must_contain: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    required_scope: str = "product"
    controls: list[str] = Field(default_factory=list)


class SourceDocument(BaseModel):
    name: str
    kind: str = "document"                 # document | structured
    text: str
    data: Optional[dict[str, Any]] = None  # parsed content of a structured record
    pages: Optional[list[str]] = None      # page texts, for PDFs (page 1 = pages[0])

    @property
    def sha256(self) -> str:
        return sha256(self.text)


class Evidence(BaseModel):
    source: str
    quote: str                             # exact text the value came from
    context_quote: Optional[str] = None    # e.g. the line stating the reference size
    field: Optional[str] = None            # for structured records: which field
    page: Optional[int] = None
    doc_sha256: Optional[str] = None       # filled in when the quote is verified
    start: Optional[int] = None            # character position of the quote
    end: Optional[int] = None

    def is_grounded(self) -> bool:
        return bool(self.quote and self.quote.strip())


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    element_id: str
    value: str
    unit: Optional[str] = None
    scope: Optional[str] = None
    product_id: Optional[str] = None
    evidence: Evidence
    method: Method = Method.AI
    produced_by: str = "unknown"           # extractor or person that produced it

    def content(self) -> dict:
        return self.model_dump(exclude={"id"})


class CheckResult(BaseModel):
    name: str
    passed: bool
    message: str = ""
    proposal_id: Optional[str] = None
    mandatory: bool = True


class ReviewDecision(BaseModel):
    reviewer_id: str
    selected_proposal_id: str
    evidence_inspected: bool
    record_version: str
    note: str = ""
    time: str = Field(default_factory=now)


class Approval(BaseModel):
    approver_id: str
    record_version: str
    time: str = Field(default_factory=now)


class LogEntry(BaseModel):
    time: str = Field(default_factory=now)
    actor: Role
    actor_id: Optional[str] = None
    action: str
    detail: str = ""


class Record(BaseModel):
    element_id: str
    state: State = State.REQUIRED
    proposals: list[Proposal] = Field(default_factory=list)
    rejected: list[Proposal] = Field(default_factory=list)   # kept, never deleted
    checks: list[CheckResult] = Field(default_factory=list)
    checks_version: Optional[str] = None
    review: Optional[ReviewDecision] = None
    approval: Optional[Approval] = None
    log: list[LogEntry] = Field(default_factory=list)

    @property
    def version(self) -> str:
        """Fingerprint of the candidate values and their evidence. Any change to a
        value or its evidence produces a new version, which invalidates earlier
        checks, reviews and approvals."""
        payload = json.dumps([p.content() for p in self.proposals], sort_keys=True, default=str)
        return sha256(payload)[:16]

    @property
    def selected(self) -> Optional[Proposal]:
        if not self.review:
            return None
        return next((p for p in self.proposals if p.id == self.review.selected_proposal_id), None)

    @property
    def value(self) -> Optional[str]:
        return self.selected.value if self.selected else None

    def note(self, actor: Role, action: str, detail: str = "", actor_id: Optional[str] = None) -> None:
        self.log.append(LogEntry(actor=actor, actor_id=actor_id, action=action, detail=detail))
