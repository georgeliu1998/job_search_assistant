"""
Unit tests for user preference persistence.
"""

from src.core.preferences import load_preferences, save_preferences
from src.models.user import CriterionConfig, JobPreferences


class TestPreferencesPersistence:
    def test_load_missing_file_returns_defaults(self, tmp_path):
        prefs = load_preferences(tmp_path / "does_not_exist.yaml")
        assert prefs == JobPreferences()

    def test_save_then_load_round_trip(self, tmp_path):
        path = tmp_path / "prefs.yaml"
        original = JobPreferences(
            min_salary=140000,
            acceptable_locations=["hybrid"],
            company_blacklist=["Acme"],
            target_role_description="ML Engineer",
        )
        original.salary_config = CriterionConfig(mode="optional", none_policy="pass")

        save_preferences(original, path)
        loaded = load_preferences(path)

        assert loaded == original

    def test_saved_yaml_uses_plain_strings(self, tmp_path):
        path = tmp_path / "prefs.yaml"
        save_preferences(JobPreferences(), path)
        text = path.read_text()
        # StrEnum values should be written as plain strings, not enum reprs.
        assert "mode: required" in text
        assert "CriterionMode" not in text

    def test_malformed_yaml_falls_back_to_defaults(self, tmp_path):
        path = tmp_path / "prefs.yaml"
        path.write_text("min_salary: [unbalanced\n")
        assert load_preferences(path) == JobPreferences()

    def test_invalid_schema_falls_back_to_defaults(self, tmp_path):
        path = tmp_path / "prefs.yaml"
        path.write_text("acceptable_locations:\n  - work-from-moon\n")
        assert load_preferences(path) == JobPreferences()

    def test_empty_file_returns_defaults(self, tmp_path):
        path = tmp_path / "prefs.yaml"
        path.write_text("")
        assert load_preferences(path) == JobPreferences()

    def test_partial_criterion_config_uses_pass_none_policy(self, tmp_path):
        """Partial YAML with only `mode` set picks up the product-wide PASS default.

        Regression guard: keeps CriterionConfig's class-level none_policy default
        aligned with what every JobPreferences factory uses.
        """
        path = tmp_path / "prefs.yaml"
        path.write_text("salary_config:\n  mode: required\n")
        prefs = load_preferences(path)
        assert prefs.salary_config.mode == "required"
        assert prefs.salary_config.none_policy == "pass"
