/agent ok going back to GSEE of a two qubit system. Say I want to calculate GSEE for H = X x Y and also for H_new=U H U_dagger, where U is a combination of Ry(theta1,0) Ry(theta2,1) and a CNOT. I have found many suggestions for a function that generates parametric ansatz, which ansatz function would you suggest for the case I described?

I'd need to understand your specific requirements better to make the best recommendation. Let me ask a few clarifying questions:

1. Goal of the ansatz: Are you trying to:
◦  Prepare a state that minimizes the ground state energy (VQE-style)?
◦  Explore how different unitaries affect GSEE?
◦  Something else?
2. Expressivity vs. simplicity: Do you prefer:
◦  Minimal ansatz (just enough to capture the physics you care about)?
◦  Highly expressive ansatz (more parameters, more flexibility)?
3. Rotation pattern: For your U = Ry(θ₁, 0) Ry(θ₂, 1) CNOT, do you want:
◦  This exact structure (2 single-qubit rotations + CNOT)?
◦  Repeated layers of this pattern?
◦  Different rotation axes (X, Y, Z) at different positions?
4. Hardware efficiency: Are you concerned about:
◦  Minimizing circuit depth?
◦  Working with specific hardware constraints?

General recommendation for your case: Since you have a 2-qubit system with a specified structure (Ry rotations + CNOT), I'd suggest:
•  Hardware-efficient ansatz: Alternating layers of single-qubit rotations (Ry or RyRzRy) followed by CNOT. This is simple, interpretable, and you can control depth.
•  Alternating ansatz: If you want more expressivity, add more layers: (Ry rotations + CNOT) repeated k times.

Can you clarify what you're trying to achieve with this ansatz? That will help me suggest the most suitable approach.

Me
1. I will use it for calculating GSEE with QVE. 2. The simplest ansatz that will still allow me to calculate GSEE with maybe two decimals at the end 3. I want ansatz that would work if a produce slight variations of the rotations and the CNOT 4.Eventually I will send my code to a real QC so I need to be careful about qc time 
Based on your requirements (VQE, ~2 decimal precision, robustness to slight variations, minimal QC time), here's my recommendation:

Suggested ansatz: single-layer hardware-efficient ansatz (HEA)
python

def ansatz(params, circuit, qubits):
    # Rotation layer 1
    circuit.ry(params[0], qubits[0])
    circuit.rz(params[1], qubits[0])
    circuit.ry(params[2], qubits[1])
    circuit.rz(params[3], qubits[1])
    # Entangling layer
    circuit.cx(qubits[0], qubits[1])
    # Rotation layer 2
    circuit.ry(params[4], qubits[0])
    circuit.rz(params[5], qubits[0])
    circuit.ry(params[6], qubits[1])
    circuit.rz(params[7], qubits[1])
    return circuit
    
Why this over pure Ry + CNOT: For H = X⊗Y, the ground states have complex amplitudes (e.g. |+⟩|-i⟩). An ansatz built only from Ry + CNOT produces real-amplitude states and cannot reach the true ground state. You need at least one Rz (or Rx) to access complex phases. This is a crucial correction even though your U only uses Ry—because U applied to |00⟩ gives a real state, but the ground state of X⊗Y is not real.

Why it fits your 4 constraints:

1. VQE-ready: 8 parameters is enough to span the states needed for 2-qubit ground states of Pauli Hamiltonians to high precision. One CNOT is sufficient for generic 2-qubit entanglement when sandwiched between single-qubit rotations (the KAK-like structure).
what is the reference for the Hardware Efficient Ansatz? WHere does it come from?
Canonical reference

Me: The Hardware-Efficient Ansatz (HEA) was introduced in:

Kandala, A., Mezzacapo, A., Temme, K., Takita, M., Brink, M., Chow, J. M., & Gambetta, J. M. (2017). "Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets." Nature 549, 242–246.

•  DOI: 10.1038/nature23879
•  arXiv: 1704.05018

Context and motivation

This paper came out of the IBM Quantum group. Prior to it, VQE work (Peruzzo et al. 2014, McClean et al. 2016) often used chemistry-inspired ansätze like UCCSD (Unitary Coupled Cluster Singles and Doubles), which are physically motivated but require deep circuits with many non-native gates—prohibitive on noisy near-term hardware.

Kandala et al.'s key idea was the opposite: instead of starting from the chemistry and compiling down to hardware, start from the hardware's native gate set and connectivity and build up a parameterized circuit. Specifically:

•  Use only the single-qubit rotations the device can execute natively (e.g. U3 on IBM superconducting chips).
•  Use only the entangling gate(s) the hardware supports (e.g. cross-resonance / CNOT between physically connected qubits).
•  Stack "rotation layer + entangling layer" blocks, parameterized by rotation angles.

They used this to compute ground-state energies of H₂, LiH, and BeH₂ on IBM's superconducting processors, and it became the standard template for NISQ-era VQE.

Related / earlier ideas

•  The general notion of variational quantum circuits predates HEA: Peruzzo et al. 2014 (Nat. Commun. 5, 4213) introduced VQE itself.
•  McClean et al. 2016 (New J. Phys. 18, 023023) formalized the variational framework.
•  "Brick-wall" and "checkerboard" parameterized circuits in condensed-matter/tensor-network literature are structurally similar.

