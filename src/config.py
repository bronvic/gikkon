from enum import Enum
from pathlib import Path
from typing import Any, Optional

import toml


class Commands(Enum):
    BACKUP = "backup"
    LIST = "list"
    ADD = "add"
    ROLLBACK = "rollback"


class ConfigLoader:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        return toml.load(self.config_path)


class AppConfig:
    def __init__(self, config: dict):
        self.config = config

    def get_variable(self, section: str, name: str, default: Optional[Any] = None) -> Any:
        try:
            return self.config[section][name]
        except KeyError:
            if default is not None:
                return default

            raise VariableRequired(section, name)


class Settings:
    def __init__(self, app_config: AppConfig, args: dict):
        self.app_config = app_config
        self.git_path = args.get("path") or Path(self.app_config.get_variable("General", "path"))
        if not self.git_path.exists():
            raise WrongGitPath(self.git_path)

        self.dry_run = args.get("dry_run") or self.app_config.get_variable("General", "dry_run", False)
        self.remove = args.get("remove") or self.app_config.get_variable("Backup", "remove", False)
        self.show_all = args.get("show_all") or self.app_config.get_variable("List", "show_all", False)
        self.ask_rollback = args.get("ask_rollback") or self.app_config.get_variable("Backup", "ask_rollback", True)
        self.repo_paths = args.get("repo_paths") or self.app_config.get_variable("List", "repo_paths", False)
        self.command = args.get("command")
        self.fname = args.get("file")


class VariableRequired(Exception):
    def __init__(self, section: str, name: str):
        super().__init__(f"Variable '{name}' in section '{section}' is required")


class WrongGitPath(Exception):
    def __init__(self, git_path: Path):
        super().__init__(f"Wrong Git path: {git_path}")


def load_settings(args) -> Settings:
    DEFAULT_PATH = Path().home().joinpath(Path(".config/gikkon/config.toml"))
    config_path = args.get("config") or DEFAULT_PATH
    config_loader = ConfigLoader(config_path)
    config_data = config_loader.load_config()
    app_config = AppConfig(config_data)
    return Settings(app_config, args)
