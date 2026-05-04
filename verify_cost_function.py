"""
Verify the VQE cost function logic locally using AerSimulator.
AerSimulator provides the same shots-based interface as IonQ's backend,
so if this works, the logic is correct for IonQ too.
"""
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_aer import AerSimulator

# ── Ansatz ──────────────────────────────────────────────────────────
def hardware_efficient_ansatz(num_qubits, num_layers):
    theta = ParameterVector("θ", num_qubits * 2 * num_layers)
    ansatz = QuantumCircuit(num_qubits)
    param_idx = 0
    for layer in range(num_layers):
        for q in range(num_qubits):
            ansatz.ry(theta[param_idx], q);  param_idx += 1
            ansatz.rz(theta[param_idx], q);  param_idx += 1
        for q in range(num_qubits - 1):
            ansatz.cx(q, q + 1)
    return ansatz, theta

# ── Hamiltonian ─────────────────────────────────────────────────────
H = SparsePauliOp("XY")

# Exact ground state energy for reference
eigvals = np.linalg.eigvalsh(Operator(H).data)
print(f"Exact eigenvalues : {np.round(eigvals, 6)}")
print(f"Exact ground state: {eigvals[0]:.6f}\n")

# ── Backend (local shots simulator — same interface as IonQ) ───────
backend = AerSimulator()
ansatz, theta = hardware_efficient_ansatz(2, num_layers=2)
nshots = 8192

# ── Expectation value from counts ──────────────────────────────────
def compute_pauli_expectation(bound_circuit, pauli_label, backend, shots):
    """Measure <pauli_label> for a bound circuit on a shots-based backend."""
    qc = bound_circuit.copy()
    n = qc.num_qubits

    # Basis-change gates so Z-measurement reads the Pauli eigenbasis
    for i, p in enumerate(pauli_label):
        qubit = n - 1 - i          # pauli_label[0] → highest qubit
        if p == 'X':
            qc.h(qubit)
        elif p == 'Y':
            qc.sdg(qubit)
            qc.h(qubit)
    qc.measure_all()

    qc_t = transpile(qc, backend=backend, optimization_level=1)
    job = backend.run(qc_t, shots=shots)
    counts = job.result().get_counts()

    expval = 0.0
    total = sum(counts.values())
    for bitstring, count in counts.items():
        parity = sum(int(bitstring[i]) for i, p in enumerate(pauli_label) if p != 'I')
        expval += ((-1) ** (parity % 2)) * count / total
    return expval


def cost_func(params):
    """VQE cost: returns <H> for the given variational parameters."""
    bound = ansatz.assign_parameters(dict(zip(theta, params)))

    energy = 0.0
    for label, coeff in zip(H.paulis.to_labels(), H.coeffs):
        if all(c == 'I' for c in label):
            energy += coeff.real
        else:
            energy += coeff.real * compute_pauli_expectation(bound, label, backend, nshots)
    return energy

# ── Quick sanity check: single evaluation ──────────────────────────
test_params = np.zeros(len(theta))
print(f"Cost at params=0 : {cost_func(test_params):.4f}  (expect ~0 for |00⟩)")

# ── Run VQE optimization ───────────────────────────────────────────
np.random.seed(42)
best_result = None

for trial in range(3):
    x0 = np.random.uniform(0, 2 * np.pi, size=len(theta))
    res = minimize(cost_func, x0, method="cobyla", options={"maxiter": 300})
    tag = "  ← best so far" if (best_result is None or res.fun < best_result.fun) else ""
    print(f"Trial {trial}: energy = {res.fun:.6f}{tag}")
    if best_result is None or res.fun < best_result.fun:
        best_result = res

print(f"\n{'='*50}")
print(f"Optimized ground state energy : {best_result.fun:.6f}")
print(f"Exact ground state energy     : {eigvals[0]:.6f}")
print(f"Error                         : {abs(best_result.fun - eigvals[0]):.6f}")
print(f"Optimal parameters θ          : {np.round(best_result.x, 4)}")
print(f"Optimization success          : {best_result.success}")
