import numpy as np
from scipy.linalg import cho_solve


def fast_mass_springs_step_dense(
    V, E, k, b, delta_t, fext, r, M, A, C, prefactorization, Uprev, Ucur
):
    """Advance the cloth one time step with the dense local-global solver.

    Implements the "fast mass springs" iteration of Liu et al. 2013. Each
    iteration alternates a cheap *local* step (project each spring vector onto
    its rest length) and a *global* step (one linear solve with the prefactored
    matrix ``Q``).

    The auxiliary right-hand side (constant within the step) is::

        y = (1/Δt²) M (2 Ucur - Uprev) + fext + w Cᵀ (C V)      (w = 1e10)

    Then repeat ~50 times::

        d[e]  = r[e] * normalize((A Unext)[e])     # local
        rhs   = k Aᵀ d + y
        Unext = solve(Q, rhs)                      # global (cho_solve)

    Parameters
    ----------
    V : (n, 3)        rest positions (used by the pinning term ``w Cᵀ C V``).
    E : (m, 2)        spring edges.
    k : float         stiffness.
    b : (c,)          pinned indices (pinning is enforced through ``C``).
    delta_t : float   time step.
    fext : (n, 3)     external force per vertex (e.g. gravity).
    r : (m,)          rest lengths.
    M : (n, n)        mass matrix.
    A : (m, n)        signed incidence matrix.
    C : (c, n)        pinning selector.
    prefactorization  Cholesky factor of ``Q`` (use ``cho_solve``).
    Uprev, Ucur : (n, 3)   positions at the previous and current time steps.

    Returns
    -------
    Unext : (n, 3)    positions at the next time step.
    """
    # TODO: build y, then run the 50-iteration local-global loop with cho_solve.
    raise NotImplementedError("Implement fast_mass_springs_step_dense")
