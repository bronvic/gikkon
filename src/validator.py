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

        if not user_input:
            return True

        if user_input in NO_VARIANTS:
            return True

        # Split user_input into numbers using ALLOWED_SEPARATORS
        if re.match(f"^(?:\d+(?:{'|'.join(ALLOWED_SEPARATORS)})*?)+$", user_input):
            indices = re.split("|".join(ALLOWED_SEPARATORS), user_input)
            # Check that every user string line is less than the total number of lines
            return all(int(index) < self.limit for index in indices if index)

        return False
