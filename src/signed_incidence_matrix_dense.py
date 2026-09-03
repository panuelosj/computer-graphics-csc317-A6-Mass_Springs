import numpy as np


def signed_incidence_matrix_dense(n, E):
    """Build the dense signed incidence matrix ``A`` of a spring network.

    Parameters
    ----------
    n : int
        Number of vertices (point masses).
    E : (m, 2) int array
        Edge list. Row ``e`` connects vertices ``E[e, 0]`` and ``E[e, 1]``.

    Returns
    -------
    A : (m, n) float64 ndarray
        ``A[e, E[e, 0]] = +1`` and ``A[e, E[e, 1]] = -1`` for each edge ``e``;
        all other entries are zero. Then ``(A @ U)[e] = U[E[e,0]] - U[E[e,1]]``
        is the spring vector of edge ``e``.
    """
    # TODO: allocate an (m, n) array of zeros and set +1/-1 for each edge.
    raise NotImplementedError("Implement signed_incidence_matrix_dense")
