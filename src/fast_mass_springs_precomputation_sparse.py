import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu

from src.signed_incidence_matrix_sparse import signed_incidence_matrix_sparse


def fast_mass_springs_precomputation_sparse(V, E, k, m, b, delta_t):
    """Sparse counterpart of :func:`fast_mass_springs_precomputation_dense`.

    Build the same matrices using ``scipy.sparse`` storage and return a sparse
    LU factorization of ``Q`` so the per-iteration global solve is fast even for
    large networks.

    Returns
    -------
    r : (m,) float array     rest lengths.
    M : sparse (n, n)        diagonal mass matrix.
    A : sparse (m, n)        signed incidence matrix.
    C : sparse (c, n)        pinning selector.
    prefactorization : scipy.sparse.linalg.SuperLU
        Factorization of CSC ``Q = k Aᵀ A + (1/Δt²) M + w Cᵀ C`` (``w = 1e10``).
        The step function solves with ``prefactorization.solve(rhs)``.
    """
    # TODO: mirror the dense version with sparse matrices (sp.diags, the sparse
    # signed incidence, a sparse C), form Q, convert to CSC and call splu(Q).
    raise NotImplementedError("Implement fast_mass_springs_precomputation_sparse")
