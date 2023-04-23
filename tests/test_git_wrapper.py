import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import user_texts
from git_wrapper import GitWrapper, DEFAULT_COMMIT_MESSAGE


class TestGitWrapper(unittest.TestCase):
    def setUp(self):
        self.git_wrapper = GitWrapper(Path("/path/to/repo"))

    @patch("git_wrapper.subprocess.run")
    def test_show_changes_no_changes(self, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout=b""),  # _get_untracked_files
            MagicMock(stdout=b""),  # _get_combined_diff_output (git diff --staged)
            MagicMock(stdout=b"")  # _get_combined_diff_output (git diff)
        ]

        result = self.git_wrapper.show_changes()
        self.assertFalse(result)

    @patch("git_wrapper.subprocess.run")
    @patch("builtins.print")
    def test_show_changes_untracked_files(self, print_mock, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout="file1.txt\nfile2.txt"),  # _get_untracked_files
            MagicMock(stdout=""),  # _get_combined_diff_output (git diff --staged)
            MagicMock(stdout="")  # _get_combined_diff_output (git diff)
        ]

        result = self.git_wrapper.show_changes()
        self.assertTrue(result)

        printed_file1 = False
        printed_file2 = False
        for call in print_mock.call_args_list:
            arg = call.args[0]
            if "file1.txt" in arg:
                printed_file1 = True
            elif "file2.txt" in arg:
                printed_file2 = True

        self.assertTrue(printed_file1)
        self.assertTrue(printed_file2)

    @patch("git_wrapper.subprocess.run")
    @patch("builtins.print")
    def test_show_changes_modified_files(self, print_mock, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout=""),  # _get_untracked_files
            MagicMock(stdout="diff --git a/file1.txt b/file1.txt\n--- a/file1.txt\n+++ b/file1.txt"),
            # _get_combined_diff_output (git diff --staged)
            MagicMock(stdout="")  # _get_combined_diff_output (git diff)
        ]

        result = self.git_wrapper.show_changes()
        self.assertTrue(result)

        printed_diff_output = False
        for call in print_mock.call_args_list:
            arg = call.args[0]
            if "diff --git a/file1.txt b/file1.txt" in arg:
                printed_diff_output = True

        self.assertTrue(printed_diff_output)

    @patch("git_wrapper.subprocess.run")
    @patch("builtins.print")
    def test_show_changes_untracked_and_modified_files(self, print_mock, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout="file2.txt\nfile3.txt"),  # _get_untracked_files
            MagicMock(stdout="diff --git a/file1.txt b/file1.txt\n--- a/file1.txt\n+++ b/file1.txt"),
            # _get_combined_diff_output (git diff --staged)
            MagicMock(stdout="")  # _get_combined_diff_output (git diff)
        ]

        result = self.git_wrapper.show_changes()
        self.assertTrue(result)

        printed_file2 = False
        printed_diff_output = False
        for call in print_mock.call_args_list:
            arg = call.args[0]
            if "+ file2.txt" in arg:
                printed_file2 = True
            if "diff --git a/file1.txt b/file1.txt" in arg:
                printed_diff_output = True

        self.assertTrue(printed_file2)
        self.assertTrue(printed_diff_output)

    @patch("git_wrapper.subprocess.run")
    def test_ensure_push_no_need(self, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout="123456"),  # _get_commit_hash
            MagicMock(stdout="123456")  # _get_remote_commit_hash
        ]

        self.git_wrapper.ensure_push()

        run_mock.assert_any_call(['git', 'rev-parse', 'main'], cwd=self.git_wrapper.path, check=True,
                                 text=True, stdout=-1)
        run_mock.assert_any_call(["git", "ls-remote", "origin", "main"], cwd=self.git_wrapper.path, check=True,
                                 text=True, stdout=-1)

    @patch("git_wrapper.subprocess.run")
    @patch("git_wrapper.UserInput.ask_bool", return_value=False)
    def test_ensure_push_decline(self, ask_bool_mock, run_mock):
        run_mock.side_effect = [
            MagicMock(stdout="123456"),  # _get_commit_hash
            MagicMock(stdout="abcdef")  # _get_remote_commit_hash
        ]

        self.git_wrapper.ensure_push()

        assert (run_mock.call_count == 2)
        run_mock.assert_any_call(['git', 'rev-parse', 'main'], cwd=self.git_wrapper.path, check=True,
                                 text=True, stdout=-1)
        run_mock.assert_any_call(["git", "ls-remote", "origin", "main"], cwd=self.git_wrapper.path, check=True,
                                 text=True, stdout=-1)

    @patch("git_wrapper.UserInput.raw", return_value="Test commit message")
    @patch("git_wrapper.GitWrapper.push")
    def test_commit_and_push(self, push_mock, raw_mock):
        self.git_wrapper.commit_and_push()

        raw_mock.assert_called_once_with(user_texts.commit_message, default=DEFAULT_COMMIT_MESSAGE)
        push_mock.assert_called_once_with("Test commit message", "origin", "main")

    @patch("git_wrapper.GitWrapper._stage_all_changes")
    @patch("git_wrapper.GitWrapper._create_commit")
    @patch("git_wrapper.GitWrapper._push_to_remote")
    def test_push(self, push_to_remote_mock, create_commit_mock, stage_all_changes_mock):
        test_message = "Test commit message"
        test_remote_name = "origin"
        test_branch_name = "main"

        self.git_wrapper.push(test_message, test_remote_name, test_branch_name)

        stage_all_changes_mock.assert_called_once()
        create_commit_mock.assert_called_once_with(test_message)
        push_to_remote_mock.assert_called_once_with(test_remote_name, test_branch_name)

    @patch("subprocess.run")
    def test_discard_changes(self, run_mock):
        self.git_wrapper.discard_changes()

        run_mock.assert_called_once_with(
            ["git", "checkout", "--", "."],
            cwd=self.git_wrapper.path,
            check=True,
        )

    @patch("os.walk")
    def test_files(self, walk_mock):
        walk_mock.return_value = [
            ("/path/to/repo", ["dir1", "dir2", ".git"], ["file1.txt", "file2.txt", ".gitignore"]),
            ("/path/to/repo/dir1", [], ["file3.txt", "file4.txt"]),
            ("/path/to/repo/dir2", [], ["file5.txt"]),
        ]

        expected_files = [
            Path("file1.txt"),
            Path("file2.txt"),
            Path("dir1/file3.txt"),
            Path("dir1/file4.txt"),
            Path("dir2/file5.txt"),
        ]

        result_files = [file for file in self.git_wrapper.files() if file.name != ".gitignore"]

        self.assertEqual(expected_files, result_files)

    @patch("subprocess.run")
    def test_get_changed_files(self, run_mock):
        git_diff_output = (
            "M\tfile1.txt\n"
            "A\tfile2.txt\n"
            "D\tfile3.txt\n"
        )
        git_ls_files_output = (
            "file4.txt\n"
        )

        run_mock.side_effect = [
            unittest.mock.Mock(stdout=git_diff_output),
            unittest.mock.Mock(stdout=git_ls_files_output),
        ]

        expected_changed_files = [
            ("M", Path("file1.txt")),
            ("A", Path("file2.txt")),
            ("?", Path("file4.txt")),
        ]

        result_changed_files = self.git_wrapper.get_changed_files()
        self.assertEqual(expected_changed_files, result_changed_files)

    @patch("subprocess.run")
    def test_stage_all_changes_and_create_commit(self, run_mock):
        # Выполнение приватных методов
        self.git_wrapper._stage_all_changes()
        self.git_wrapper._create_commit("Test commit message")

        # Ожидаемые вызовы subprocess.run
        expected_calls = [
            call(["git", "add", "-A"], cwd=Path("/path/to/repo"), check=True),
            call(["git", "commit", "-m", "Test commit message"], cwd=Path("/path/to/repo"), check=True)
        ]

        # Проверка, что ожидаемые вызовы были сделаны
        run_mock.assert_has_calls(expected_calls)


if __name__ == "__main__":
    unittest.main()
