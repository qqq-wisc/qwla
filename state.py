"""
Quantum state simulator using functional programming techniques.
This module implements a quantum state class that supports various quantum gates
and operations without requiring matrix algebra.
"""

from math import sqrt, pi
from cmath import exp
import random
from typing import Optional
from functional import seq
from bitarray import frozenbitarray as bitarray
from bitarray import bitarray as mut_bitarray


# Helper functions for bit manipulation
def set_bit(x: bitarray, i: int, v: int) -> bitarray:
    """Set the i-th bit of bitarray x to value v (0 or 1)"""
    new = mut_bitarray(x)
    new[i] = v
    return bitarray(new)


def flip(x: bitarray, i: int) -> bitarray:
    """Flip (negate) the i-th bit of bitarray x"""
    mask = bitarray("0" * i + "1" + "0" * (len(x) - i - 1))
    return x ^ mask


class State:
    """
    Quantum state using a dictionary-like structure mapping bitstrings to amplitudes.
    """

    def __init__(self, n_qubits: int, n_bits: int = 0):
        """
        Initialize a quantum state with n_qubits qubits and n_bits classical bits.

        Args:
            n_qubits: Number of qubits in the system
            n_bits: Number of classical bits for measurement results

        The state starts in 0...0 (ground state).
        """
        assert n_qubits > 0 and n_bits >= 0

        self.n_qubits = n_qubits
        self.n_bits = n_bits
        self.state = seq(
            [
                (bitarray(format(i, f"0{n_qubits}b")), 1.0 if i == 0 else 0.0)
                for i in range(2**n_qubits)
            ]
        )
        self.cbits = [0] * n_bits

    def x(self, j: int):
        """
        Apply the NOT gate to the j-th qubit.

        This gate flips the basis states where qubit j is present.
        """
        print(f"-> Applying X gate to qubit {j}")
        self.state = self.state.smap(lambda b, a: (flip(b, j), a))
        return self

    def cx(self, j: int, k: int):
        """
        Apply the CX (controlled-NOT) gate with control qubit ctrl (j) and target (k) qubit trgt.
        """
        print(f"-> Applying CX gate with control {j} and target {k}")
        self.state = self.state.smap(lambda b, a: (b if not b[j] else flip(b, k), a))
        return self

    def s(self, j: int):
        """
        Apply the S (phase) gate to the j-th qubit.
        """
        print(f"-> Applying S gate to qubit {j}")
        self.state = self.state.smap(lambda b, a: (b, (1j ** b[j]) * a))
        return self

    def t(self, j: int):
        """
        Apply the T gate to the j-th qubit.
        """
        print(f"-> Applying T gate to qubit {j}")
        phase = exp(1j * pi / 4)
        self.state = self.state.smap(lambda b, a: (b, (phase ** b[j]) * a))
        return self

    def h(self, j: int):
        """
        Apply the Hadamard gate to the j-th qubit.
        """
        print(f"-> Applying Hadamard gate to qubit {j}")
        norm = 1 / sqrt(2)
        self.state = (
            self.state.smap(
                lambda b, a: [
                    (set_bit(b, j, 0), a * norm),
                    (set_bit(b, j, 1), a * norm * (-1 if b[j] else 1)),
                ]
            )
            .flatten()
            .reduce_by_key(lambda x, y: x + y)
        )
        return self

    def measure(self, j: int, cbit: Optional[int] = None):
        """
        Measure the j-th qubit.

        Args:
            j: Index of qubit to measure
            cbit: Optional classical bit to store the measurement result

        Returns:
            The state after measurement (collapsed)
        """
        print(f"-> Measuring qubit {j}")
        # compute the probability of 0
        prob_0 = (
            self.state.filter(lambda s: not s[0][j])
            .smap(lambda _, a: abs(a) ** 2)
            .sum()
            .real
        )  # take the real component (the imaginary component is 0)

        print(f"\tProbability of 0: {prob_0:.3f}")
        measurement = int(random.random() >= prob_0)
        print(f"\tMeasurement result: {measurement}")

        if cbit is not None:
            self.cbits[cbit] = int(measurement)

        if measurement == 0:
            # Collapse to 0 state
            self.state = self.state.smap(lambda b, a: (b, a * (not b[j]))).smap(
                lambda b, a: (b, a / sqrt(prob_0))
            )
        else:
            # Collapse to 1 state
            self.state = self.state.smap(lambda b, a: (b, a * b[j])).smap(
                lambda b, a: (b, a / sqrt(1.0 - prob_0))
            )
        return self

    def __str__(self):
        """
        Return a string representation of the quantum state.

        Format: Each bitstring with its corresponding amplitude.
        """
        self.state = self.state.sorted(key=lambda x: x[0].to01())

        result = "Quantum state:\n" + "\n".join(
            [f"{b.to01()}: {a:.2f}" for b, a in self.state]
        )

        # Add classical register values if they exist
        if self.n_bits > 0:
            result += f"\n\nClassical register: {self.cbits}"

        return result
