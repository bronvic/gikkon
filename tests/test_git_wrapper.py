import unittest
from pathlib import Path
from typing import NamedTuple
from unittest import SkipTest, TestCase
from unittest.mock import call, patch

from git_wrapper import DEFAULT_COMMIT_MESSAGE, Diff, Git
from tests.fixtures.formatting import git_output

# TODO: finish type and update test_format
FileTypes = NamedTuple("FileTypes", [])


class TestGit(TestCase):
    def setUp(self):
        self.path = Path("/dev/null")


class TestInit(TestGit):
    @patch("git_wrapper.Repo", return_value="hello, repo")
    def test_init(self, mock_repo):
        test_cases = [False, True]

        for dry_run in test_cases:
            with self.subTest(dry_run=dry_run):
                git = Git(self.path, dry_run)

                self.assertEqual(git.path, self.path)
                self.assertEqual(git.repo, "hello, repo")
                self.assertEqual(git.dry_run, dry_run)

                # Might be better:
                # mock_repo.assert_called_once_with(str(self.path))
                mock_repo.assert_has_calls()


class TestLoadToRemote(TestGit):
    @patch("git_wrapper.Repo")
    def setUp(self, mock_repo):
        super().setUp()

        self.git = Git(self.path)

    @patch("builtins.input", return_value="")
    def test_commit_default_message(self, mock_input):
        self.git.load_to_remote()

        self.git.repo.git.add.assert_called_once_with(all=True)
        self.git.repo.index.commit.assert_called_once_with(DEFAULT_COMMIT_MESSAGE)
        self.git.repo.remote().push.assert_called_once()

    @patch("builtins.input", return_value="my commit message")
    def test_commit_custom_message(self, mock_input):
        self.git.load_to_remote()

        self.git.repo.git.add.assert_called_once_with(all=True)
        self.git.repo.index.commit.assert_called_once_with(mock_input.return_value)
        self.git.repo.remote().push.assert_called_once()


class TestDiff(TestCase):
    def setUp(self):
        self.untracked = list(map(Path, ["/untracked1", "/untracked2", "/untracked3"]))
        self.deleted = list(map(Path, ["/deleted1", "/deleted2", "/deleted3"]))
        self.changed = list(map(Path, ["/changed1", "/changed2", "/changed3"]))

        self.diff = Diff(untracked=self.untracked, deleted=self.deleted, changed=self.changed)

    def test_init(self):
        self.assertListEqual(self.diff.untracked, self.untracked)
        self.assertListEqual(self.diff.deleted, self.deleted)
        self.assertListEqual(self.diff.changed, self.changed)

        # positional arguments does not allow
        with self.assertRaises(TypeError):
            Diff(self.untracked, self.deleted, self.changed)

    def test_format(self):
        test_cases = [
            # (untracked
            (True, True, True),
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, False),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                if not case[0]:
                    self.diff.untracked = []
                if not case[1]:
                    self.diff.deleted = []
                if not case[2]:
                    self.diff.changed = []

                self.assertEqual(
                    str(self.diff),
                    git_output(self.diff.untracked, self.diff.deleted, self.diff.changed),
                )

    def test_indexes(self):
        self.assertEqual(self.diff.by_indexes([0]), [self.diff.changed[0]])
        self.assertEqual(self.diff.by_indexes([1, 2]), [self.diff.changed[1], self.diff.changed[2]])

    def test_indexes_exception(self):
        with self.assertRaises(IndexError):
            self.diff.by_indexes([100])

        with self.assertRaises(IndexError):
            self.diff.by_indexes([0, 1, 120])

    def test_is_empty(self):
        self.assertFalse(self.diff.is_empty)

        self.diff.untracked = []
        self.diff.deleted = []
        self.diff.changed = []
        self.assertTrue(self.diff.is_empty)
