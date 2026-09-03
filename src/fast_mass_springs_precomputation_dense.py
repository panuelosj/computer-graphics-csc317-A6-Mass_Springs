import numpy as np
from scipy.linalg import cho_factor

from src.signed_incidence_matrix_dense import signed_incidence_matrix_dense


def fast_mass_springs_precomputation_dense(V, E, k, m, b, delta_t):
    """Precompute the (constant) quantities of the fast mass-spring solver (dense).

    The "global" step of the local-global solver repeatedly solves a linear
    system ``Q x = rhs`` where the system matrix ``Q`` never changes. Build
    ``Q`` once here and factorize it so every later solve is cheap.

    Parameters
    ----------
    V : (n, 3) float array   rest/initial vertex positions.
    E : (m, 2) int array     spring edge list.
    k : float                spring stiffness.
    m : (n,) float array     per-vertex masses.
    b : (c,) int array       indices of pinned (fixed) vertices.
    delta_t : float          time step.

    Returns
    -------
    r : (m,) float array     rest length of each spring (``|V[i] - V[j]|``).
    M : (n, n) ndarray       diagonal mass matrix ``diag(m)``.
    A : (m, n) ndarray       signed incidence matrix.
    C : (c, n) ndarray       pinning selector: ``C[j, b[j]] = 1``.
    prefactorization : object
        Cholesky factorization of
        ``Q = k Aᵀ A + (1/Δt²) M + w Cᵀ C``  (with ``w = 1e10``),
        returned by ``scipy.linalg.cho_factor``. The step function consumes it
        via ``scipy.linalg.cho_solve(prefactorization, rhs)``.
    """
    # TODO:
    #   1. M = diag(m); r = per-edge rest lengths.
    #   2. A = signed_incidence_matrix_dense(n, E).
    #   3. C = pinning selector (one row per pinned vertex).
    #   4. Q = k AᵀA + (1/Δt²) M + w CᵀC  with w = 1e10.
    #   5. prefactorization = cho_factor(Q); return (r, M, A, C, prefactorization).
    raise NotImplementedError("Implement fast_mass_springs_precomputation_dense")
