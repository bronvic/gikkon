from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, PropertyMock, call, patch

from parameterized import parameterized

import user_texts
from backuper import Backuper, Paths
from validator import YES_VARIANTS, Validator

FILE_1 = Path("file1")
FILE_2 = Path("file2")


class TestBackuper(TestCase):
    path = Path("/dev/null")

    def setUp(self):
        with patch("backuper.Git") as _:
            self.backuper = Backuper(self.path)


class TestInit(TestBackuper):
    @parameterized.expand(
        [
            ("not delete not dry", False, False),
            ("not delete dry", False, True),
            ("delete not dry", True, False),
            ("delete dry", True, True),
        ]
    )
    @patch("backuper.Git")
    def test_init(self, _, delete, dry, mock_git):
        backuper = Backuper(self.path, delete, dry)

        mock_git.assert_called_once_with(self.path, dry)
        self.assertEqual(backuper.delete_not_present, delete)
        self.assertEqual(backuper.dry_run, dry)


class TestAdd(TestBackuper):
    def setUp(self):
        super().setUp()

        type(self.backuper.git).path = PropertyMock(return_value=Path("/git/repo"))

    @parameterized.expand(
        [
            (
                "home",
                Mock(return_value=Path.home().joinpath(Path("config/conf.conf"))),
                Path("/git/repo/home/config/conf.conf"),
            ),
            (
                "not home",
                Mock(return_value=Path("/etc/conf.conf")),
                Path("/git/repo/etc/conf.conf"),
            ),
        ]
    )
    @patch("backuper.Path.mkdir")
    @patch("backuper.Backuper._copy")
    def test_add(self, _, path_in, path_out, mock_copy, mock_mkdir):
        mock_path = Mock()
        mock_path.resolve = path_in

        self.backuper.add(mock_path)

        mock_path.resolve.assert_called_once()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_copy.assert_called_once_with(mock_path.resolve.return_value, path_out)


class TestPrintFiles(TestBackuper):
    @classmethod
    def setUpClass(cls):
        cls.skipTest(cls, "logger does not implemented")


class TestBackupBasic(TestBackuper):
    def setUp(self):
        super().setUp()

        self.mock_diff = Mock()
        self.backuper.git.diff = Mock(return_value=self.mock_diff)

    @staticmethod
    def _assert_rollback_not_called(mock_rollback, mock_ask_rollback):
        mock_ask_rollback.assert_not_called()
        mock_rollback.assert_not_called()

    def _assert_copy_diff(self, mock_copy):
        mock_copy.assert_called_once()
        self.backuper.git.diff.assert_called_once()


@patch("backuper.Backuper.copy")
@patch("backuper.interactor.ask_bool")
@patch("backuper.interactor.ask_rollback")
@patch("backuper.Backuper.rollback")
class TestBackup(TestBackupBasic):
    def test_no_files(self, mock_rollback, mock_ask_rollback, mock_ask_accept, mock_copy):
        self.mock_diff.is_empty = True

        self.backuper.backup()

        self._assert_copy_diff(mock_copy)
        mock_ask_accept.assert_not_called()
        self._assert_rollback_not_called(mock_rollback, mock_ask_rollback)

    def test_backup(self, mock_rollback, mock_ask_rollback, mock_ask_accept, mock_copy):
        self.mock_diff.is_empty = False
        mock_ask_accept.return_value = True

        self.backuper.backup()

        self._assert_copy_diff(mock_copy)
        mock_ask_accept.assert_called_once_with(user_texts.accept_changes, default=True)
        self.backuper.git.load_to_remote.assert_called_once()
        self._assert_rollback_not_called(mock_rollback, mock_ask_rollback)


