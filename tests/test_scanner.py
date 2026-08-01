"""
Complementa test_cli_scan.py (que cubre scan_project de punta a punta).
Aquí: discover_sources con exclusiones, detect_pipeline_steps en sus dos
ramas (R / Python), build_report, infer_paths y helpers de inferencia.
"""
from __future__ import annotations

from pathlib import Path

from research_operator.core.scanner import (
    build_report,
    detect_outputs_from_name,
    detect_pipeline_steps,
    discover_sources,
    existing_or_default,
    infer_paths,
    infer_source_role,
    infer_source_type,
    sanitize_id,
)

_CFG = {
    "discovery": {
        "include_globs": ["**/*.md"],
        "exclude_globs": [".git/**", "__pycache__/**"],
    }
}


class TestDiscoverSources:
    def test_encuentra_archivos_incluidos(self, tmp_path: Path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "protocolo.md").write_text("x", encoding="utf-8")
        records = discover_sources(tmp_path, _CFG)
        assert len(records) == 1
        assert records[0]["path"] == "docs/protocolo.md"
        assert records[0]["role"] == "project_doc"

    def test_excluye_segun_exclude_globs(self, tmp_path: Path):
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.md").write_text("x", encoding="utf-8")
        (tmp_path / "real.md").write_text("x", encoding="utf-8")
        records = discover_sources(tmp_path, _CFG)
        paths = [r["path"] for r in records]
        assert "real.md" in paths
        assert not any("__pycache__" in p for p in paths)

    def test_sin_include_globs_no_encuentra_nada(self, tmp_path: Path):
        (tmp_path / "x.md").write_text("x", encoding="utf-8")
        assert discover_sources(tmp_path, {}) == []

    def test_ids_correlativos(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("x", encoding="utf-8")
        (tmp_path / "b.md").write_text("x", encoding="utf-8")
        records = discover_sources(tmp_path, _CFG)
        ids = sorted(r["id"] for r in records)
        assert ids == ["src_0001", "src_0002"]


class TestInferSourceType:
    def test_mapea_extensiones_conocidas(self, tmp_path: Path):
        assert infer_source_type(tmp_path / "x.md") == "markdown"
        assert infer_source_type(tmp_path / "x.qmd") == "qmd_manuscript"
        assert infer_source_type(tmp_path / "x.R") == "r_script"
        assert infer_source_type(tmp_path / "x.py") == "python_script"
        assert infer_source_type(tmp_path / "x.csv") == "dataset_csv"

    def test_extension_desconocida_es_file(self, tmp_path: Path):
        assert infer_source_type(tmp_path / "x.zzz") == "file"


class TestInferSourceRole:
    def test_paper_es_manuscript(self):
        assert infer_source_role("paper/borrador.qmd") == "manuscript"

    def test_scripts_es_pipeline(self):
        assert infer_source_role("analysis/scripts/limpieza.R") == "pipeline"

    def test_docs_o_readme_es_project_doc(self):
        assert infer_source_role("docs/protocolo.md") == "project_doc"
        assert infer_source_role("README.md") == "project_doc"

    def test_data_raw_es_raw_data(self):
        assert infer_source_role("data/raw/encuesta.csv") == "raw_data"

    def test_data_derived_es_derived_data(self):
        assert infer_source_role("data/derived/limpio.csv") == "derived_data"

    def test_default_es_source(self):
        assert infer_source_role("otro/archivo.txt") == "source"


class TestDetectPipelineSteps:
    def test_detecta_scripts_r(self, tmp_path: Path):
        scripts_dir = tmp_path / "analysis" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "01_derived.R").write_text("# script", encoding="utf-8")
        steps = detect_pipeline_steps(tmp_path)
        assert len(steps) == 1
        assert steps[0]["run"] == "Rscript analysis/scripts/01_derived.R"
        assert steps[0]["outputs"] == ["data-derived"]

    def test_detecta_cli_python_si_no_hay_scripts_r(self, tmp_path: Path):
        src_dir = tmp_path / "src" / "paquete"
        src_dir.mkdir(parents=True)
        (src_dir / "cli.py").write_text("# cli", encoding="utf-8")
        steps = detect_pipeline_steps(tmp_path)
        assert len(steps) == 1
        assert "python3" in steps[0]["run"]

    def test_sin_scripts_ni_src_devuelve_vacio(self, tmp_path: Path):
        assert detect_pipeline_steps(tmp_path) == []


class TestDetectOutputsFromName:
    def test_derived(self):
        assert detect_outputs_from_name("01_derived_data") == ["data-derived"]

    def test_parquet(self):
        assert detect_outputs_from_name("build_parquet") == ["data/parquet"]

    def test_render(self):
        assert detect_outputs_from_name("render_manuscript") == ["paper"]

    def test_sin_coincidencia(self):
        assert detect_outputs_from_name("limpieza") == []


class TestBuildReport:
    def test_incluye_secciones_clave(self, tmp_path: Path):
        profile = {"id": "mixed_methods"}
        sources = [{"path": "docs/x.md", "type": "markdown"}]
        steps = [{"id": "paso1", "run": "Rscript x.R"}]
        checks = [{"status": "ok", "label": "tiene readme"}]
        report = build_report(tmp_path, profile, sources, steps, checks)
        assert "# Project Scan" in report
        assert "docs/x.md" in report
        assert "paso1" in report
        assert "[ok] tiene readme" in report

    def test_sin_pipeline_indica_que_no_hay(self, tmp_path: Path):
        report = build_report(tmp_path, {"id": "x"}, [], [], [])
        assert "No se detectaron scripts canonicos." in report


class TestInferPaths:
    def test_usa_carpetas_existentes(self, tmp_path: Path):
        (tmp_path / "data-raw").mkdir()
        paths = infer_paths(tmp_path, {})
        assert paths["raw_data"] == ["data-raw"]

    def test_usa_default_si_no_existe_ninguna(self, tmp_path: Path):
        paths = infer_paths(tmp_path, {})
        assert paths["raw_data"] == ["data/raw"]
        assert paths["outputs"] == ["output"]


class TestExistingOrDefault:
    def test_devuelve_candidatos_existentes(self, tmp_path: Path):
        (tmp_path / "scripts").mkdir()
        assert existing_or_default(tmp_path, ["analysis/scripts", "scripts"], ["default"]) == ["scripts"]

    def test_devuelve_default_si_ninguno_existe(self, tmp_path: Path):
        assert existing_or_default(tmp_path, ["no-existe"], ["default"]) == ["default"]


class TestSanitizeId:
    def test_normaliza_caracteres_no_alfanumericos(self):
        assert sanitize_id("Mi Proyecto 2026!") == "mi_proyecto_2026"
