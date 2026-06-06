from __future__ import annotations

import os
from typing import Optional

from dora_event import DoraEventV2


class EventEnricher:
    def enrich(self, event: DoraEventV2) -> DoraEventV2:
        """
        Enrich event with additional metadata.
        Returns enriched copy — never mutates input.
        """
        enriched = event.model_copy()

        if not enriched.correlation_id:
            enriched = enriched.model_copy(
                update={"correlation_id": event.work_id},
            )

        return enriched

    def auto_enrich_from_environment(self, event: DoraEventV2) -> DoraEventV2:
        """Apply GitHub Actions environment variables when present."""
        updates: dict[str, str] = {}

        repo = self._extract_repo_from_env()
        if repo is not None:
            updates["repo"] = repo

        actor = self._extract_actor_from_env()
        if actor is not None:
            updates["actor"] = actor

        commit_sha = self._extract_commit_sha()
        if commit_sha is not None:
            updates["commit_sha"] = commit_sha

        workflow_run_id = self._extract_workflow_run_id()
        if workflow_run_id is not None:
            updates["workflow_run_id"] = workflow_run_id

        if not updates:
            return event

        return event.model_copy(update=updates)

    def _extract_repo_from_env(self) -> Optional[str]:
        """Extract repo from GITHUB_REPOSITORY env var."""
        return os.environ.get("GITHUB_REPOSITORY")

    def _extract_actor_from_env(self) -> Optional[str]:
        """Extract actor from GITHUB_ACTOR env var."""
        return os.environ.get("GITHUB_ACTOR")

    def _extract_commit_sha(self) -> Optional[str]:
        """Extract commit SHA from GITHUB_SHA env var."""
        return os.environ.get("GITHUB_SHA")

    def _extract_workflow_run_id(self) -> Optional[str]:
        """Extract workflow run ID from GITHUB_RUN_ID."""
        return os.environ.get("GITHUB_RUN_ID")
