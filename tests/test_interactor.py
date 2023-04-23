import unittest
from pathlib import Path
from unittest.mock import patch

from interactor import UserInput
from validator import RollbackValidator


class TestUserInput(unittest.TestCase):
    @patch("builtins.input", side_effect=["", "test input"])
    def test_raw(self, input_mock):
        # Проверка, что возвращается значение по умолчанию при пустом вводе
        default_value = "default value"
        result = UserInput.raw("Enter some text: ", default=default_value)
        self.assertEqual(result, default_value.lower())

        # Проверка, что возвращается введенное значение
        result = UserInput.raw("Enter some text: ")
        self.assertEqual(result, "test input")

    @patch("builtins.input", side_effect=["", "y", "n", "yes", "no"])
    def test_ask_bool(self, input_mock):
        # Проверка, что возвращается значение по умолчанию при пустом вводе
        result = UserInput.ask_bool("Is this a question?", default=True)
        self.assertEqual(result, True)

        # Проверка, что возвращается True при "y"
        result = UserInput.ask_bool("Is this a question?", default=False)
        self.assertEqual(result, True)

        # Проверка, что возвращается False при "n"
        result = UserInput.ask_bool("Is this a question?", default=True)
        self.assertEqual(result, False)

        # Проверка, что возвращается True при "yes"
        result = UserInput.ask_bool("Is this a question?", default=False)
        self.assertEqual(result, True)

        # Проверка, что возвращается False при "no"
        result = UserInput.ask_bool("Is this a question?", default=True)
        self.assertEqual(result, False)

    @patch("builtins.input", side_effect=["", "0,1", "0-2", "1", "no"])
    def test_ask_rollback(self, input_mock):
        rollback_candidates = [Path("file1.txt"), Path("file2.txt"), Path("file3.txt")]
        validator = RollbackValidator(len(rollback_candidates))

        # Проверка, что возвращается все индексы при пустом вводе
        indices, success = UserInput.ask_rollback(rollback_candidates, validator)
        self.assertEqual(indices, {0, 1, 2})
        self.assertTrue(success)

        # Проверка, что возвращается корректный набор индексов при вводе "0,1"
        indices, success = UserInput.ask_rollback(rollback_candidates, validator)
        self.assertEqual(indices, {0, 1})
        self.assertTrue(success)

        # Проверка, что при невалидном вводе "0-2" запрашивается повторный ввод
        result_rollback, success = UserInput.ask_rollback(rollback_candidates, validator)
        self.assertEqual(result_rollback, {1})
        self.assertTrue(success)

        # Проверка, что возвращается None и False при вводе "no"
        indices, success = UserInput.ask_rollback(rollback_candidates, validator)
        self.assertIsNone(indices)
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
