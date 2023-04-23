import unittest
from unittest.mock import PropertyMock, call
from unittest.mock import patch

from backuper import *
from backuper import _copy, _select_files_to_revert, _copy_file, _copy_file_with_sudo, _delete_file, \
    _delete_file_with_sudo


@patch("backuper._copy")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.home", return_value=Path("/home/user"))
@patch("pathlib.Path.joinpath", return_value=Path("/home/user/test/file.txt"))
@patch("pathlib.Path.resolve", return_value=Path("/test/file.txt"))
class TestAdd(unittest.TestCase):

    def setUp(self) -> None:
        self.backuper = Backuper(Path("/backup"))

    @patch("builtins.print")
    @patch("pathlib.Path.parent", new_callable=PropertyMock)
    @patch("pathlib.Path.is_relative_to", return_value=False)
    def test_dry_run(self, path_is_relative_to_mock,
                     path_parent_mock, print_mock, path_resolve_mock, path_joinpath_mock, path_home_mock,
                     path_mkdir_mock, copy_mock):
        self.backuper.dry_run = True

        self.backuper.add(Path("test.txt"))

        path_resolve_mock.assert_called_once()
        path_joinpath_mock.assert_called_once_with(Path("test/file.txt"))
        path_is_relative_to_mock.assert_called_once_with(path_home_mock.return_value)
        path_home_mock.assert_called_once()
        path_parent_mock.assert_called_once()
        print_mock.assert_called_once_with(
            f"Dry run: Copying {path_resolve_mock.return_value} to {path_joinpath_mock.return_value}")
        path_mkdir_mock.assert_not_called()
        copy_mock.assert_not_called()

    @patch("builtins.print")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.is_relative_to", return_value=False)
    def test_not_dry_run(self, _path_is_relative_to_mock,
                         path_is_dir, print_mock, path_resolve_mock, path_joinpath_mock, _path_home_mock,
                         path_mkdir_mock, copy_mock):
        self.backuper.add(Path("test.txt"))

        path_mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
        copy_mock.assert_called_once_with(path_resolve_mock.return_value, path_joinpath_mock.return_value)

        path_is_dir.assert_not_called()
        print_mock.assert_not_called()

    @patch("pathlib.Path.is_relative_to", return_value=True)
    @patch("pathlib.Path.relative_to", return_value=Path("test/file.txt"))
    def test_home(self, mock_relative_to, _path_is_relative_to_mock,
                  _path_resolve_mock, path_joinpath_mock, path_home_mock,
                  path_mkdir_mock, copy_mock):
        self.backuper.add(Path("test.txt"))

        assert len(path_home_mock.call_args_list) == 2
        assert len(path_joinpath_mock.call_args_list) == 2
        assert path_joinpath_mock.call_args_list[0], call("test/file.txt")
        assert path_joinpath_mock.call_args_list[0], call(HOME, mock_relative_to.return_value)

        path_mkdir_mock.assert_called_once()
        copy_mock.assert_called_once()


class TestPrintFiles(unittest.TestCase):

    @patch("backuper.Path.is_file")
    @patch("backuper.Backuper._absolute_paths_from_inner")
    @patch("backuper.GitWrapper.files")
    @patch("builtins.print")
    def test_print_files_no_files(self, print_mock, git_files_mock, absolute_paths_mock, is_file_mock):
        git_files_mock.return_value = []
        backuper = Backuper(Path("/some/repo"))

        backuper.print_files(print_all=False, repo_paths=False)

        print_mock.assert_called_once_with("\nNo files under gikkon control")

    @patch("backuper.Path.is_file")
    @patch("backuper.Backuper._absolute_paths_from_inner")
    @patch("backuper.GitWrapper.files")
    @patch("builtins.print")
    def test_print_files_some_files(self, print_mock, git_files_mock, absolute_paths_mock, is_file_mock):
        git_files_mock.return_value = ["file1.txt", "file2.txt"]
        absolute_paths_mock.side_effect = [
            Paths(inner=Path("/some/repo/file1.txt"), outer=Path("/file1.txt")),
            Paths(inner=Path("/some/repo/file2.txt"), outer=Path("/file2.txt")),
        ]
        is_file_mock.return_value = True
        backuper = Backuper(Path("/some/repo"))

        backuper.print_files(print_all=False, repo_paths=False)

        print_calls = [
            unittest.mock.call("\nFiles under gikkon control:"),
            unittest.mock.call("/file1.txt"),
            unittest.mock.call("/file2.txt"),
        ]
        print_mock.assert_has_calls(print_calls, any_order=False)


