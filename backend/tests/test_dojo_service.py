"""
Tests for Dojo Service.
"""

from app.services.dojo_service import DojoService, DOJO_SCENARIOS


def test_get_scenarios_returns_list():
    """Should return all scenarios for a given language."""
    service = DojoService(api_key="fake")
    scenarios = service.get_scenarios(language="es")
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0
    assert all("id" in s and "name" in s for s in scenarios)


def test_get_scenarios_english():
    """Should return English scenario names."""
    service = DojoService(api_key="fake")
    scenarios = service.get_scenarios(language="en")
    names = [s["name"] for s in scenarios]
    assert "The Angry Parent" in names


def test_start_scenario_valid():
    """Should return scenario details for a valid ID."""
    service = DojoService(api_key="fake")
    result = service.start_scenario("angry_parent", language="es")
    assert "scenario_id" in result
    assert "opening_line" in result
    assert result["scenario_id"] == "angry_parent"


def test_start_scenario_invalid():
    """Should return error for invalid scenario ID."""
    service = DojoService(api_key="fake")
    result = service.start_scenario("nonexistent")
    assert "error" in result


def test_all_scenarios_have_bilingual_data():
    """Every scenario should have both 'en' and 'es' data."""
    for scenario_id, data in DOJO_SCENARIOS.items():
        assert "en" in data, f"{scenario_id} missing English data"
        assert "es" in data, f"{scenario_id} missing Spanish data"
        for lang in ["en", "es"]:
            assert "name" in data[lang], f"{scenario_id}/{lang} missing name"
            assert "system_prompt" in data[lang], f"{scenario_id}/{lang} missing system_prompt"
            assert "opening_line" in data[lang], f"{scenario_id}/{lang} missing opening_line"