@patch("backuper.Backuper.copy")
@patch("backuper.interactor.ask_bool")
@patch("backuper.interactor.ask_rollback")
@patch("backuper.Backuper.rollback")
class TestBackupAndRollbackReject(TestBackupBasic):
    def setUp(self):
        super().setUp()

        self.mock_diff.is_empty = False

    def test_ask_disabled(self, mock_rollback, mock_ask_rollback, mock_ask_accept, mock_copy):
        mock_ask_accept.return_value = False

        self.backuper.backup(ask_rollback=False)

        self._assert_copy_diff(mock_copy)
        mock_ask_accept.assert_called_once_with(user_texts.accept_changes, default=True)
        self._assert_rollback_not_called(mock_rollback, mock_ask_rollback)

    def test_rejected(self, mock_rollback, mock_ask_rollback, mock_ask_bool, mock_copy):
        mock_ask_bool.side_effect = [False, False]

        self.backuper.backup(ask_rollback=True)

        self._assert_copy_diff(mock_copy)
        self.assertListEqual(
            mock_ask_bool.call_args_list,
            [
                call(user_texts.accept_changes, default=True),
                call(user_texts.rollback_changes, default=True),
            ],
        )
        self._assert_rollback_not_called(mock_rollback, mock_ask_rollback)


@patch("backuper.Backuper.copy")
@patch("backuper.interactor.ask_bool", side_effect=[False, True])
@patch("backuper.interactor.ask_rollback")
@patch("backuper.Backuper.rollback")
@patch("backuper.Validator")
class TestBackupRejectedRollbackAccepted(TestBackupBasic):
    def setUp(self):
        super().setUp()

        self.mock_diff.is_empty = False
        self.mock_diff.untracked_and_changed = ["a", "b", "c"]

    def _assert_ask(self, mock_ask_bool, mock_ask_rollback, mock_validator):
        self.assertListEqual(
            mock_ask_bool.call_args_list,
            [
                call(user_texts.accept_changes, default=True),
                call(user_texts.rollback_changes, default=True),
            ],
        )
        mock_validator.assert_called_once_with(len(self.mock_diff.untracked_and_changed))
        mock_ask_rollback.assert_called_once_with(self.mock_diff.untracked_and_changed, validator=mock_validator())

    def _assert_copy_diff_ask(self, mock_copy, mock_ask_bool, mock_ask_rollback, mock_validator):
        self._assert_copy_diff(mock_copy)
        self._assert_ask(mock_ask_bool, mock_ask_rollback, mock_validator)

    def test_reject(self, mock_validator, mock_rollback, mock_ask_rollback, mock_ask_bool, mock_copy):
        mock_ask_rollback.return_value = ([], False)
        self.backuper.backup(ask_rollback=True)

        self._assert_copy_diff_ask(mock_copy, mock_ask_bool, mock_ask_rollback, mock_validator)
        mock_rollback.assert_not_called()

    def test_rollback(self, mock_validator, mock_rollback, mock_ask_rollback, mock_ask_bool, mock_copy):
        ids = [1, 2, 3]
        diffs = ["one", "two"]
        mock_ask_rollback.return_value = (ids, True)
        self.mock_diff.by_indexes = Mock(return_value=diffs)

        self.backuper.backup(ask_rollback=True)

        self._assert_copy_diff_ask(mock_copy, mock_ask_bool, mock_ask_rollback, mock_validator)
        self.mock_diff.by_indexes.assert_called_once_with(ids)
        mock_rollback.assert_called_once_with(diffs)


@patch("backuper.Backuper._copy")
class TestRollback(TestBackuper):
    @patch("backuper.Backuper.absolute_paths_from_inner")
    def test_rollback(self, mock_path, mock_copy):
        files = [FILE_1, FILE_2]
        inner_files = map(lambda fname: f"/inner{fname}", files)
        mock_path.side_effect = map(lambda xy: Paths(inner=xy[1], outer=xy[0]), zip(files, inner_files))

        self.backuper.rollback(files)

        mock_copy.assert_has_calls(map(lambda xy: call(xy[1], f"/{xy[0]}"), zip(files, inner_files)))

    def test_rollback_no_files(self, mock_copy):
        files = []

        self.backuper.rollback(files)

        mock_copy.assert_not_called()


