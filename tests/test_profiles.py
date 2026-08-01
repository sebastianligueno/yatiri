from __future__ import annotations

from pathlib import Path

import pytest

from research_operator.core.profiles import (
    infer_profile,
    load_all_profiles,
    load_profile,
    run_profile_checks,
)


class TestLoadAllProfiles:
    def test_carga_los_tres_perfiles_del_paquete(self):
        ids = {p["id"] for p in load_all_profiles()}
        assert {"mixed_methods", "quant_social_r", "historical_discourse"} <= ids


class TestLoadProfile:
    def test_encuentra_perfil_por_id(self):
        assert load_profile("quant_social_r")["label"] == "Quant Social R"

    def test_id_desconocido_cae_a_mixed_methods(self):
        assert load_profile("no-existe")["id"] == "mixed_methods"

    def test_sin_ningun_perfil_lanza_value_error(self, monkeypatch):
        import research_operator.core.profiles as profiles_mod
        monkeypatch.setattr(profiles_mod, "load_all_profiles", lambda: [])
        with pytest.raises(ValueError):
            load_profile("cualquiera")


class TestInferProfile:
    def test_estructura_generica_infiere_mixed_methods(self, tmp_path: Path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "README.md").write_text("x", encoding="utf-8")
        assert infer_profile(tmp_path)["id"] == "mixed_methods"

    def test_estructura_r_infiere_quant_social_r(self, tmp_path: Path):
        scripts = tmp_path / "analysis" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "01_limpieza.R").write_text("# script", encoding="utf-8")
        (tmp_path / "paper").mkdir()
        (tmp_path / "data-derived").mkdir()
        (tmp_path / "renv.lock").write_text("{}", encoding="utf-8")
        assert infer_profile(tmp_path)["id"] == "quant_social_r"

    def test_estructura_vacia_cae_a_algun_perfil_por_defecto(self, tmp_path: Path):
        result = infer_profile(tmp_path)
        assert result["id"] in {"mixed_methods", "quant_social_r", "historical_discourse"}


class TestRunProfileChecks:
    def test_check_exists_ok_y_missing(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("x", encoding="utf-8")
        profile = {"checks": [
            {"id": "has_readme", "type": "exists", "path": "README.md"},
            {"id": "has_license", "type": "exists", "path": "LICENSE"},
        ]}
        results = run_profile_checks(tmp_path, profile)
        statuses = {r["id"]: r["status"] for r in results}
        assert statuses["has_readme"] == "ok"
        assert statuses["has_license"] == "missing"

    def test_check_min_matches(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("x", encoding="utf-8")
        (tmp_path / "b.md").write_text("x", encoding="utf-8")
        profile = {"checks": [{"id": "has_docs", "type": "min_matches", "glob": "*.md", "min": 2}]}
        results = run_profile_checks(tmp_path, profile)
        assert results[0]["status"] == "ok"

    def test_check_min_matches_insuficiente(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("x", encoding="utf-8")
        profile = {"checks": [{"id": "has_docs", "type": "min_matches", "glob": "*.md", "min": 3}]}
        results = run_profile_checks(tmp_path, profile)
        assert results[0]["status"] == "missing"

    def test_tipo_de_check_desconocido_es_missing(self, tmp_path: Path):
        profile = {"checks": [{"id": "raro", "type": "no-existe"}]}
        results = run_profile_checks(tmp_path, profile)
        assert results[0]["status"] == "missing"

    def test_label_reemplaza_guion_bajo_por_espacio(self, tmp_path: Path):
        profile = {"checks": [{"id": "has_readme_file", "type": "exists", "path": "README.md"}]}
        results = run_profile_checks(tmp_path, profile)
        assert results[0]["label"] == "has readme file"
