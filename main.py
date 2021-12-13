import argparse
from pathlib import Path

from backuper import Backuper
from config import Config, Commands, VariableRequired

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=Path, help="path to git repo with backuped config files")
    parser.add_argument("-d", "--dry_run", action="store_true", help="prints the functions that would be run without actually running it")
    parser.add_argument("-c", "--config", type=Path, help="path to configuration file")
    
    subparser = parser.add_subparsers(title="commands", required=True, dest="command")

    # Commands.BACKUP
    parser_backup = subparser.add_parser(Commands.BACKUP.value, help="copy changes files from system and add them to backup")
    parser_backup.add_argument("-r", "--remove", action="store_true", help="removes files from repo which are not present in the system")

    # Commands.LIST
    parser_list = subparser.add_parser(Commands.LIST.value, help="list all files under backup control")
    parser_list.add_argument("-a", "--show_all", action="store_true", help="show all files, including that dont present in system (works with -r only)")
    parser_list.add_argument("-r", "--repo_pathes", action="store_true", help="show files in git repo instead of system")

    # Commands.ADD
    parser_add = subparser.add_parser(Commands.ADD.value, help="add file for backup controll")
    parser_add.add_argument("file", type=Path, help="file to add to backup controll")

    # Command.Commit
    parser_commit = subparser.add_parser(Commands.COMMIT.value, help="commit changes to git repo without adding anything new")

    try:
        config = Config(vars(parser.parse_args()))
    except VariableRequired as ex:
        parser.print_usage()
        parser.exit(-1, f'main.py: error: the following arguments are required: {ex}\n')

    backuper = Backuper(path=config.git_path, dry_run=config.dry_run, delete_unpresent=config.remove)

    if config.command == Commands.BACKUP.value:
        backuper.backup()
    elif config.command == Commands.LIST.value:
        backuper.print_files(print_all=config.show_all, repo_pathes=config.repo_pathes)
    elif config.command == Commands.ADD.value:
        backuper.add(config.fname)
    elif config.command == Commands.COMMIT.value:
        backuper.commit()


if __name__ == "__main__":
    main()