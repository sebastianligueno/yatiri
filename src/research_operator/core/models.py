from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CheckResult:
    label: str
    status: str


@dataclass(slots=True)
class ScanReport:
    project_name: str
    profile_id: str
    source_count: int
    pipeline_count: int
    report_path: Path


@dataclass(slots=True)
class ProjectState:
    project_name: str
    profile_id: str
    root: Path
    config_path: Path
    source_count: int
    run_count: int
    claim_count: int
    checks: list[CheckResult]
