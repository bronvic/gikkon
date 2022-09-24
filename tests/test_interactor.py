from unittest import TestCase
from unittest.mock import Mock, call, patch

from parameterized import parameterized

import interactor
from validator import NO_VARIANTS, YES_VARIANTS


class TestRaw(TestCase):
    @parameterized.expand(
        [
            ("empty without default", ("", ""), ""),
            ("empty with default", ("", "default"), "default"),
            ("empty with default capitalize", ("", "DEFAULT"), "default"),
            ("lowercase", ("user_input", "default"), "user_input"),
            ("uppercase ", ("USER_input", ""), "user_input"),
        ]
    )
    @patch("builtins.input")
    def test_raw_without_default(self, _mock_test_name, mock_params, mock_result, mock_input):
        mock_input.return_value = mock_params[0]
        self.assertEqual(interactor.raw("Prompt: ", mock_params[1]), mock_result)


QUESTION = "How do you do?"


@patch("interactor.raw")
class TestAskBool(TestCase):
    @parameterized.expand(
        [
            ("question mark", QUESTION),
            ("no question mark", QUESTION[:-1]),
        ]
    )
    def test_question_mark(self, mock_raw, _, question):
        mock_raw.return_value = "kkkk"
        res = interactor.ask_bool(question)

        self.assertFalse(res)
        mock_raw.assert_called_once_with(f"{QUESTION} [y/N]: ", default=NO_VARIANTS[0])

    @parameterized.expand(
        [
            ("user accept", YES_VARIANTS[0]),
            ("user reject", NO_VARIANTS[0]),
            ("user default", "AAAA"),
        ]
    )
    def test_default_true(self, mock_raw, _, user_input):
        mock_raw.return_value = user_input

        res = interactor.ask_bool(QUESTION, default=True)

        mock_raw.assert_called_once_with(f"{QUESTION} [Y/n]: ", default=YES_VARIANTS[0])

        if user_input in YES_VARIANTS:
            self.assertTrue(res)
        elif user_input in NO_VARIANTS:
            self.assertFalse(res)
        else:
            self.assertTrue(res)

    @parameterized.expand(
        [
            ("user accept", YES_VARIANTS[0]),
            ("user reject", NO_VARIANTS[0]),
            ("user default", "AAAA"),
        ]
    )
    def test_default_false(self, mock_raw, _, user_input):
        mock_raw.return_value = user_input

        res = interactor.ask_bool(QUESTION, default=False)

        mock_raw.assert_called_once_with(f"{QUESTION} [y/N]: ", default=NO_VARIANTS[0])

        if user_input in YES_VARIANTS:
            self.assertTrue(res)
        elif user_input in NO_VARIANTS:
            self.assertFalse(res)
        else:
            self.assertFalse(res)


@patch("interactor.raw")
class TestAskRollback(TestCase):
    prompt = "something"
    ok_return_value = {1, 2, 3}

    def ask_rollback(self, validator=None, default=None):
        return interactor.ask_rollback(self.prompt, validator, default)

    @parameterized.expand(
        [
            ("comma separator", "1, 2, 3"),
            ("whitespace separator", "1 2 3"),
            ("combined separators", "1, 2 3"),
            ("multiple separators in a row", "1,,,,2      3"),
        ]
    )
    def test_accept(self, mock_raw, _mock_name, mock_user_input):
        mock_raw.return_value = mock_user_input

        numbers, ok = self.ask_rollback()

        mock_raw.assert_called_once_with(self.prompt)
        self.assertTrue(ok)
        self.assertSetEqual(self.ok_return_value, numbers)

    def test_reject(self, mock_raw):
        mock_raw.return_value = NO_VARIANTS[0]

        numbers, ok = self.ask_rollback()
        self.assertFalse(ok)
        self.assertIsNone(numbers)

    @patch("interactor.Validator")
    def test_validator(self, mock_validator, mock_raw):
        user_input = NO_VARIANTS[0]
        default = [1, 2, 3]
        mock_validator.validate = Mock(return_value=True)
        mock_raw.return_value = user_input

        res, ok = self.ask_rollback(mock_validator, default)
        self.assertFalse(ok)
        mock_validator.validate.assert_called_once_with(user_input)

    @patch("interactor.Validator")
    def test_validator_error(self, mock_validator, mock_raw):
        user_inputs = ["error", "1 2 3"]
        mock_validator.validate = Mock(side_effect=[False, True])
        mock_validator.error_message = "error msg"
        mock_raw.side_effect = user_inputs

        res, ok = self.ask_rollback(mock_validator)

        self.assertTrue(ok)
        self.assertSetEqual(self.ok_return_value, res)
        mock_validator.validate.assert_has_calls([call(user_inputs[0]), call(user_inputs[1])])
        mock_raw.assert_has_calls([call(self.prompt), call(self.prompt)])
