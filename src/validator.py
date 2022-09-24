import re

from user_texts import index_out_of_bounds

YES_VARIANTS = ("yes", "y")
NO_VARIANTS = ("no", "n")

ALLOWED_SEPARATORS = (" ", ",")


class RollbackValidator:
    def __init__(self, limit: int):
        self.limit = limit
        self.error_message = index_out_of_bounds.format(0, limit)

    def is_valid(self, user_input: str) -> bool:
        """
        Validate user input for rollback functionality.
        Allowed NO_VARIANTS or any combination of digits and ALLOWED_SEPARATORS.
        Each result number should not be greater than the given limit.
        Empty string is allowed, string with separators only is not.
        """
        user_input = user_input.lower()
        if user_input in NO_VARIANTS:
            return True

        # Split user_input into numbers using ALLOWED_SEPARATORS
        parsed_input = re.findall(r'\d+', user_input)

        # Check that the input is not empty and contains at least one number
        if not parsed_input:
            return False

        # Check that every user string line is less than the total number of lines
        return all(int(s) <= self.limit for s in parsed_input)
