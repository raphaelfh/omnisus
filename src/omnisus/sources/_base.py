"""Shared value types for source families: scopes, results and reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ALL_UFS: tuple[str, ...] = (
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
)
"""The 27 federative units. A two-letter code outside this set is not a state."""

UF_CODES: dict[str, str] = {
    "RO": "11",
    "AC": "12",
    "AM": "13",
    "RR": "14",
    "PA": "15",
    "AP": "16",
    "TO": "17",
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
    "MG": "31",
    "ES": "32",
    "RJ": "33",
    "SP": "35",
    "PR": "41",
    "SC": "42",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
    "DF": "53",
}
"""IBGE code of each UF, as ``SIM/CID10/TABELAS/TABUF.DBF`` lists them (registry
``sim-tabelas-tabuf-273f7e756a1a``); a test checks it against the packaged ``aux_uf``."""


@dataclass(frozen=True)
class ScopeKey:
    """Identifies one slice of a dataset (e.g., SP/2024 or MG/2024/01).

    `mes` is None for yearly datasets, set for monthly (SIH).
    """

    uf: str | None
    """None denotes a national source, never an artificial record-level UF."""
    ano: int
    mes: int | None = None

    def __str__(self) -> str:
        if self.mes is None:
            return f"{self.uf or 'national'}_{self.ano}"
        return f"{self.uf or 'national'}_{self.ano}_{self.mes:02d}"


@dataclass
class ImportResult:
    """Outcome of one import_scope call."""

    rows: int
    bytes_written: int
    duration_seconds: float
    snapshot_id: int | None = None
    run_id: str | None = None
    batch_id: str | None = None
    publication_id: str | None = None


ScopeStatus = Literal["ok", "skipped", "failed"]

ScopeCode = Literal[
    "outside_coverage", "not_listed", "unchanged", "fetch_failed", "ingest_failed", "rolled_back"
]
"""Why a scope did not import; see :attr:`ScopeOutcome.code`."""


@dataclass(frozen=True)
class ScopeOutcome:
    """What happened to one scope in an import run.

    ``skipped`` and ``failed`` are different facts and must not be collapsed.
    ``skipped`` means the listing does not have the scope (``not_listed``), it
    is outside the row's coverage (``outside_coverage``), or the same source is
    already published (``unchanged``). ``failed`` is worth retrying.
    """

    scope: ScopeKey
    status: ScopeStatus
    result: ImportResult | None = None
    """Set when ``status == "ok"``, ``None`` otherwise."""

    reason: str | None = None
    """Set when ``status`` is ``skipped`` or ``failed``, ``None`` otherwise."""

    code: ScopeCode | None = None
    """Why the scope did not import; ``None`` only for ``ok``."""


@dataclass(frozen=True)
class ImportReport:
    """Per-scope outcomes of one import run.

    Normal FTP completion reports each requested input position. An
    ImportAbortedError carries a partial report of determined outcomes and
    separately identifies unresolved positions; inspect before retrying.

    Inspect :attr:`failed` — never the report's truthiness. An empty run and a
    run where everything failed are different facts, and no falsy sentinel
    stands in for either.
    """

    outcomes: tuple[ScopeOutcome, ...]
    run_id: str | None = None

    @property
    def rows(self) -> int:
        """Total rows ingested across successful scopes."""
        return sum(o.result.rows for o in self.outcomes if o.result is not None)

    @property
    def ok(self) -> tuple[ScopeOutcome, ...]:
        return tuple(o for o in self.outcomes if o.status == "ok")

    @property
    def skipped(self) -> tuple[ScopeOutcome, ...]:
        return tuple(o for o in self.outcomes if o.status == "skipped")

    @property
    def failed(self) -> tuple[ScopeOutcome, ...]:
        return tuple(o for o in self.outcomes if o.status == "failed")


class ImportAbortedError(RuntimeError):
    """Partial progress is known, but the remaining inputs need inspection."""

    def __init__(
        self,
        report: ImportReport,
        unresolved: tuple[tuple[int, ScopeKey], ...],
    ) -> None:
        self.report = report
        self.unresolved = unresolved
        super().__init__(
            f"import aborted: {len(unresolved)} input(s) unresolved; inspect before retry"
        )
