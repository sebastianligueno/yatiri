"""
Cubre cli/repl.py: funciones puras de renderizado, el dispatcher de
comandos slash (handle_slash_command) y las rutas de exportación/cruce
con biblioteca. Las llamadas a red (answer_session_query, providers) se
mockean; el resto opera sobre tmp_path real.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

from research_operator.cli import repl as repl_mod
from research_operator.core.session import SessionState


@dataclass
class _FakeResult:
    title: str
    url: str = ""
    snippet: str = ""
    source_type: str = "academic"
    year: str | None = None


class TestRenderHelpers:
    def test_render_help_incluye_secciones_clave(self):
        text = repl_mod.render_help()
        assert "/search" in text
        assert "/brief" in text
        assert "/doctor" in text

    def test_render_context_sin_adjunto_ni_ficha(self):
        state = SessionState()
        text = repl_mod.render_context(state)
        assert "Contexto adjunto: ninguno" in text
        assert "Ficha de proyecto: vacía" in text

    def test_render_context_con_adjunto_y_ficha(self, tmp_path: Path):
        state = SessionState(attached_path=tmp_path)
        state.brief.phenomenon = "convivencia escolar"
        text = repl_mod.render_context(state)
        assert str(tmp_path) in text
        assert "Ficha de proyecto: cargada" in text

    def test_render_memories_marca_las_fijadas(self, monkeypatch):
        note = MagicMock(slug="proyecto-x", title="Proyecto X")
        monkeypatch.setattr(repl_mod, "list_memories", lambda: [note])
        state = SessionState(pinned_memories=["proyecto-x"])
        text = repl_mod.render_memories(state)
        assert "* proyecto-x: Proyecto X" in text


class TestRenderCost:
    def test_sin_uso_registrado(self):
        state = SessionState()
        assert repl_mod._render_cost(state) == "Sin uso registrado en esta sesión."

    def test_con_uso_muestra_costo(self):
        state = SessionState(last_provider="deepseek")
        state.record_usage("deepseek", 1000, 500)
        text = repl_mod._render_cost(state)
        assert "deepseek" in text
        assert "Costo estimado" in text


class TestReadInput:
    def test_sin_prompt_session_usa_input(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *a, **k: "  hola  ")
        assert repl_mod.read_input(None, SessionState()) == "hola"

    def test_con_prompt_session_usa_prompt(self):
        session = MagicMock()
        session.prompt.return_value = "  consulta  "
        assert repl_mod.read_input(session, SessionState()) == "consulta"


class TestHandleSlashCommandBasico:
    def test_exit_termina_sesion(self):
        assert repl_mod.handle_slash_command(SessionState(), "/exit") is True

    def test_quit_termina_sesion(self):
        assert repl_mod.handle_slash_command(SessionState(), "/quit") is True

    def test_clear_borra_historial(self):
        state = SessionState()
        state.add_exchange("a", "b")
        repl_mod.handle_slash_command(state, "/clear")
        assert state.messages == []

    def test_comando_no_reconocido_no_termina_sesion(self, capsys):
        assert repl_mod.handle_slash_command(SessionState(), "/inexistente") is False
        assert "no reconocido" in capsys.readouterr().out

    def test_mode_sin_argumento_muestra_modo_actual(self, capsys):
        state = SessionState(mode="qual")
        repl_mod.handle_slash_command(state, "/mode")
        assert "qual" in capsys.readouterr().out

    def test_mode_con_argumento_cambia_modo(self):
        state = SessionState()
        repl_mod.handle_slash_command(state, "/mode teach")
        assert state.mode == "teach"


class TestHandleSlashCommandConMocks:
    def test_provider_imprime_label(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "active_provider_label", lambda: "provider=deepseek")
        repl_mod.handle_slash_command(SessionState(), "/provider")
        assert "provider=deepseek" in capsys.readouterr().out

    def test_doctor_imprime_diagnostico(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "provider_diagnostics", lambda: "diagnóstico completo")
        repl_mod.handle_slash_command(SessionState(), "/doctor")
        assert "diagnóstico completo" in capsys.readouterr().out

    def test_mcp_imprime_reporte(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "render_mcp_report", lambda: "MCPs: ninguno")
        repl_mod.handle_slash_command(SessionState(), "/mcp")
        assert "MCPs: ninguno" in capsys.readouterr().out

    def test_search_con_query_cambia_modo_y_consulta(self, monkeypatch, capsys):
        mock_answer = MagicMock(return_value="síntesis académica")
        monkeypatch.setattr(repl_mod, "answer_session_query", mock_answer)
        monkeypatch.setattr(repl_mod, "get_config", lambda key: "")  # sin bib local
        state = SessionState()
        repl_mod.handle_slash_command(state, "/search convivencia escolar")
        assert state.mode == "search"
        mock_answer.assert_called_once_with(state, "convivencia escolar")
        assert "síntesis académica" in capsys.readouterr().out

    def test_search_sin_query_solo_cambia_modo(self, capsys):
        state = SessionState()
        repl_mod.handle_slash_command(state, "/search")
        assert state.mode == "search"
        assert "Modo activo: search" in capsys.readouterr().out

    def test_cost_imprime_render_cost(self, capsys):
        state = SessionState(last_provider="deepseek")
        state.record_usage("deepseek", 10, 10)
        repl_mod.handle_slash_command(state, "/cost")
        assert "Costo estimado" in capsys.readouterr().out

    def test_brief_delega_a_run_brief_form(self, monkeypatch):
        mock_brief = MagicMock()
        monkeypatch.setattr(repl_mod, "run_brief_form", mock_brief)
        state = SessionState()
        repl_mod.handle_slash_command(state, "/brief")
        mock_brief.assert_called_once_with(state)

    def test_review_delega_a_review_project_brief(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "review_project_brief", lambda state: "revisión crítica")
        repl_mod.handle_slash_command(SessionState(), "/review")
        assert "revisión crítica" in capsys.readouterr().out


class TestHandleSlashCommandAttach:
    def test_attach_sin_argumento_muestra_uso(self, capsys):
        repl_mod.handle_slash_command(SessionState(), "/attach")
        assert "Uso: /attach" in capsys.readouterr().out

    def test_attach_ruta_inexistente(self, tmp_path: Path, capsys):
        repl_mod.handle_slash_command(SessionState(), f"/attach {tmp_path / 'no-existe'}")
        assert "No existe" in capsys.readouterr().out

    def test_attach_ruta_existente_inicializa_research(self, tmp_path: Path, capsys):
        state = SessionState()
        repl_mod.handle_slash_command(state, f"/attach {tmp_path}")
        assert state.attached_path == tmp_path.resolve()
        assert (tmp_path / ".research" / "project.yaml").exists()

    def test_detach_limpia_adjunto(self, tmp_path: Path, capsys):
        state = SessionState(attached_path=tmp_path)
        repl_mod.handle_slash_command(state, "/detach")
        assert state.attached_path is None

    def test_context_imprime_render_context(self, capsys):
        repl_mod.handle_slash_command(SessionState(), "/context")
        assert "Modo:" in capsys.readouterr().out


class TestHandleSlashCommandMemory:
    def test_memory_show(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "list_memories", lambda: [])
        repl_mod.handle_slash_command(SessionState(), "/memory")
        assert "Memorias disponibles" in capsys.readouterr().out

    def test_memory_pin(self):
        state = SessionState()
        repl_mod.handle_slash_command(state, "/memory pin proyecto-x")
        assert "proyecto-x" in state.pinned_memories

    def test_memory_unpin(self):
        state = SessionState(pinned_memories=["proyecto-x"])
        repl_mod.handle_slash_command(state, "/memory unpin proyecto-x")
        assert "proyecto-x" not in state.pinned_memories

    def test_memory_uso_invalido(self, capsys):
        repl_mod.handle_slash_command(SessionState(), "/memory algo-raro")
        assert "Uso: /memory" in capsys.readouterr().out


class TestRunExport:
    def test_sin_resultados_muestra_aviso(self, capsys):
        state = SessionState()
        repl_mod._run_export(state, [])
        assert "No hay resultados" in capsys.readouterr().out

    def test_exporta_a_ruta_local_indicada(self, monkeypatch, tmp_path: Path, capsys):
        monkeypatch.setattr(repl_mod, "get_config", lambda key: "")
        state = SessionState(last_search_results=[_FakeResult(title="Un paper", snippet="resumen")])
        output_dir = tmp_path / "salida"
        repl_mod._run_export(state, [str(output_dir)])
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.md"))) == 1
        assert "fichas exportadas" in capsys.readouterr().out

    def test_exporta_al_vault_si_esta_configurado(self, monkeypatch, tmp_path: Path, capsys):
        vault = tmp_path / "vault"
        (vault / "Convivencia").mkdir(parents=True)
        monkeypatch.setattr(repl_mod, "get_config", lambda key: str(vault) if key == "YATIRI_VAULT_PATH" else "")
        state = SessionState(last_search_results=[_FakeResult(title="Convivencia escolar", snippet="bienestar")])
        repl_mod._run_export(state, [])
        out = capsys.readouterr().out
        assert "Exportando al vault" in out
        assert any((vault / "Convivencia").glob("*.md"))


class TestZoteroCommand:
    def test_sin_query_muestra_uso(self, capsys):
        repl_mod.handle_slash_command(SessionState(), "/zotero")
        assert "Uso: /zotero" in capsys.readouterr().out

    def test_sin_credenciales_pide_configurar(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "has_zotero_credentials", lambda: False)
        repl_mod.handle_slash_command(SessionState(), "/zotero convivencia escolar")
        out = capsys.readouterr().out
        assert "no está configurado" in out
        assert "yatiri setup" in out

    def test_sin_resultados(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "has_zotero_credentials", lambda: True)
        monkeypatch.setattr(repl_mod, "search_zotero", lambda query, max_results: [])
        repl_mod.handle_slash_command(SessionState(), "/zotero tema inexistente")
        assert "Sin resultados" in capsys.readouterr().out

    def test_con_resultados_los_lista(self, monkeypatch, capsys):
        result = MagicMock(
            title="Convivencia escolar en Chile", year="2021",
            authors="Pérez, A.", journal="Revista X", doi="10.1234/abc", url="",
        )
        monkeypatch.setattr(repl_mod, "has_zotero_credentials", lambda: True)
        monkeypatch.setattr(repl_mod, "search_zotero", lambda query, max_results: [result])
        repl_mod.handle_slash_command(SessionState(), "/zotero convivencia escolar")
        out = capsys.readouterr().out
        assert "Convivencia escolar en Chile" in out
        assert "Pérez, A." in out
        assert "https://doi.org/10.1234/abc" in out

    def test_titulo_con_corchetes_no_se_pierde(self, monkeypatch, capsys):
        result = MagicMock(
            title="Un [concepto] entre corchetes", year=None,
            authors=None, journal=None, doi=None, url="https://x.org",
        )
        monkeypatch.setattr(repl_mod, "has_zotero_credentials", lambda: True)
        monkeypatch.setattr(repl_mod, "search_zotero", lambda query, max_results: [result])
        repl_mod.handle_slash_command(SessionState(), "/zotero concepto")
        out = capsys.readouterr().out
        assert "[concepto]" in out


class TestShowLibraryMatches:
    def test_sin_bibtex_configurado_no_hace_nada(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "get_config", lambda key: "")
        state = SessionState(last_search_results=[_FakeResult(title="X")])
        repl_mod._show_library_matches(state, query="x")
        assert capsys.readouterr().out == ""

    def test_muestra_coincidencia_exacta_por_doi(self, monkeypatch, tmp_path: Path, capsys):
        bib_path = tmp_path / "library.bib"
        bib_path.write_text(
            "@article{palacios2020,\n"
            "  title = {Convivencia escolar},\n"
            "  doi = {10.1234/abc},\n"
            "  year = {2020},\n"
            "}\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(repl_mod, "get_config", lambda key: str(bib_path) if key == "YATIRI_BIBTEX_PATH" else "")
        state = SessionState(last_search_results=[_FakeResult(title="Convivencia escolar", url="https://doi.org/10.1234/abc")])
        repl_mod._show_library_matches(state, query="convivencia")
        out = capsys.readouterr().out
        assert "Coincidencia exacta" in out
        assert "palacios2020" in out


class TestRunBriefForm:
    def test_completa_ficha_minima(self, monkeypatch, capsys):
        respuestas = iter([
            "cualitativo",   # paradigma
            "Chile",         # contexto
            "convivencia escolar",  # fenómeno
            "",              # pregunta
            "",              # objetivo general
            "",              # objetivo 1 (termina de inmediato)
            "",              # marco teórico
            "",              # metodología
            "",              # muestra
            "",              # plan de análisis
        ])
        monkeypatch.setattr("builtins.input", lambda *a, **k: next(respuestas))
        state = SessionState()
        repl_mod.run_brief_form(state)
        assert state.brief.paradigm == "cualitativo"
        assert state.brief.phenomenon == "convivencia escolar"
        assert "Ficha guardada" in capsys.readouterr().out


class TestBuildPromptSession:
    def test_crea_directorio_de_historial_y_devuelve_sesion(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "home"
        monkeypatch.setattr(repl_mod.Path, "home", classmethod(lambda cls: fake_home))
        session = repl_mod.build_prompt_session()
        assert (fake_home / ".yatiri").is_dir()
        assert session is not None

    def test_oserror_al_crear_directorio_cae_a_tmp(self, monkeypatch):
        monkeypatch.setattr(repl_mod.Path, "home", classmethod(lambda cls: Path("/raiz-sin-permiso")))
        monkeypatch.setattr(
            repl_mod.Path, "mkdir",
            lambda self, *a, **k: (_ for _ in ()).throw(OSError("sin permiso")),
        )
        session = repl_mod.build_prompt_session()
        assert session is not None

    def test_sin_prompt_toolkit_devuelve_none(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "home"
        monkeypatch.setattr(repl_mod.Path, "home", classmethod(lambda cls: fake_home))
        monkeypatch.setattr(repl_mod, "PromptSession", None)
        assert repl_mod.build_prompt_session() is None


class TestStartRepl:
    def test_eof_inmediato_termina_sin_mostrar_costo(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(repl_mod, "read_input", MagicMock(side_effect=EOFError()))
        repl_mod.start_repl()
        out = capsys.readouterr().out
        assert "Sesión terminada." in out
        assert "Sin uso registrado" not in out
        assert "Costo estimado" not in out

    def test_keyboard_interrupt_con_uso_muestra_costo(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(
            repl_mod, "read_input", MagicMock(side_effect=["consulta", KeyboardInterrupt()])
        )

        def _fake_answer(state, query):
            state.record_usage("deepseek", 10, 5)
            return "respuesta"

        monkeypatch.setattr(repl_mod, "answer_session_query", _fake_answer)
        repl_mod.start_repl()
        out = capsys.readouterr().out
        assert "Sesión terminada." in out
        assert "Costo estimado" in out

    def test_input_vacio_continua_el_loop(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(repl_mod, "read_input", MagicMock(side_effect=["", EOFError()]))
        repl_mod.start_repl()
        assert "Sesión terminada." in capsys.readouterr().out

    def test_comando_slash_que_sale_termina_el_loop(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(repl_mod, "read_input", MagicMock(return_value="/exit"))
        repl_mod.start_repl()
        assert "Sesión terminada." not in capsys.readouterr().out

    def test_comando_slash_que_no_sale_continua_el_loop(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(
            repl_mod, "read_input", MagicMock(side_effect=["/provider", EOFError()])
        )
        monkeypatch.setattr(repl_mod, "active_provider_label", lambda: "provider=deepseek")
        repl_mod.start_repl()
        out = capsys.readouterr().out
        assert "provider=deepseek" in out
        assert "Sesión terminada." in out

    def test_consulta_normal_llama_answer_session_query(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(
            repl_mod, "read_input", MagicMock(side_effect=["convivencia escolar", EOFError()])
        )
        mock_answer = MagicMock(return_value="síntesis académica")
        monkeypatch.setattr(repl_mod, "answer_session_query", mock_answer)
        repl_mod.start_repl()
        out = capsys.readouterr().out
        mock_answer.assert_called_once()
        assert "síntesis académica" in out

    def test_modo_search_con_resultados_muestra_biblioteca(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(
            repl_mod, "read_input", MagicMock(side_effect=["convivencia escolar", EOFError()])
        )

        def _fake_answer(state, query):
            state.mode = "search"
            state.last_search_results = [_FakeResult(title="Un paper")]
            state.last_search_query = query
            return "síntesis"

        monkeypatch.setattr(repl_mod, "answer_session_query", _fake_answer)
        mock_library = MagicMock()
        monkeypatch.setattr(repl_mod, "_show_library_matches", mock_library)
        repl_mod.start_repl()
        mock_library.assert_called_once()

    def test_modo_search_sin_resultados_no_muestra_biblioteca(self, monkeypatch, capsys):
        monkeypatch.setattr(repl_mod, "build_prompt_session", lambda: None)
        monkeypatch.setattr(
            repl_mod, "read_input", MagicMock(side_effect=["convivencia escolar", EOFError()])
        )

        def _fake_answer(state, query):
            state.mode = "search"
            return "síntesis sin fuentes"

        monkeypatch.setattr(repl_mod, "answer_session_query", _fake_answer)
        mock_library = MagicMock()
        monkeypatch.setattr(repl_mod, "_show_library_matches", mock_library)
        repl_mod.start_repl()
        mock_library.assert_not_called()
