import importlib
import sys
from pathlib import Path
from unittest import SkipTest, TestCase
from unittest.mock import Mock, PropertyMock, call, patch

from parameterized import parameterized

from backuper import Backuper, Pathes


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
        self.assertEqual(backuper.delete_unpresent, delete)
        self.assertEqual(backuper.dry_run, dry)


class TestBackup(TestBackuper):
    @patch("backuper.Backuper.save_to_git")
    def test_backup(self, mock_save):

        self.backuper.backup()

        mock_save.assert_called_once()
        self.backuper.git.push_to_repo.assert_called_once()


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
    @patch("backuper.Backuper.copy")
    def test_add(self, _, path_in, path_out, mock_copy, mock_mkdir):
        mock_path = Mock()
        mock_path.resolve = path_in

        self.backuper.add(mock_path)

        mock_path.resolve.assert_called_once()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_copy.assert_called_once_with(mock_path.resolve.return_value, path_out)


class TestCommit(TestBackuper):
    def test_commit(self):
        self.backuper.commit()

        self.backuper.git.push_to_repo.assert_called_once()


class TestPrintFiles(TestBackuper):
    @classmethod
    def setUpClass(cls):
        cls.skipTest(cls, "logger does not implemented")


FILE_1 = Path("file1")
FILE_2 = Path("file2")
INNER_PATH = Path("inner_path")
OUTER_PATH = Path("outer_path")


@patch("backuper.Backuper.files", return_value=[FILE_1, FILE_2])
@patch(
    "backuper.Backuper.absolute_pathes_from_inner",
    return_value=Pathes(INNER_PATH, OUTER_PATH),
)
class TestSaveToGit(TestBackuper):
    def test_no_files(self, _, mock_files):
        mock_files.return_value = []
        self.backuper.save_to_git()

    @patch("backuper.Path.exists", return_value=False)
    def test_outer_path_does_not_exists(self, mock_exists, mock_absolute, _):
        self.backuper.save_to_git()

        mock_absolute.assert_has_calls([call(FILE_1), call(FILE_2)])
        self.assertEqual(mock_exists.call_count, 2)

    @parameterized.expand(
        [
            (
                "delete yes",
                "Y",
                True,
            ),
            (
                "delete no",
                "nononono",
                False,
            ),
        ]
    )
    @patch("backuper.Path.exists", return_value=False)
    @patch("backuper.filecmp.cmp")
    @patch("backuper.Backuper.delete")
    @patch("builtins.input")
    def test_delete(
        self,
        _,
        user_input,
        delete_expected,
        mock_input,
        mock_delete,
        mock_cmp,
        mock_exists,
        mock_absolute,
        mock_files,
    ):
        self.backuper.delete_unpresent = True
        mock_input.return_value = user_input

        self.backuper.save_to_git()

        self.assertEqual(mock_input.call_count, 2)
        mock_cmp.assert_not_called()
        if delete_expected:
            mock_delete.assert_has_calls([call(INNER_PATH)] * 2)
        else:
            mock_delete.assert_not_called()

    @patch("backuper.Path.exists", return_value=False)
    @patch("backuper.filecmp.cmp")
    def test_outer_not_file(self, mock_cmp, mock_exists, mock_absolute, mock_files):
        self.backuper.save_to_git()

        mock_cmp.assert_not_called()

    @patch("backuper.Path.exists", return_value=True)
    @patch("backuper.Path.is_file", return_value=True)
    @patch("backuper.filecmp.cmp", return_value=False)
    @patch("backuper.Backuper.copy")
    def test_cmp_different(
        self, mock_copy, mock_cmp, mock_is_file, mock_exists, mock_absolute, mock_files
    ):
        self.backuper.save_to_git()

        mock_copy.assert_has_calls([call(OUTER_PATH, INNER_PATH)] * 2)


class TestAbsolutePath(TestBackuper):
    def test_absolute_from_inner(self):
        path = FILE_1
        pathes = self.backuper.absolute_pathes_from_inner(path)
        self.assertEqual(pathes.inner, self.backuper.git.path.joinpath(path))
        self.assertEqual(pathes.outer, Path("/").joinpath(path))

    def test_absolute_from_inner_home(self):
        path = Path.home().joinpath(FILE_2)

        pathes = self.backuper.absolute_pathes_from_inner(path)
        self.assertEqual(pathes.inner, self.backuper.git.path.joinpath(path))
        self.assertEqual(pathes.outer, path)


class TestDelete(TestBackuper):
    @patch("backuper.Path.unlink")
    def test_delete(self, mock_unlink):
        self.backuper.delete(self.path)

        mock_unlink.assert_called_once_with(missing_ok=True)


class TestCopy(TestBackuper):
    @patch("backuper.shutil.copy")
    def test_copy(self, mock_copy):
        self.backuper.copy(FILE_1, FILE_2)

        mock_copy.assert_called_once_with(FILE_1, FILE_2)


class TestFiles(TestBackuper):
    pass
