import unittest
from unittest import TestCase

from parameterized import parameterized

from validator import Validator


class TestRollback(TestCase):
    @parameterized.expand(
        [
            ("empty", ("", 0), True),
            ("single digit", ("1", 1), True),
            ("number", ("123", 123), True),
            ("separator ','", ("1,2,3", 3), True),
            ("separator ' '", ("1 2 3", 3), True),
            ("mixed separators", ("1, 2 3, 4, ", 4), True),
            ("only separators", ("  , ,,  ", 0), False),
            ("with letters", ("1, 2, 3a, 4", 4), False),
            ("only letters", ("meo", 4), False),
        ]
    )
    def test_rollback(self, _mock_test_name, mock_user_input, mock_result):
        self.assertEqual(Validator(mock_user_input[1]).validate(mock_user_input[0]), mock_result)

    @parameterized.expand(
        [
            ("less than max", ("1,2,3", 5), True),
            ("more than max", ("1,2,3", 2), False),
            ("equal max", ("1,2,3", 3), True),
        ]
    )
    def test_rollback_with_maximum(self, _gle_name, mock_user_input, mock_result):
        self.assertEqual(
            Validator(mock_user_input[1]).validate(mock_user_input[0]),
            mock_result,
        )
