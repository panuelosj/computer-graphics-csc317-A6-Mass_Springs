import numpy as np
import scipy.sparse as sp


def signed_incidence_matrix_sparse(n, E):
    """Build the sparse signed incidence matrix ``A`` of a spring network.

    Identical in meaning to :func:`signed_incidence_matrix_dense` but returns a
    ``scipy.sparse`` matrix built from a triplet (COO) list rather than a dense
    array, so it scales to large networks.

    Parameters
    ----------
    n : int
        Number of vertices (point masses).
    E : (m, 2) int array
        Edge list.

    Returns
    -------
    A : scipy.sparse matrix, shape (m, n)
        ``A[e, E[e, 0]] = +1`` and ``A[e, E[e, 1]] = -1`` for each edge ``e``.

    Notes
    -----
    Build the matrix from triplets (row, col, value) and a single
    ``scipy.sparse.coo_matrix(...)`` call. Do NOT assign into the sparse matrix
    element by element.
    """
    # TODO: build (rows, cols, vals) triplet arrays and construct a coo_matrix.
    raise NotImplementedError("Implement signed_incidence_matrix_sparse")
