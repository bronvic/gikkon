import unittest
from pathlib import Path
from unittest import SkipTest, TestCase
from unittest.mock import call, patch

from parameterized import parameterized

from git_saver import COMMIT_MESSAGE, Git


class TestGit(TestCase):
    def setUp(self):
        self.path = Path("/dev/null")


class TestInit(TestGit):
    @parameterized.expand(
        [
            (
                "dry run false",
                False,
            ),
            (
                "dry run true",
                True,
            ),
        ]
    )
    @patch("git_saver.Repo", return_value="hello, repo")
    def test_init(self, _, mock_dry_run, mock_repo):
        git = Git(self.path, mock_dry_run)

        self.assertEqual(git.path, self.path)
        self.assertEqual(git.repo, "hello, repo")
        self.assertEqual(git.dry_run, mock_dry_run)

        mock_repo.assert_called_once_with(str(self.path))


class TestCommitAndPush(TestGit):
    @patch("git_saver.Repo")
    def setUp(self, mock_repo):
        super().setUp()

        self.git = Git(self.path)

    @patch("builtins.input", return_value="")
    def test_commit_default_message(self, mock_input):
        self.git.commit_and_push()

        self.git.repo.git.add.assert_called_once_with(all=True)
        self.git.repo.index.commit.assert_called_once_with(COMMIT_MESSAGE)
        self.git.repo.remote().push.assert_called_once()

    @patch("builtins.input", return_value="my commit message")
    def test_commit_custom_message(self, mock_input):
        self.git.commit_and_push()

        self.git.repo.git.add.assert_called_once_with(all=True)
        self.git.repo.index.commit.assert_called_once_with(mock_input.return_value)
        self.git.repo.remote().push.assert_called_once()


class TestPushToRepo(TestGit):
    @classmethod
    def setUpClass(cls):
        cls.skipTest(cls, "logger does not implemented")
