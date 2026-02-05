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

import re
import ast
import operator as op
import math
from collections import Counter


def safe_eval(expr: str):
    """
    Safely and correctly evaluates a mathematical expression string.
    This prevents arbitrary code execution vulnerabilities present in eval().
    """
    allowed_operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.USub: op.neg,
    }
    try:
        tree = ast.parse(expr, mode="eval")
    except (SyntaxError, ValueError, TypeError):
        raise ValueError("Invalid syntax in expression")

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, (ast.Num, ast.Constant)):
            return node.n
        elif isinstance(node, ast.UnaryOp):
            op_func = allowed_operators.get(type(node.op))
            if not op_func:
                raise TypeError(
                    f"Disallowed operator: {type(node.op).__name__}"
                )
            return op_func(_eval_node(node.operand))
        elif isinstance(node, ast.BinOp):
            op_func = allowed_operators.get(type(node.op))
            if not op_func:
                raise TypeError(
                    f"Disallowed operator: {type(node.op).__name__}"
                )
            return op_func(_eval_node(node.left), _eval_node(node.right))
        else:
            raise TypeError(f"Disallowed operation: {type(node).__name__}")

    return _eval_node(tree)


class EquationValidator:
    """
    Validates mathematical equations with robust, mathematically-aware logic.
    """

    def _get_canonical_form(self, equation: str) -> str:
        """
        Generates a standardized "canonical" string for an equation.
        - Sorts operands for commutative operations (+, *).
        - Preserves order for non-commutative operations (-, /).
        - Respects order of operations (parentheses).

        Examples:
        - "9+1+9" -> "(1+9+9)"
        - "9+9+1" -> "(1+9+9)" (Same as above)
        - "5*2+3" -> "((2*5)+3)"
        - "3+2*5" -> "(3+(2*5))" (Different)
        """
        try:
            tree = ast.parse(equation, mode="eval").body
        except (SyntaxError, ValueError, TypeError):
            return equation.replace(" ", "")

        def _canonicalize(node):
            if isinstance(node, (ast.Num, ast.Constant)):
                return str(node.n)

            if isinstance(node, ast.UnaryOp):
                # e.g., -(5+2) -> "(-((2+5)))"
                op_symbol = {ast.USub: "-"}.get(type(node.op), "")
                return f"({op_symbol}{_canonicalize(node.operand)})"

            if isinstance(node, ast.BinOp):
                op_type = type(node.op)
                op_symbol = {
                    ast.Add: "+",
                    ast.Sub: "-",
                    ast.Mult: "*",
                    ast.Div: "/",
                }.get(op_type)

                if op_type in (ast.Add, ast.Mult):
                    operands = []

                    def _collect_operands(sub_node):
                        if (
                            isinstance(sub_node, ast.BinOp)
                            and isinstance(sub_node.op, op_type)
                        ):
                            _collect_operands(sub_node.left)
                            _collect_operands(sub_node.right)
                        else:
                            operands.append(_canonicalize(sub_node))

                    _collect_operands(node)
                    operands.sort()
                    return f"({op_symbol.join(operands)})"

                else:
                    left = _canonicalize(node.left)
                    right = _canonicalize(node.right)
                    return f"({left}{op_symbol}{right})"

            return ""

        return _canonicalize(tree)

    def _extract_operands_and_operators(self, equation: str) -> tuple:
        """
        Extract all operands and operators from an equation for structural comparison.
        Returns a tuple of (operands_counter, operators_counter, structure_signature).

        This allows us to distinguish between:
        - (9+1) vs (1+9): Same operands [1,9], same operators [+] -> Equivalent
        - (2+8) vs (1+9): Different operands [2,8] vs [1,9], same operators [+] -> NOT Equivalent
        """
        try:
            tree = ast.parse(equation, mode="eval").body
        except (SyntaxError, ValueError, TypeError):
            return Counter(), Counter(), ""

        operands = []
        operators = []

        def _extract(node):
            if isinstance(node, (ast.Num, ast.Constant)):
                val = node.n
                operands.append(int(val) if val == int(val) else val)

            elif isinstance(node, ast.UnaryOp):
                op_name = type(node.op).__name__
                operators.append(f"unary_{op_name}")
                _extract(node.operand)

            elif isinstance(node, ast.BinOp):
                op_name = type(node.op).__name__
                operators.append(op_name)
                _extract(node.left)
                _extract(node.right)

        _extract(tree)

        operands_counter = Counter(operands)
        operators_counter = Counter(operators)

        structure_sig = self._get_canonical_form(equation)

        return operands_counter, operators_counter, structure_sig

    def validate(self, equation, target):
        """
        Validate if an equation equals the target value. Secure and robust.
        (This implementation is already solid and remains unchanged).
        """
        result = {"valid": False, "error": "", "value": None}
        equation = equation.strip()
        if not equation:
            result["error"] = "Equation is empty"
            return result
        if re.search(r"[^0-9+\-*/().\s]", equation):
            result["error"] = "Invalid characters in equation"
            return result
        # Disallow unary plus to match safe_eval behaviour
        if re.search(r"(^|\(|\s)\+", equation) :
            result["error"] = "Unary plus is not allowed"
            return result
        try:
            value = safe_eval(equation)
            result["value"] = value
            if math.isclose(value, float(target)):
                result["valid"] = True
            else:
                result["error"] = f"Result is {value:.2f}, not {target}"
        except ZeroDivisionError:
            result["error"] = "Division by zero"
        except (ValueError, TypeError) as e:
            result["error"] = f"Invalid equation: {e}"
        return result

    def are_equations_equivalent(self, eq1: str, eq2: str) -> bool:
        """
        Enhanced check for mathematical equivalence based on structural similarity.

        Two equations are considered equivalent if they have:
        1. The same operands (numbers) with the same frequency
        2. The same operators with the same frequency
        3. The same structural arrangement (considering commutativity)

        Examples:
        - (9+1) ≡ (1+9) -> True (same operands, same operators, commutative)
        - (2+8) ≢ (1+9) -> False (different operands: {2,8} vs {1,9})
        - (5*2) ≡ (2*5) -> True (same operands, same operators, commutative)
        - (10-5) ≢ (5-10) -> False (subtraction is not commutative)
        - (3+2*4) ≢ (2*4+3) -> True (same operands {2,3,4}, same operators {+,*})
        """
        if eq1.replace(" ", "") == eq2.replace(" ", ""):
            return True

        operands1, operators1, structure1 = self._extract_operands_and_operators(eq1)
        operands2, operators2, structure2 = self._extract_operands_and_operators(eq2)

        if not structure1 or not structure2:
            return False

        same_operands = operands1 == operands2
        same_operators = operators1 == operators2

        if not (same_operands and same_operators):
            return False

        return structure1 == structure2

    def are_equations_unique(self, eq1: str, eq2: str) -> bool:
        """
        Convenience method that returns True if equations are unique (NOT equivalent).
        This is the inverse of are_equations_equivalent.
        """
        return not self.are_equations_equivalent(eq1, eq2)

    def get_equation_signature(self, equation: str) -> dict:
        """
        Get a detailed signature of an equation for debugging/analysis purposes.
        """
        operands, operators, structure = self._extract_operands_and_operators(equation)
        try:
            value = safe_eval(equation)
        except Exception:
            value = None

        return {
            "equation": equation,
            "operands": dict(operands),
            "operators": dict(operators),
            "canonical_form": structure,
            "numerical_value": value,
        }


