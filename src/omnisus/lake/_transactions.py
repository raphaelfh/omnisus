from dataclasses import dataclass


@dataclass
class TransactionReceipt:
    committed: bool = False
    snapshot_id: int | None = None


class TransactionStateError(RuntimeError):
    """The handle cannot safely continue its managed transaction workflow."""


class CommitOutcomeUnknown(TransactionStateError):  # noqa: N818 - mandated public API
    """COMMIT raised; do not infer rollback or retry the write automatically."""