class TestBackup(unittest.TestCase):
    @patch("backuper.Backuper._revert_files")
    @patch("backuper._select_files_to_revert")
    @patch("backuper.GitWrapper.get_changed_files")
    @patch("backuper.GitWrapper.discard_changes")
    @patch("backuper.UserInput.ask_bool", return_value=True)
    @patch("backuper.GitWrapper.commit_and_push")
    @patch("backuper.GitWrapper.show_changes")
    @patch("backuper.Backuper._copy_files")
    @patch("backuper.GitWrapper.ensure_push")
    def test_backup_commit(self, ensure_push_mock, copy_files_mock, show_changes_mock, commit_and_push_mock,
                           ask_bool_mock, discard_changes_mock, get_changed_files_mock,
                           select_files_to_revert_mock, revert_files_mock):
        backuper = Backuper(Path("/some/repo"))

        backuper.backup(ask_rollback=True, delete_not_present=False)

        ensure_push_mock.assert_called_once()
        copy_files_mock.assert_called_once_with(False)
        show_changes_mock.assert_called_once()
        ask_bool_mock.assert_has_calls([unittest.mock.call(unittest.mock.ANY, default=True)])
        commit_and_push_mock.assert_called_once()
        discard_changes_mock.assert_not_called()
        get_changed_files_mock.assert_not_called()
        select_files_to_revert_mock.assert_not_called()
        revert_files_mock.assert_not_called()

    @patch("backuper.Backuper._revert_files")
    @patch("backuper._select_files_to_revert")
    @patch("backuper.GitWrapper.get_changed_files")
    @patch("backuper.GitWrapper.discard_changes")
    @patch("backuper.UserInput.ask_bool", side_effect=[False, True])
    @patch("backuper.GitWrapper.commit_and_push")
    @patch("backuper.GitWrapper.show_changes")
    @patch("backuper.Backuper._copy_files")
    @patch("backuper.GitWrapper.ensure_push")
    def test_backup_abort_and_rollback(self, ensure_push_mock, copy_files_mock, show_changes_mock,
                                       commit_and_push_mock,
                                       ask_bool_mock, discard_changes_mock, get_changed_files_mock,
                                       select_files_to_revert_mock, revert_files_mock):
        backuper = Backuper(Path("/some/repo"))

        backuper.backup(ask_rollback=True, delete_not_present=False)

        ensure_push_mock.assert_called_once()
        copy_files_mock.assert_called_once_with(False)
        show_changes_mock.assert_called_once()
        ask_bool_mock.assert_has_calls([unittest.mock.call(unittest.mock.ANY, default=True),
                                        unittest.mock.call(unittest.mock.ANY, default=False)])
        commit_and_push_mock.assert_not_called()
        discard_changes_mock.assert_called_once()
        get_changed_files_mock.assert_called_once()
        select_files_to_revert_mock.assert_called_once_with(get_changed_files_mock.return_value)
        revert_files_mock.assert_called_once_with(select_files_to_revert_mock.return_value)

    @patch("backuper.GitWrapper.ensure_push")
    @patch("backuper.GitWrapper.show_changes", return_value=False)
    @patch("backuper.GitWrapper.commit_and_push")
    @patch("backuper.GitWrapper.discard_changes")
    @patch("backuper.Backuper._copy_files")
    @patch("backuper.Backuper._revert_files")
    @patch("backuper.UserInput.ask_bool")
    def test_backup_no_changes(self, ask_bool_mock, revert_files_mock, copy_files_mock, discard_changes_mock,
                               commit_and_push_mock, show_changes_mock, ensure_push_mock):
        backuper = Backuper(Path("test_repo"))
        backuper.backup()

        ensure_push_mock.assert_called_once()
        copy_files_mock.assert_called_once_with(False)
        show_changes_mock.assert_called_once()

        commit_and_push_mock.assert_not_called()
        discard_changes_mock.assert_not_called()
        revert_files_mock.assert_not_called()
        ask_bool_mock.assert_not_called()

    @patch("backuper.GitWrapper.ensure_push")
    @patch("backuper.GitWrapper.show_changes", return_value=True)
    @patch("backuper.GitWrapper.commit_and_push")
    @patch("backuper.GitWrapper.discard_changes")
    @patch("backuper.Backuper._copy_files")
    @patch("backuper.Backuper._revert_files")
    @patch("backuper.UserInput.ask_bool", side_effect=[False, False])
    def test_backup_decline_changes(self, ask_bool_mock, revert_files_mock, copy_files_mock, discard_changes_mock,
                                    commit_and_push_mock, show_changes_mock, ensure_push_mock):
        backuper = Backuper(Path("test_repo"))
        backuper.backup()

        ensure_push_mock.assert_called_once()
        copy_files_mock.assert_called_once_with(False)
        show_changes_mock.assert_called_once()

        commit_and_push_mock.assert_not_called()
        discard_changes_mock.assert_not_called()
        revert_files_mock.assert_not_called()
        ask_bool_mock.assert_called()

    @patch("backuper.GitWrapper.ensure_push")
    @patch("backuper.GitWrapper.show_changes", return_value=True)
    @patch("backuper.GitWrapper.commit_and_push")
    @patch("backuper.GitWrapper.discard_changes")
    @patch("backuper.GitWrapper.get_changed_files", return_value=[("M", "file1.txt"), ("A", "file2.txt")])
    @patch("backuper.Backuper._copy_files")
    @patch("backuper.Backuper._revert_files")
    @patch("backuper.UserInput.ask_bool", side_effect=[False, True])
    @patch("backuper._select_files_to_revert", return_value=[("M", "file1.txt"), ("A", "file2.txt")])
    def test_backup_decline_changes_and_rollback(self, select_files_to_revert_mock, ask_bool_mock, revert_files_mock,
                                                 copy_files_mock, get_changed_files_mock, discard_changes_mock,
                                                 commit_and_push_mock, show_changes_mock, ensure_push_mock):
        backuper = Backuper(Path("test_repo"))
        backuper.backup()

        ensure_push_mock.assert_called_once()
        copy_files_mock.assert_called_once_with(False)
        show_changes_mock.assert_called_once()

        commit_and_push_mock.assert_not_called()
        discard_changes_mock.assert_called_once()
        get_changed_files_mock.assert_called_once()
        select_files_to_revert_mock.assert_called_once_with(get_changed_files_mock.return_value)
        revert_files_mock.assert_called_once_with(select_files_to_revert_mock.return_value)
        ask_bool_mock.assert_called()


