# This file is part of the Broken Calculator game.
# Copyright (C) 2025 Bishoy Wadea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import random
from typing import List


class BrokenButtonValidator:
    """
    Validates and generates broken calculator buttons while ensuring
    the puzzle remains solvable.
    """

    ALL_BUTTONS = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "+", "-", "*", "/", "(", ")"
    ]

    SMALL_TARGET_THRESHOLD = 50
    MAX_RECURSION_ATTEMPTS = 10

    def generate_broken_buttons(self, target: int, count: int, attempts: int = 0) -> List[str]:
        """
        Generate a list of broken buttons while ensuring the target
        remains solvable.

        Args:
            target (int): Target number for the puzzle.
            count (int): Number of buttons to break.
            attempts (int): Internal retry counter to avoid infinite recursion.

        Returns:
            List[str]: List of broken button symbols.
        """
        if count <= 0 or attempts >= self.MAX_RECURSION_ATTEMPTS:
            return []

        required_working = self._get_required_working_buttons(target)
        breakable = [b for b in self.ALL_BUTTONS if b not in required_working]

        max_breakable = min(count, len(breakable))
        broken = random.sample(breakable, max_breakable)

        if not self.validate_solvable(target, broken):
            return self.generate_broken_buttons(
                target,
                count - 1,
                attempts + 1
            )

        return broken

    def validate_solvable(self, target: int, broken_buttons: List[str]) -> bool:
        """
        Check whether the target number can reasonably be reached
        using the remaining working buttons.

        Args:
            target (int): Target number.
            broken_buttons (List[str]): Buttons that are unavailable.

        Returns:
            bool: True if solvable, False otherwise.
        """
        working_buttons = [
            b for b in self.ALL_BUTTONS if b not in broken_buttons
        ]

        digits = [int(b) for b in working_buttons if b.isdigit()]
        operators = [b for b in working_buttons if b in "+-*/"]

        if not digits or not operators:
            return False

        max_reachable = self._estimate_max_reachable_value(digits, operators)
        return max_reachable >= target

    def _get_required_working_buttons(self, target: int) -> set:
        """
        Determine the minimum required buttons to keep the puzzle solvable.
        """
        if target <= self.SMALL_TARGET_THRESHOLD:
            return {"1", "+"}
        return {"2", "*", "+"}

    def _estimate_max_reachable_value(self, digits: List[int], operators: List[str]) -> int:
        """
        Rough estimation of the maximum value that can be reached
        using available digits and operators.
        """
        max_digit = max(digits)
        estimate = max_digit * 10

        if "+" in operators:
            estimate = max(estimate, sum(digits) * 5)

        if "*" in operators and len(digits) >= 2:
            estimate = max(estimate, max_digit ** 2)

        return estimate
