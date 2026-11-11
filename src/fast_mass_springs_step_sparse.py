import numpy as np


def fast_mass_springs_step_sparse(
    V, E, k, b, delta_t, fext, r, M, A, C, prefactorization, Uprev, Ucur
):
    """Sparse counterpart of :func:`fast_mass_springs_step_dense`.

    Uses the same ``y`` as the dense step, starts from ``Unext = Ucur.copy()``
    and runs exactly 50 local-global iterations. ``M``, ``A`` and ``C`` are
    sparse, and the global solve uses the sparse LU factorization
    (``prefactorization.solve(rhs)`` instead of ``cho_solve``).

    Returns
    -------
    Unext : (n, 3)   positions at the next time step.
    """
    # TODO: same as the dense step (start from Unext = Ucur.copy(), exactly 50
    # iterations), but solve with prefactorization.solve(rhs).
    raise NotImplementedError("Implement fast_mass_springs_step_sparse")