# Example usage and testing
if __name__ == "__main__":
    validator = EquationValidator()

    # Test cases
    test_cases = [
        ("9+1", "1+9", True),  # Commutative addition - should be equivalent
        ("2+8", "1+9", False),  # Different operands - should NOT be equivalent
        ("5*2", "2*5", True),  # Commutative multiplication - should be equivalent
        (
            "10-5",
            "5-10",
            False,
        ),  # Non-commutative subtraction - should NOT be equivalent
        (
            "3+2*4",
            "2*4+3",
            True,
        ),  # Same operands/operators, different order - should be equivalent
        ("(9+1)", "(1+9)", True),  # With parentheses - should be equivalent
        ("2*3+4", "3*2+4", True),  # Mixed operations - should be equivalent
        (
            "6/2",
            "2*3",
            False,
        ),  # Same result, different operands/operators - should NOT be equivalent
    ]

    print("Testing equation equivalence:")
    print("=" * 50)

    for eq1, eq2, expected in test_cases:
        result = validator.are_equations_equivalent(eq1, eq2)
        status = "✓" if result == expected else "✗"
        print(f"{status} {eq1} ≡ {eq2}: {result} (expected: {expected})")

        if result != expected:
            print("   Debug info:")
            print(f"   {eq1}: {validator.get_equation_signature(eq1)}")
            print(f"   {eq2}: {validator.get_equation_signature(eq2)}")

    print("\n" + "=" * 50)
    print("Equation signatures for analysis:")
    equations = ["9+1", "1+9", "2+8", "10-5", "5-10"]
    for eq in equations:
        sig = validator.get_equation_signature(eq)
        print(f"{eq}: {sig}")
