import unittest

from validator import RollbackValidator, NO_VARIANTS, ALLOWED_SEPARATORS


class TestRollbackValidator(unittest.TestCase):

    def setUp(self):
        self.limit = 5
        self.validator = RollbackValidator(self.limit)

    def test_empty_input(self):
        self.assertTrue(self.validator.is_valid(""))

    def test_no_variants(self):
        for variant in NO_VARIANTS:
            self.assertTrue(self.validator.is_valid(variant))

    def test_valid_input(self):
        valid_inputs = [
            "0",
            "1",
            "0 1",
            "0,1",
            "0, 1",
            "0, 1,",
            "1,2,3",
            "0 1 2 3 4",
        ]
        for valid_input in valid_inputs:
            self.assertTrue(self.validator.is_valid(valid_input), f"Failed for input: {valid_input}")

    def test_invalid_input(self):
        invalid_inputs = [
            " ",
            ",",
            "0-1",
            "5",
            "0,5",
            "0 5",
            "1,5",
            "0 1 2 3 4 5",
        ]
        for invalid_input in invalid_inputs:
            self.assertFalse(self.validator.is_valid(invalid_input), f"Failed for input: {invalid_input}")

    def test_mixed_separators(self):
        for sep1 in ALLOWED_SEPARATORS:
            for sep2 in ALLOWED_SEPARATORS:
                if sep1 != sep2:
                    mixed_input = f"1{sep1}2{sep2}3"
                    self.assertTrue(self.validator.is_valid(mixed_input), f"Failed for input: {mixed_input}")


if __name__ == "__main__":
    unittest.main()
