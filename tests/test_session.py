from __future__ import annotations

from research_operator.core.session import ProjectBrief, SessionState


class TestProjectBrief:
    def test_vacia_por_defecto(self):
        assert ProjectBrief().is_empty() is True

    def test_no_vacia_con_fenomeno(self):
        assert ProjectBrief(phenomenon="convivencia escolar").is_empty() is False

    def test_to_text_incluye_solo_campos_presentes(self):
        brief = ProjectBrief(phenomenon="X", methodology="")
        text = brief.to_text()
        assert "Fenómeno/problema: X" in text
        assert "Metodología" not in text

    def test_to_text_enumera_objetivos_especificos(self):
        brief = ProjectBrief(specific_objectives=["Uno", "Dos"])
        text = brief.to_text()
        assert "1. Uno" in text
        assert "2. Dos" in text


class TestSessionState:
    def test_record_usage_acumula_tokens(self):
        state = SessionState()
        state.record_usage("deepseek", 100, 50)
        state.record_usage("deepseek", 20, 10)
        assert state.total_input_tokens == 120
        assert state.total_output_tokens == 60
        assert state.last_provider == "deepseek"

    def test_record_usage_sin_provider_no_sobreescribe(self):
        state = SessionState(last_provider="deepseek")
        state.record_usage("", 10, 10)
        assert state.last_provider == "deepseek"

    def test_pin_memory_no_duplica(self):
        state = SessionState()
        state.pin_memory("nota-a")
        state.pin_memory("nota-a")
        assert state.pinned_memories == ["nota-a"]

    def test_unpin_memory_ausente_no_falla(self):
        state = SessionState()
        state.unpin_memory("no-existe")
        assert state.pinned_memories == []

    def test_add_exchange_trunca_historial(self):
        state = SessionState()
        for i in range(15):
            state.add_exchange(f"pregunta {i}", f"respuesta {i}")
        assert len(state.messages) == 20
        assert state.messages[0]["content"] == "pregunta 5"

    def test_clear_history(self):
        state = SessionState()
        state.add_exchange("a", "b")
        state.clear_history()
        assert state.messages == []
