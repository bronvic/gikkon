from enum import Enum
from pathlib import Path
from typing import Any, Optional

import toml


class Commands(Enum):
    BACKUP = "backup"
    LIST = "list"
    ADD = "add"
    COMMIT = "commit"


class Config:
    DEFAILT_PATH = Path().home().joinpath(Path(".config/gikkon/config.toml"))

    # Common
    git_path: Path
    config_path: Path
    command: str
    dry_run: bool

    # Backup
    remove: bool

    # List
    show_all: bool
    repo_pathes: bool

    # Add
    fname: Path

    def __init__(self, args):
        config_path = args.get("config") or self.DEFAILT_PATH
        self.config = toml.load(config_path)

        self.git_path = args.get("path") or Path(self.get_variable("General", "path"))
        if not self.git_path.exists():
            raise WrongGitPath(self.git_path)

        self.dry_run = args.get("dry_run") or self.get_variable(
            "General", "dry_run", False
        )
        self.remove = args.get("remove") or self.get_variable("Backup", "remove", False)
        self.show_all = args.get("show_all") or self.get_variable(
            "List", "show_all", False
        )
        self.repo_pathes = args.get("repo_pathes") or self.get_variable(
            "List", "repo_pathes", False
        )
        self.command = args.get("command")
        self.fname = args.get("file")

    def get_variable(
        self, section: str, name: str, default: Optional[Any] = None
    ) -> Any:
        try:
            return self.config[section][name]
        except KeyError:
            if default is not None:
                return default

            raise VariableRequired(name)


class VariableRequired(Exception):
    pass


class WrongGitPath(Exception):
    pass
