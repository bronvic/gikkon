import unittest
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from config import Config, VariableRequired, WrongGitPath

kwargs = {
    "config": Path("config path"),
    "path": Path("git path"),
    "dry_run": True,
    "remove": True,
    "show_all": True,
    "repo_pathes": True,
    "command": "a command",
    "file": Path("file name"),
}


class TestConfig(TestCase):
    pass


@patch("config.toml.load", return_value="config")
@patch("config.Config.get_variable", side_effect=["mypath"] + [False] * 4)
class TestInit(TestConfig):
    @patch("config.Path.exists", return_value=True)
    def test_defaults(self, mock_git_path, mock_get, mock_load):
        config = Config({})

        mock_load.assert_called_once_with(config.DEFAILT_PATH)
        mock_git_path.assert_called_once()

        self.assertEqual(config.config, "config")
        self.assertEqual(config.git_path, Path("mypath"))
        self.assertFalse(config.dry_run)
        self.assertFalse(config.remove)
        self.assertFalse(config.show_all)
        self.assertFalse(config.repo_pathes)
        self.assertIsNone(config.command)
        self.assertIsNone(config.fname)

    @patch("config.Path.exists", return_value=True)
    def test_from_args(self, mock_git_path, mock_get, mock_load):
        config = Config(kwargs)

        mock_load.assert_called_once_with(kwargs["config"])

        self.assertEqual(config.git_path, kwargs["path"])
        self.assertEqual(config.dry_run, kwargs["dry_run"])
        self.assertEqual(config.remove, kwargs["remove"])
        self.assertEqual(config.show_all, kwargs["show_all"])
        self.assertEqual(config.repo_pathes, kwargs["repo_pathes"])
        self.assertEqual(config.command, kwargs["command"])
        self.assertEqual(config.fname, kwargs["file"])

    @patch("config.Path.exists", return_value=False)
    def test_wrong_git_path(self, mock_git_path, mock_get, mock_load):
        with self.assertRaises(WrongGitPath):
            config = Config({})


class TestGetVariable(TestConfig):
    @patch("config.Path.exists", return_value=True)
    @patch("config.toml.load")
    def setUp(self, mock_exists, mock_load):
        self.config = Config(kwargs)
        self.config.config = {"First": {"Second": "Third"}}

    def test_ok(self):
        self.assertEqual(self.config.get_variable("First", "Second"), "Third")
        self.assertEqual(
            self.config.get_variable("First", "Kekond", "Fourth"), "Fourth"
        )

    def test_error(self):
        with self.assertRaises(VariableRequired):
            self.config.get_variable("First", "Kekond")
