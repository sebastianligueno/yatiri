from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml


def load_all_profiles() -> list[dict]:
    profiles_dir = resources.files("research_operator").joinpath("profiles")
    profiles: list[dict] = []
    for entry in profiles_dir.iterdir():
        if entry.name.endswith(".yaml"):
            profiles.append(yaml.safe_load(entry.read_text(encoding="utf-8")))
    return profiles


def load_profile(profile_id: str) -> dict:
    for profile in load_all_profiles():
        if profile.get("id") == profile_id:
            return profile
    for profile in load_all_profiles():
        if profile.get("id") == "mixed_methods":
            return profile
    raise ValueError("No se encontro perfil mixed_methods")


def infer_profile(root: Path) -> dict:
    best_profile = None
    best_score = -1

    for profile in load_all_profiles():
        score = 0
        detect = profile.get("detect", {})
        for rel_path in detect.get("any_paths", []):
            if (root / rel_path).exists():
                score += 2
        for rel_file in detect.get("any_files", []):
            if (root / rel_file).exists():
                score += 3
        for ext in detect.get("extensions", []):
            if any(root.rglob(f"*{ext}")):
                score += 1

        if score > best_score:
            best_score = score
            best_profile = profile

    return best_profile or load_profile("mixed_methods")


def run_profile_checks(root: Path, profile: dict) -> list[dict]:
    results: list[dict] = []

    for check in profile.get("checks", []):
        check_id = check.get("id", "unknown")
        if check["type"] == "exists":
            ok = (root / check["path"]).exists()
        elif check["type"] == "min_matches":
            matches = list(root.glob(check["glob"]))
            ok = len(matches) >= int(check.get("min", 1))
        else:
            ok = False

        results.append(
            {
                "id": check_id,
                "label": check_id.replace("_", " "),
                "status": "ok" if ok else "missing",
            }
        )

    return results
