# SPDX-License-Identifier: MIT
"""Durable authorization and control intents, never an application submit worker."""
from __future__ import annotations

import uuid

from .m1_types import AttemptRecord, ExecutionMode, Fence, ResolvedOperation
from .workspace_store import AttemptConflictError, NotFoundError, WorkspaceStore


class AttemptService:
    """Use the active store; identifiers are resolved only inside its authority."""

    def __init__(self, store: WorkspaceStore) -> None:
        if not isinstance(store, WorkspaceStore):
            raise TypeError("active WorkspaceStore required")
        self._store = store

    def _operation(self, operation_id: str) -> ResolvedOperation:
        with self._store._connect() as db:
            row = db.execute("SELECT project_id FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            raise NotFoundError("operation not found")
        return self._store.get_operation(row[0], operation_id)

    def authorize(self, operation_id: str, client_request_id: str, mode: ExecutionMode,
                  challenger_of: str | None) -> AttemptRecord:
        return self._store.authorize_attempt(self._operation(operation_id), client_request_id, mode, challenger_of)

    def reconcile(self, attempt_id: str) -> AttemptRecord:
        """Request poll/validated lookup. Unsupported lookup stays actionable pending.

        No adapter is invoked here, no empty history is evidence of absence, and
        no request key is minted. The later sole worker consumes this intent.
        """
        return self._store._record_intent(attempt_id, "reconcile_intent")

    def request_cancel(self, attempt_id: str) -> AttemptRecord:
        self._store._record_intent(attempt_id, "cancel_intent")
        # When the worker is busy, the durable intent is consumed at its next
        # boundary. Web threads never impersonate the lifetime lock holder.
        owner = "cancel-" + uuid.uuid4().hex
        try:
            with self._store.worker_lock(owner) as epoch:
                with self._store._transaction() as db:
                    self._store._event(db, attempt_id, "claimed", {"owner_id": owner, "epoch": epoch})
                return self._store.apply_cancel_intent(Fence(attempt_id, owner, epoch))
        except AttemptConflictError as error:
            if str(error) != "WORKER_BUSY":
                raise
        return self._store._lookup_attempt(attempt_id)
