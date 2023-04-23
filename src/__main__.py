import argparse
from pathlib import Path

from backuper import Backuper
from config import Commands, Settings, VariableRequired, WrongGitPath, load_settings


def main() -> None:
    """main configure argument parsers and run appropriate function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=Path, help="path to git repo with backuped config files")
    parser.add_argument(
        "-d",
        "--dry_run",
        action="store_true",
        help="prints what would be done without actually doing it",
    )
    parser.add_argument("-c", "--config", type=Path, help="path to configuration file")

    subparser = parser.add_subparsers(title="commands", required=True, dest="command")

    # Commands.BACKUP
    parser_backup = subparser.add_parser(
        Commands.BACKUP.value,
        help="copy changes files from system and add them to backup",
    )
    parser_backup.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="removes files from repo which are not present in the system",
    )
    parser_backup.add_argument(
        "--ask_rollback",
        action="store_true",
        help="ask about rollback changed files on the system",
    )

    # Commands.LIST
    parser_list = subparser.add_parser(Commands.LIST.value, help="list all files under backup control")
    parser_list.add_argument(
        "-a",
        "--show_all",
        action="store_true",
        help="show all files, including that dont present in system (works with -r only)",
    )
    parser_list.add_argument(
        "-r",
        "--repo_paths",
        action="store_true",
        help="show files in git repo instead of system",
    )

    # Commands.ADD
    parser_add = subparser.add_parser(Commands.ADD.value, help="add file for backup control")
    parser_add.add_argument("file", type=Path, help="file to add to backup control")

    # Commands.ROLLBACK
    subparser.add_parser(Commands.ROLLBACK.value, help="rollback changes on the system")

    try:
        args = vars(parser.parse_args())
        config = load_settings(args)
    except VariableRequired as ex:
        parser.print_usage()
        parser.exit(-1, f"error: the following arguments are required: {ex}\n")
    except WrongGitPath as ex:
        parser.exit(
            -2,
            f"\
            Wrong path to git repo: '{ex}'\n\
            Change path variable in config file (~/.config/gikkon/config.toml by default)\n\
            Or use '--path' option\n",
        )

    backuper = Backuper(path=config.git_path, dry_run=config.dry_run)

    if config.command == Commands.BACKUP.value:
        backuper.backup(ask_rollback=config.ask_rollback, delete_not_present=config.remove)
    elif config.command == Commands.LIST.value:
        backuper.print_files(print_all=config.show_all, repo_paths=config.repo_paths)
    elif config.command == Commands.ADD.value:
        backuper.add(config.fname)


if __name__ == "__main__":
    main()
