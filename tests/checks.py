"""Unit checks for Assignment 6 (Mass-Springs).

Each check exercises one function in ``src/`` against the golden fixtures in
``tests/golden/a6_golden.npz``. The same checks are used by ``run_tests.py``
(for students) and by the grader. Marks per check mirror the marking scheme.

The step checks build the ``prefactorization`` object themselves (using the same
convention as the reference precomputation) so they test the step solver in
isolation from the precomputation function:

* dense  -> ``scipy.linalg.cho_factor(Q)``  (consumed with ``cho_solve``)
* sparse -> ``scipy.sparse.linalg.splu(Q_csc)``  (consumed with ``.solve``)
"""

import os

import numpy as np
import scipy.sparse as sp
from scipy.linalg import cho_factor
from scipy.sparse.linalg import splu

from cgcommon.testkit import Check, fixture_path

_GOLDEN = None


def golden():
    global _GOLDEN
    if _GOLDEN is None:
        path = fixture_path(
            os.path.join(os.path.dirname(__file__), "golden", "a6_golden.npz")
        )
        _GOLDEN = np.load(path)
    return _GOLDEN


def _reconstruct_Q(g):
    """Q = k AᵀA + (1/Δt²) M + w CᵀC from the golden dense matrices."""
    k = float(g["k"])
    delta_t = float(g["delta_t"])
    M, A, C = g["M"], g["A"], g["C"]
    w = 1e10
    return k * (A.T @ A) + (1.0 / (delta_t * delta_t)) * M + w * (C.T @ C)


def _reconstruct_chain_Q(g):
    """Same as :func:`_reconstruct_Q` for the second (chain) step fixture."""
    k = float(g["chain_k"])
    delta_t = float(g["chain_dt"])
    M, A, C = g["chain_M"], g["chain_A"], g["chain_C"]
    w = 1e10
    return k * (A.T @ A) + (1.0 / (delta_t * delta_t)) * M + w * (C.T @ C)


# --- individual checks ------------------------------------------------------

def check_signed_incidence_matrix_dense():
    from src.signed_incidence_matrix_dense import signed_incidence_matrix_dense
    g = golden()
    A = np.asarray(signed_incidence_matrix_dense(int(g["si_n"]), g["si_E"]))
    assert A.shape == g["si_A"].shape, (
        f"signed_incidence_matrix_dense: wrong shape {A.shape}, "
        f"expected {g['si_A'].shape}"
    )
    assert np.array_equal(A, g["si_A"]), (
        "signed_incidence_matrix_dense: entries differ from reference"
    )


def check_signed_incidence_matrix_sparse():
    from src.signed_incidence_matrix_sparse import signed_incidence_matrix_sparse
    g = golden()
    A = signed_incidence_matrix_sparse(int(g["si_n"]), g["si_E"])
    assert sp.issparse(A), (
        "signed_incidence_matrix_sparse: must return a scipy.sparse matrix"
    )
    dense = A.toarray()
    assert dense.shape == g["si_A_sparse"].shape, (
        f"signed_incidence_matrix_sparse: wrong shape {dense.shape}"
    )
    assert np.array_equal(dense, g["si_A_sparse"]), (
        "signed_incidence_matrix_sparse: entries differ from reference"
    )


def check_fast_mass_springs_precomputation_dense():
    from src.fast_mass_springs_precomputation_dense import (
        fast_mass_springs_precomputation_dense,
    )
    g = golden()
    r, M, A, C, pre = fast_mass_springs_precomputation_dense(
        g["V"], g["E"], float(g["k"]), g["m"], g["b"], float(g["delta_t"])
    )
    r = np.asarray(r)
    assert np.allclose(r, g["r"]), "precomputation_dense: rest lengths r are wrong"
    A = np.asarray(A)
    assert np.array_equal(A, g["A"]), "precomputation_dense: A incorrect"
    assert np.allclose(np.asarray(M), g["M"]), "precomputation_dense: M incorrect"
    assert np.allclose(np.asarray(C), g["C"]), "precomputation_dense: C incorrect"
    # Q must be symmetric positive definite.
    Q = (float(g["k"]) * (A.T @ A)
         + (1.0 / (float(g["delta_t"]) ** 2)) * np.asarray(M)
         + 1e10 * (np.asarray(C).T @ np.asarray(C)))
    assert np.allclose(Q, Q.T), "precomputation_dense: Q is not symmetric"
    assert np.allclose(Q, _reconstruct_Q(g)), "precomputation_dense: Q differs"
    np.linalg.cholesky(Q)  # raises if not positive definite
    # The returned prefactorization must solve Q x = rhs.
    from scipy.linalg import cho_solve
    rhs = np.ones((g["V"].shape[0], 3))
    x = cho_solve(pre, rhs)
    assert np.allclose(Q @ x, rhs, atol=1e-4), (
        "precomputation_dense: prefactorization does not solve Q x = rhs"
    )