class TestSelectFilesToRevert(unittest.TestCase):
    changed_files = [
        ("M", Path("file1.txt")),
        ("A", Path("file2.txt")),
        ("D", Path("file3.txt")),
    ]

    @patch("builtins.input", return_value="")
    @patch("builtins.print")
    def test_select_all_files(self, print_mock, input_mock):
        result = _select_files_to_revert(self.changed_files)
        self.assertEqual(result, self.changed_files)

    @patch("builtins.input", return_value="q")
    @patch("builtins.print")
    def test_quit_selection(self, print_mock, input_mock):
        result = _select_files_to_revert(self.changed_files)
        self.assertEqual(result, [])

    @patch("builtins.input", return_value="1 3")
    @patch("builtins.print")
    def test_select_specific_files(self, print_mock, input_mock):
        expected_result = [
            self.changed_files[0],
            self.changed_files[2],
        ]
        result = _select_files_to_revert(self.changed_files)
        self.assertEqual(result, expected_result)


class TestCopy(unittest.TestCase):
    @patch("shutil.copy")
    def test_copy(self, shutil_copy_mock):
        from_path = Path("from.txt")
        to_path = Path("to.txt")

        _copy(from_path, to_path)

        shutil_copy_mock.assert_called_once_with(from_path, to_path)