class TestAbsolutePath(TestBackuper):
    def test_absolute_from_inner(self):
        path = FILE_1
        paths = self.backuper.absolute_paths_from_inner(path)
        self.assertEqual(paths.inner, self.backuper.git.path.joinpath(path))
        self.assertEqual(paths.outer, Path("/").joinpath(path))

    def test_absolute_from_inner_home(self):
        path = Path.home().joinpath(FILE_2)

        paths = self.backuper.absolute_paths_from_inner(path)
        self.assertEqual(paths.inner, self.backuper.git.path.joinpath(path))
        self.assertEqual(paths.outer, path)


class TestDelete(TestBackuper):
    @patch("backuper.Path.unlink")
    def test_delete(self, mock_unlink):
        self.backuper.delete(self.path)

        mock_unlink.assert_called_once_with(missing_ok=True)


@patch("backuper.Backuper._copy")
@patch("backuper.Backuper.delete")
@patch("backuper.Backuper.files", return_value=[FILE_1])
@patch(
    "backuper.Backuper.absolute_paths_from_inner",
    return_value=Paths(inner=FILE_1, outer=FILE_2),
)
class TestCopy(TestBackuper):
    def test_no_files(self, mock_absolute, mock_files, mock_delete, mock_copy):
        mock_files.return_value = []

        self.backuper.copy()

        mock_delete.assert_not_called()
        mock_copy.assert_not_called()

    @patch("backuper.Path.exists", return_value=True)
    @patch("backuper.Path.is_file", return_value=False)
    def test_delete_not_present_false(
        self,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.copy()

        mock_delete.assert_not_called()
        mock_copy.assert_not_called()

    @patch("backuper.Path.exists", return_value=True)
    def test_outer_path_does_not_exist(self, mock_exists, mock_absolute, mock_files, mock_delete, mock_copy):
        self.backuper.delete_not_present = True

        self.backuper.copy()

        mock_exists.assert_called()
        mock_delete.assert_not_called()
        mock_copy.assert_not_called()

    @patch("backuper.Path.exists", return_value=False)
    @patch("backuper.Path.is_file", return_value=False)
    @patch("builtins.input", return_value="fgkbhdk")
    def test_delete_no(
        self,
        mock_input,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.delete_not_present = True

        self.backuper.copy()

        mock_delete.assert_not_called()

    @patch("backuper.Path.exists", return_value=False)
    @patch("backuper.Path.is_file", return_value=False)
    @patch("builtins.input", return_value=YES_VARIANTS[0])
    def test_delete_yes(
        self,
        mock_input,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.delete_not_present = True

        self.backuper.copy()

        mock_delete.assert_called_once_with(FILE_1)

    @patch("backuper.Path.exists", return_value=True)
    @patch("backuper.Path.is_file", return_value=False)
    def test_outer_not_file(
        self,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.copy()

        mock_copy.assert_not_called()

    @patch("backuper.Path.exists", return_value=True)
    @patch("backuper.Path.is_file", return_value=True)
    @patch("backuper.filecmp.cmp", return_value=True)
    def test_files_equal(
        self,
        mock_cmp,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.copy()

        mock_cmp.assert_called_once_with(FILE_2, FILE_1)
        mock_copy.assert_not_called()

    @patch("backuper.Path.exists", return_value=True)
    @patch("backuper.Path.is_file", return_value=True)
    @patch("backuper.filecmp.cmp", return_value=False)
    def test_copy(
        self,
        mock_cmp,
        mock_is_file,
        mock_exists,
        mock_absolute,
        mock_files,
        mock_delete,
        mock_copy,
    ):
        self.backuper.copy()

        mock_cmp.assert_called_once_with(FILE_2, FILE_1)
        mock_copy.assert_called_once_with(FILE_2, FILE_1)


class TestInnerCopy(TestBackuper):
    @patch("backuper.shutil.copy")
    def test_copy(self, mock_copy):
        self.backuper._copy(FILE_1, FILE_2)

        mock_copy.assert_called_once_with(FILE_1, FILE_2)
