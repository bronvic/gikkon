from pathlib import Path
from git import Repo

from wrappers import maybe_dry, DryRunnable

COMMIT_MESSAGE = "something changed"


class Git(DryRunnable):
    def __init__(self, path: Path, dry_run: bool = False) -> None:
        self.path: Path = path
        self.repo: Repo = Repo(str(self.path))

        super().__init__(dry_run)

    @maybe_dry
    def commit_and_push(self) -> None:
        # add custom commit message
        message = input("Write custom commit message (or enter to skip): ")
        message = COMMIT_MESSAGE if message == "" else message
        
        # add files to commit
        self.repo.git.add(all=True)

        # create commit
        self.repo.index.commit(message)

        # push
        self.repo.remote().push()

    def push_to_repo(self) -> None:
        if self.repo.is_dirty(untracked_files = True):
            untracked_files = self.repo.untracked_files
            diffs = self.repo.index.diff(None)

            if untracked_files:
                print("\nAdding new files:")
                for f in untracked_files:
                    print(f'+ {f}')

            deleted = diffs.iter_change_type("D")
            if list(deleted):
                print("\nDeleting files")
                for obj in diffs.iter_change_type("D"):
                    print(f'- {obj.b_path}')

            changed =  [d for d in diffs if d.change_type != "D"]
            if len(changed):
                print("\nChanging files")
                for diff in changed:
                    print(self.repo.git.diff(diff.b_path))

            accept = input("\nAccept changes? [Y/n]: ")
            if accept not in ("", "Y", "y", "yes"):
                print("Abort adding git files")
                return

            self.commit_and_push()