def check_fast_mass_springs_precomputation_sparse():
    from src.fast_mass_springs_precomputation_sparse import (
        fast_mass_springs_precomputation_sparse,
    )
    g = golden()
    r, M, A, C, pre = fast_mass_springs_precomputation_sparse(
        g["V"], g["E"], float(g["k"]), g["m"], g["b"], float(g["delta_t"])
    )
    assert np.allclose(np.asarray(r), g["r"]), (
        "precomputation_sparse: rest lengths r are wrong"
    )
    assert sp.issparse(A), "precomputation_sparse: A must be sparse"
    assert sp.issparse(M), "precomputation_sparse: M must be sparse"
    assert sp.issparse(C), "precomputation_sparse: C must be sparse"
    Ad = A.toarray()
    assert np.array_equal(Ad, g["A"]), "precomputation_sparse: A differs from dense"
    assert np.allclose(M.toarray(), g["M"]), "precomputation_sparse: M differs"
    assert np.allclose(C.toarray(), g["C"]), "precomputation_sparse: C differs"
    # Sparse Q must agree with the dense reference Q.
    w = 1e10
    Q = (float(g["k"]) * (A.T @ A)
         + (1.0 / (float(g["delta_t"]) ** 2)) * M
         + w * (C.T @ C)).toarray()
    assert np.allclose(Q, _reconstruct_Q(g)), (
        "precomputation_sparse: Q differs from dense reference"
    )
    # prefactorization must solve the system.
    rhs = np.ones((g["V"].shape[0], 3))
    x = pre.solve(rhs)
    assert np.allclose(Q @ x, rhs, atol=1e-4), (
        "precomputation_sparse: prefactorization does not solve Q x = rhs"
    )


def _run_steps(step_fn, g, M, A, C, prefactorization, n_steps):
    V = g["V"]
    fext = g["fext"]
    Uprev = V.copy()
    Ucur = V.copy()
    for _ in range(n_steps):
        Unext = np.asarray(step_fn(
            V, g["E"], float(g["k"]), g["b"], float(g["delta_t"]), fext,
            g["r"], M, A, C, prefactorization, Uprev, Ucur,
        ))
        Uprev = Ucur
        Ucur = Unext
    return Ucur


def check_fast_mass_springs_step_dense():
    from src.fast_mass_springs_step_dense import fast_mass_springs_step_dense
    g = golden()
    Q = _reconstruct_Q(g)
    pre = cho_factor(Q)
    M, A, C = g["M"], g["A"], g["C"]

    # Single step from rest should match the reference exactly (tol).
    one = np.asarray(fast_mass_springs_step_dense(
        g["V"], g["E"], float(g["k"]), g["b"], float(g["delta_t"]), g["fext"],
        g["r"], M, A, C, pre, g["V"], g["V"],
    ))
    assert one.shape == g["one_Unext"].shape, "step_dense: wrong output shape"
    assert np.allclose(one, g["one_Unext"], atol=1e-6), (
        "step_dense: single-step result differs from reference"
    )

    # Multi-step trajectory.
    final = _run_steps(
        fast_mass_springs_step_dense, g, M, A, C, pre, int(g["n_steps"])
    )
    assert np.allclose(final, g["step_Unext"], atol=1e-6), (
        "step_dense: multi-step trajectory differs from reference"
    )
    # Pinned vertices stay (approximately) fixed.
    bidx = g["b"]
    assert np.allclose(final[bidx], g["V"][bidx], atol=1e-3), (
        "step_dense: pinned vertices moved"
    )

    # Second fixture: a longer, stiffer chain whose Ucur is displaced on the
    # pinned rows too. 50 iterations do not converge on it, so it checks the
    # exact iterate: a start other than Unext = Ucur, any count other than 50,
    # or a pinning term built from Ucur instead of V fails here.
    Qc = _reconstruct_chain_Q(g)
    prec = cho_factor(Qc)
    out = np.asarray(fast_mass_springs_step_dense(
        g["chain_V"], g["chain_E"], float(g["chain_k"]), g["chain_b"],
        float(g["chain_dt"]), g["chain_fext"], g["chain_r"],
        g["chain_M"], g["chain_A"], g["chain_C"], prec,
        g["chain_Uprev"], g["chain_Ucur"],
    ))
    assert np.allclose(out, g["chain_Unext"], atol=1e-6), (
        "step_dense: chain step differs. Start at Unext = Ucur, run exactly "
        "50 local-global iterations, and pin to the rest positions V."
    )


