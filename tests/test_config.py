import unittest
from pathlib import Path
from unittest.mock import patch

from config import ConfigManager, VariableRequired, AppConfig, Settings, WrongGitPath


class TestConfigManager(unittest.TestCase):
    @patch("config.toml.load")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_config_success(self, exists_mock, toml_load_mock):
        config_path = Path("config.toml")
        config_loader = ConfigManager(config_path)

        config = config_loader.load_config()

        exists_mock.assert_called_once()
        toml_load_mock.assert_called_once_with(config_path)
        self.assertEqual(config, toml_load_mock.return_value)

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_config_not_found(self, exists_mock):
        config_path = Path("config.toml")
        config_loader = ConfigManager(config_path)

        with self.assertRaises(FileNotFoundError) as context:
            config_loader.load_config()

        exists_mock.assert_called_once()
        self.assertEqual(str(context.exception), f"Config file not found: {config_path}")


class TestAppConfig(unittest.TestCase):
    def setUp(self):
        self.config = {
            "section1": {
                "var1": "value1",
                "var2": "value2",
            },
            "section2": {
                "var1": "value3",
                "var3": "value4",
            },
        }
        self.app_config = AppConfig(self.config, "/path/to/repo")

    def test_get_variable_success(self):
        value = self.app_config.get_variable("section1", "var1")
        self.assertEqual(value, "value1")

    def test_get_variable_with_default(self):
        value = self.app_config.get_variable("section1", "nonexistent_var", default="default_value")
        self.assertEqual(value, "default_value")

    def test_get_variable_key_error(self):
        with self.assertRaises(VariableRequired) as context:
            self.app_config.get_variable("section1", "nonexistent_var")

        self.assertEqual(str(context.exception), "Variable 'nonexistent_var' in section 'section1' is required")


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.config = {
            "General": {
                "path": "/path/to/repo",
                "dry_run": True,
            },
            "Backup": {
                "remove": False,
                "ask_rollback": True,
            },
            "List": {
                "show_all": False,
                "repo_paths": True,
            },
        }
        self.app_config = AppConfig(self.config, "/path/to/repo")

    def test_settings_init_success(self):
        args = {
            "path": None,
            "dry_run": None,
            "remove": None,
            "show_all": None,
            "ask_rollback": None,
            "repo_paths": None,
            "command": "backup",
            "file": None,
        }
        mock_path = Path("/path/to/repo")
        with unittest.mock.patch("pathlib.Path.exists", return_value=True):
            settings = Settings(self.app_config, args)

        self.assertEqual(settings.git_path, mock_path)
        self.assertEqual(settings.dry_run, True)
        self.assertEqual(settings.remove, False)
        self.assertEqual(settings.show_all, False)
        self.assertEqual(settings.ask_rollback, True)
        self.assertEqual(settings.repo_paths, True)
        self.assertEqual(settings.command, "backup")
        self.assertIsNone(settings.fname)

    def test_settings_init_wrong_git_path(self):
        args = {
            "path": None,
            "dry_run": None,
            "remove": None,
            "show_all": None,
            "ask_rollback": None,
            "repo_paths": None,
            "command": "backup",
            "file": None,
        }
        mock_path = Path("/path/to/repo")
        with unittest.mock.patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(WrongGitPath) as context:
                Settings(self.app_config, args)

            self.assertEqual(str(context.exception), f"Wrong Git path: {mock_path}")


if __name__ == '__main__':
    unittest.main()