But the term "hardware-efficient ansatz" and its widespread adoption in the VQE community trace specifically to Kandala et al. 2017.

Me: 
I did not see the ansatz in the paper written exactly as you did but probably I missed it. Can you tell me where did you find that specific form of the ansatz? Also in the paper they say they optimized for IBM because some gates were native, does it mean that if I run for example in IonQ the ansatz form should be different?

Honest correction on the ansatz form

You're right to push back—the exact form I wrote is not literally in Kandala et al. 2017. What I gave you is a common pedagogical/simplified version of HEA that appears in tutorials (Qiskit's EfficientSU2, PennyLane's BasicEntanglerLayers, textbooks), which was inspired by that paper but isn't a verbatim quote from it.

What's actually in Kandala et al. 2017 (see Methods and the circuit diagram in Fig. 1):

•  Each single-qubit block is a full Euler decomposition of an arbitrary SU(2) rotation, written as U(θ, φ, λ) — effectively a Z–Y–Z (or Z-X-Z) sequence, i.e. 3 angles per qubit per layer, not 2.
•  The entangler is not a CNOT but a set of cross-resonance-driven entangling gates native to IBM's superconducting transmons, applied across the device's fixed connectivity graph.
•  The circuit is d layers of: (rotation block) → (entangling block), with a final rotation block. The depth d is a variational hyperparameter.

So I conflated "HEA as a concept/template" with "the specific circuit in the 2017 paper." The concept (native gates + depth-d alternating rotation/entangling layers) is from Kandala et al.; the Ry-Rz-CNOT form I gave is a simplified instantiation.

Does the ansatz need to change for IonQ?

Yes, in principle—but the high-level template stays the same. The whole point of "hardware-efficient" is that the ansatz tracks the device's native gate set and connectivity. For IonQ:

•  Native single-qubit gates: GPi(φ) and GPi2(φ) (and Rz as a virtual/frame rotation, essentially free).
•  Native 2-qubit gate: the Mølmer–Sørensen (MS) gate, not CNOT. IonQ also exposes a parameterized version (ZZ(θ) / partial MS).
•  Connectivity: all-to-all (trapped ions), so you don't have to worry about routing.

A truly hardware-efficient ansatz on IonQ would look like:
python

# Conceptual IonQ-native HEA layer (2 qubits)
for q in qubits:
    GPi2(phi_a, q)       # or an Rz-GPi2-Rz Euler decomposition
    Rz(phi_b, q)         # virtual, free
    GPi2(phi_c, q)
MS(theta, q0, q1)        # native entangler
# ... repeat for d layers

Practical answer for your situation

If you write the ansatz with Ry/Rz/CNOT and send it to IonQ:

•  The transpiler will compile CNOT → MS + single-qubit rotations automatically. It works, but you spend more gate time than necessary because each CNOT becomes 1 MS + several single-qubit gates.
•  For a 2-qubit problem with ~1 CNOT, the overhead is small—probably fine for getting 2-decimal precision.
•  For deeper circuits, writing the ansatz directly in IonQ's native gates (MS instead of CNOT) saves real QC time and reduces error.

Bottom line: the template (alternating rotation/entangling layers of native gates) is universal; the specific gates should match whatever platform you run on if you want to be maximally hardware-efficient. For a small 2-qubit study the difference is mostly cosmetic and the compiler handles it, but for anything bigger you'd want to re-express the entangler (and possibly the single-qubit blocks) in the target hardware's native set.

Me: In your answer for native IonQ, I see GPi2 and MS, are those instructions that qiskit will understand?


Short answer: not out of the box

Standard Qiskit (qiskit) does not know about GPi, GPi2, or MS gates. Its built-in gate library is centered on U/U3, RX/RY/RZ, CX, CZ, etc.

To use IonQ native gates from Qiskit, you need the qiskit-ionq provider (IonQ's official Qiskit plugin):
bash

pip install qiskit-ionq

This package adds Qiskit-compatible gate classes:
python

from qiskit_ionq import GPIGate, GPI2Gate, MSGate, ZZGate

qc.append(GPI2Gate(phi), [0])
qc.append(MSGate(phi0, phi1, theta), [0, 1])

When you submit, you can tell the IonQ backend to accept native gates directly:
python

from qiskit_ionq import IonQProvider

provider = IonQProvider(token="YOUR_TOKEN")
backend = provider.get_backend("ionq_qpu")   # or a simulator
job = backend.run(qc, gateset="native")      # key option

If you omit gateset="native" (or use a plain CX/U3 circuit), IonQ will transpile your circuit to the native set on their side—you don't have to do it yourself. That's the easiest path for a small 2-qubit VQE: write the circuit in standard Qiskit gates, submit to IonQ, and let their compiler handle the conversion.

Practical recommendation for your VQE

•  Easiest / portable: write the ansatz in generic Qiskit gates (RY, RZ, CX). Run on IBM, IonQ, or simulators without changes. Fine for 2 decimals on a 2-qubit problem.
•  Maximally hardware-efficient on IonQ: install qiskit-ionq, build the ansatz with GPI2Gate / MSGate, and submit with gateset="native". Worth it for deeper circuits; marginal benefit for your small system.