def check_fast_mass_springs_step_sparse():
    from src.fast_mass_springs_step_sparse import fast_mass_springs_step_sparse
    g = golden()
    Q = _reconstruct_Q(g)
    pre = splu(sp.csc_matrix(Q))
    M = sp.diags(np.diag(g["M"])).tocsr()
    A = sp.csr_matrix(g["A"])
    C = sp.csr_matrix(g["C"])

    one = np.asarray(fast_mass_springs_step_sparse(
        g["V"], g["E"], float(g["k"]), g["b"], float(g["delta_t"]), g["fext"],
        g["r"], M, A, C, pre, g["V"], g["V"],
    ))
    assert np.allclose(one, g["one_Unext"], atol=1e-6), (
        "step_sparse: single-step result differs from reference"
    )

    final = _run_steps(
        fast_mass_springs_step_sparse, g, M, A, C, pre, int(g["n_steps"])
    )
    assert np.allclose(final, g["step_Unext"], atol=1e-6), (
        "step_sparse: multi-step trajectory differs from reference (and from dense)"
    )
    bidx = g["b"]
    assert np.allclose(final[bidx], g["V"][bidx], atol=1e-3), (
        "step_sparse: pinned vertices moved"
    )

    # Second fixture: the discriminating chain (see the dense check).
    Qc = _reconstruct_chain_Q(g)
    prec = splu(sp.csc_matrix(Qc))
    Mc = sp.diags(np.diag(g["chain_M"])).tocsr()
    Ac = sp.csr_matrix(g["chain_A"])
    Cc = sp.csr_matrix(g["chain_C"])
    out = np.asarray(fast_mass_springs_step_sparse(
        g["chain_V"], g["chain_E"], float(g["chain_k"]), g["chain_b"],
        float(g["chain_dt"]), g["chain_fext"], g["chain_r"],
        Mc, Ac, Cc, prec, g["chain_Uprev"], g["chain_Ucur"],
    ))
    assert np.allclose(out, g["chain_Unext"], atol=1e-6), (
        "step_sparse: chain step differs. Start at Unext = Ucur, run exactly "
        "50 local-global iterations, and pin to the rest positions V."
    )


def get_checks():
    """Return the ordered list of checks for this assignment."""
    return [
        Check("fast_mass_springs_precomputation_dense", 19,
              check_fast_mass_springs_precomputation_dense,
              "builds r, M, A, C and an SPD prefactored Q (dense)"),
        Check("fast_mass_springs_precomputation_sparse", 19,
              check_fast_mass_springs_precomputation_sparse,
              "same as dense using scipy.sparse + sparse factorization"),
        Check("fast_mass_springs_step_dense", 19,
              check_fast_mass_springs_step_dense,
              "local-global time step (dense)"),
        Check("fast_mass_springs_step_sparse", 19,
              check_fast_mass_springs_step_sparse,
              "local-global time step (sparse)"),
        Check("signed_incidence_matrix_dense", 12,
              check_signed_incidence_matrix_dense,
              "signed incidence matrix (dense)"),
        Check("signed_incidence_matrix_sparse", 12,
              check_signed_incidence_matrix_sparse,
              "signed incidence matrix (sparse)"),
    ]
