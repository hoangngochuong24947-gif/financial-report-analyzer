from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.models.workspace_metrics import PromptProfile


class PromptProfileRegistry:
    """Registry of prompt profiles for archive-first analysis."""

    def __init__(self, profiles: Dict[str, PromptProfile]) -> None:
        self._profiles = profiles

    @classmethod
    def default(cls) -> "PromptProfileRegistry":
        return cls(
            {
                "archive_review": PromptProfile(
                    key="archive_review",
                    name="Archive Review",
                    system_prompt=(
                        "You are an archive-first A-share financial analyst. "
                        "Use the archived workspace as the primary source of truth. "
                        "AKShare is only a non-critical fallback when archive data is missing."
                    ),
                    context_title="Archive-First Financial Context",
                    context_guidance=[
                        "Start with the archived statement bundle.",
                        "Prefer evidence from Baidu archive manifests over live fetches.",
                        "Call out gaps explicitly instead of inventing values.",
                    ],
                ),
                "executive_summary": PromptProfile(
                    key="executive_summary",
                    name="Executive Summary",
                    system_prompt=(
                        "You are an archive-first A-share financial analyst focused on concise executive summaries."
                    ),
                    context_title="Executive Summary Context",
                    context_guidance=[
                        "Keep the answer brief and action-oriented.",
                        "Lead with the most important archive-backed metrics.",
                    ],
                ),
            }
        )

    def get(self, profile_key: str) -> PromptProfile:
        if profile_key not in self._profiles:
            raise KeyError(f"Unknown prompt profile: {profile_key}")
        return self._profiles[profile_key]