class TestCopyFile(unittest.TestCase):
    @patch("backuper.print")
    @patch("backuper._copy")
    @patch("backuper._has_write_access", return_value=True)
    def test_copy_file_with_write_access(self, has_write_access_mock, copy_mock, print_mock):
        src = Path("src.txt")
        dst = Path("dst.txt")

        _copy_file(src, dst)

        print_mock.assert_called_once_with(f"copying from {src} to {dst}")
        has_write_access_mock.assert_called_once_with(dst)
        copy_mock.assert_called_once_with(src, dst)

    @patch("backuper.print")
    @patch("backuper._copy_file_with_sudo")
    @patch("backuper._has_write_access", return_value=False)
    def test_copy_file_without_write_access(self, has_write_access_mock, copy_file_with_sudo_mock, print_mock):
        src = Path("src.txt")
        dst = Path("dst.txt")

        _copy_file(src, dst)

        print_mock.assert_called_once_with(f"copying from {src} to {dst}")
        has_write_access_mock.assert_called_once_with(dst)
        copy_file_with_sudo_mock.assert_called_once_with(src, dst)


class TestCopyFileWithSudo(unittest.TestCase):
    @patch("backuper.subprocess.check_call")
    @patch("backuper.print")
    def test_copy_file_with_sudo_success(self, print_mock, check_call_mock):
        src = "src.txt"
        dst = "dst.txt"

        _copy_file_with_sudo(src, dst)

        check_call_mock.assert_called_once_with(["sudo", "cp", src, dst])
        print_mock.assert_called_once_with(f"copying from {src} to {dst}")

    @patch("backuper.sys.exit")
    @patch("backuper.print")
    @patch("backuper.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "sudo cp"))
    def test_copy_file_with_sudo_failure(self, check_call_mock, print_mock, sys_exit_mock):
        src = "src.txt"
        dst = "dst.txt"

        _copy_file_with_sudo(src, dst)

        check_call_mock.assert_called_once_with(["sudo", "cp", src, dst])
        print_mock.assert_has_calls([call(f"copying from {src} to {dst}"),
                                     call(
                                         "Error: Failed to copy file with sudo: Command 'sudo cp' returned non-zero exit status 1.")])
        sys_exit_mock.assert_called_once_with(1)


class TestDeleteFile(unittest.TestCase):
    @patch("backuper.print")
    @patch("backuper.os.remove")
    @patch("backuper._has_write_access", return_value=True)
    def test_delete_file_with_write_access(self, has_write_access_mock, remove_mock, print_mock):
        file_path = Path("test.txt")

        _delete_file(file_path)

        print_mock.assert_called_once_with(f"removing {file_path}")
        remove_mock.assert_called_once_with(file_path)
        has_write_access_mock.assert_called_once_with(file_path)

    @patch("backuper.print")
    @patch("backuper._delete_file_with_sudo")
    @patch("backuper._has_write_access", return_value=False)
    def test_delete_file_without_write_access(self, has_write_access_mock, delete_file_with_sudo_mock, print_mock):
        file_path = Path("test.txt")

        _delete_file(file_path)

        print_mock.assert_called_once_with(f"removing {file_path}")
        delete_file_with_sudo_mock.assert_called_once_with(file_path)
        has_write_access_mock.assert_called_once_with(file_path)


class TestDeleteFileWithSudo(unittest.TestCase):
    @patch("backuper.subprocess.check_call")
    def test_delete_file_with_sudo_success(self, check_call_mock):
        file_path = "test.txt"

        _delete_file_with_sudo(file_path)

        check_call_mock.assert_called_once_with(["sudo", "rm", file_path])

    @patch("backuper.sys.exit")
    @patch("backuper.print")
    @patch("backuper.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "rm"))
    def test_delete_file_with_sudo_failure(self, check_call_mock, print_mock, sys_exit_mock):
        file_path = "test.txt"

        _delete_file_with_sudo(file_path)

        check_call_mock.assert_called_once_with(["sudo", "rm", file_path])
        print_mock.assert_called_once_with(
            "Error: Failed to delete file with sudo: Command 'rm' returned non-zero exit status 1.")
        sys_exit_mock.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
