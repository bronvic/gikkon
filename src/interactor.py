import re
from pathlib import Path
from typing import List, Optional

import user_texts
from validator import ALLOWED_SEPARATORS, NO_VARIANTS, YES_VARIANTS, RollbackValidator


class UserInput:
    @staticmethod
    def raw(prompt: str, default: str = "") -> str:
        user_input = input(prompt).lower()
        return user_input if user_input else default.lower()

    @staticmethod
    def ask_bool(question: str, default: bool = False) -> bool:
        if not question.endswith("?"):
            question += "?"

        suffix = " [Y/n]: "
        default_srt = YES_VARIANTS[0]
        if not default:
            suffix = " [y/N]: "
            default_srt = NO_VARIANTS[0]

        user_input = UserInput.raw(f"{question}{suffix}", default=default_srt)
        if user_input in YES_VARIANTS:
            return True
        if user_input in NO_VARIANTS:
            return False

        return default

    @staticmethod
    def ask_rollback(
            rollback_candidates: List[Path],
            validator: Optional[RollbackValidator] = None,
    ) -> tuple[Optional[set[int]], bool]:
        while True:
            prompt = [user_texts.specify_rollback]

            for i, path in enumerate(rollback_candidates):
                prompt += f"{i} {path}"

            user_input = UserInput.raw("\n".join(prompt) + "\n")
            if not validator or validator.is_valid(user_input):
                break

            print(validator.error_message + "\n\n")

        if not user_input:
            user_input = ALLOWED_SEPARATORS[0].join(
                map(str, range(len(rollback_candidates)))
            )

        if user_input in NO_VARIANTS:
            return None, False

        user_input = re.split("|".join(ALLOWED_SEPARATORS), user_input)

        return set(map(int, filter(bool, user_input))), True
