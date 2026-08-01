"""
Cubre cli/app.py: parseo de argumentos y el dispatch de main() hacia cada
subcomando. Los run_* y start_repl se mockean (ya tienen sus propios tests
en test_cli_init.py / test_cli_scan.py / etc. o dependen de red/consola).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from research_operator.cli.app import build_parser, main


class TestBuildParser:
    def test_chat_requiere_pregunta(self):
        parser = build_parser()
        args = parser.parse_args(["chat", "una consulta"])
        assert args.command == "chat"
        assert args.question == "una consulta"
        assert args.mode == "general"
        assert args.attach is None

    def test_chat_con_mode_y_attach(self):
        parser = build_parser()
        args = parser.parse_args(["chat", "consulta", "--mode", "search", "--attach", "/tmp/x"])
        assert args.mode == "search"
        assert args.attach == "/tmp/x"

    def test_init_path_por_defecto_es_punto(self):
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.path == "."

    def test_comando_desconocido_falla(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["no-existe"])

    def test_sin_comando_falla_por_ser_requerido(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestMainDispatch:
    def test_sin_argumentos_abre_repl(self, monkeypatch):
        mock_repl = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.start_repl", mock_repl)
        monkeypatch.setattr("sys.argv", ["yatiri"])
        main()
        mock_repl.assert_called_once()

    def test_comando_setup_llama_run_setup(self, monkeypatch):
        mock_setup = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_setup", mock_setup)
        monkeypatch.setattr("sys.argv", ["yatiri", "setup"])
        main()
        mock_setup.assert_called_once()

    def test_comando_init_resuelve_ruta_absoluta(self, monkeypatch, tmp_path: Path):
        mock_init = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_init", mock_init)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["yatiri", "init", "subcarpeta"])
        main()
        called_root = mock_init.call_args[0][0]
        assert called_root == (tmp_path / "subcarpeta").resolve()

    def test_comando_scan_llama_run_scan(self, monkeypatch, tmp_path: Path):
        mock_scan = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_scan", mock_scan)
        monkeypatch.setattr("sys.argv", ["yatiri", "scan", str(tmp_path)])
        main()
        mock_scan.assert_called_once_with(tmp_path)

    def test_comando_status_llama_run_status(self, monkeypatch, tmp_path: Path):
        mock_status = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_status", mock_status)
        monkeypatch.setattr("sys.argv", ["yatiri", "status", str(tmp_path)])
        main()
        mock_status.assert_called_once_with(tmp_path)

    def test_comando_ask_llama_run_ask_con_pregunta(self, monkeypatch, tmp_path: Path):
        mock_ask = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_ask", mock_ask)
        monkeypatch.setattr("sys.argv", ["yatiri", "ask", "una pregunta", str(tmp_path)])
        main()
        mock_ask.assert_called_once_with(tmp_path, "una pregunta")

    def test_comando_run_llama_run_step_con_step_id(self, monkeypatch, tmp_path: Path):
        mock_run_step = MagicMock()
        monkeypatch.setattr("research_operator.cli.app.run_step", mock_run_step)
        monkeypatch.setattr("sys.argv", ["yatiri", "run", "paso1", str(tmp_path)])
        main()
        mock_run_step.assert_called_once_with(tmp_path, "paso1")

    def test_comando_chat_sin_attach_llama_answer_session_query(self, monkeypatch, capsys):
        mock_answer = MagicMock(return_value="respuesta del modelo")
        monkeypatch.setattr("research_operator.core.advisor.answer_session_query", mock_answer)
        monkeypatch.setattr("sys.argv", ["yatiri", "chat", "consulta cualquiera"])
        main()
        out = capsys.readouterr().out
        assert "respuesta del modelo" in out
        mock_answer.assert_called_once()
        state_arg = mock_answer.call_args[0][0]
        assert state_arg.mode == "general"
        assert state_arg.attached_path is None

    def test_comando_chat_con_attach_existente_no_reescanea(self, monkeypatch, tmp_path: Path, capsys):
        from research_operator.core.project import ensure_research_layout, init_project_config

        ensure_research_layout(tmp_path)
        init_project_config(tmp_path)
        mock_answer = MagicMock(return_value="ok")
        mock_scan = MagicMock()
        monkeypatch.setattr("research_operator.core.advisor.answer_session_query", mock_answer)
        monkeypatch.setattr("research_operator.core.scanner.scan_project", mock_scan)
        monkeypatch.setattr("sys.argv", ["yatiri", "chat", "consulta", "--attach", str(tmp_path)])
        main()
        mock_scan.assert_not_called()
        state_arg = mock_answer.call_args[0][0]
        assert state_arg.attached_path == tmp_path.resolve()
