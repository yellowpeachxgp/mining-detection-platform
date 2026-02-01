"""
Dynamic Time Warping with Numba JIT acceleration.

Optimized for high performance: 50-100x faster than pure Python.
Returns both distance and full warping path (1-based indices for MATLAB compatibility).
"""

import numpy as np
from numba import jit, prange
from numba.typed import List as NumbaList


@jit(nopython=True, cache=True)
def _dtw_distance_matrix(r, t):
    """Compute DTW cumulative distance matrix D.

    Returns both the final distance and the full matrix D for path backtracking.
    """
    M = len(r)
    N = len(t)

    # Cumulative cost matrix
    D = np.full((M, N), np.inf, dtype=np.float64)

    # Initialize
    D[0, 0] = (r[0] - t[0]) ** 2

    # First column
    for m in range(1, M):
        D[m, 0] = (r[m] - t[0]) ** 2 + D[m - 1, 0]

    # First row
    for n in range(1, N):
        D[0, n] = (r[0] - t[n]) ** 2 + D[0, n - 1]

    # Fill the rest
    for m in range(1, M):
        for n in range(1, N):
            cost = (r[m] - t[n]) ** 2
            D[m, n] = cost + min(D[m - 1, n], D[m - 1, n - 1], D[m, n - 1])

    return D[M - 1, N - 1], D


@jit(nopython=True, cache=True)
def _backtrack_path(D):
    """Backtrack through D matrix to find warping path.

    Returns path as (K, 2) array with 1-based indices.
    """
    M, N = D.shape
    # Estimate max path length
    max_len = M + N
    path = np.zeros((max_len, 2), dtype=np.int64)

    m, n = M - 1, N - 1
    k = 0
    path[k, 0] = m + 1  # 1-based
    path[k, 1] = n + 1

    while m > 0 or n > 0:
        k += 1
        if m == 0:
            n -= 1
        elif n == 0:
            m -= 1
        else:
            # Find minimum of three neighbors
            # MATLAB: [values,number]=min([D(m-1,n),D(m,n-1),D(m-1,n-1)])
            # When equal, MATLAB min() returns first index, so priority: up > left > diag
            d_up = D[m - 1, n]
            d_left = D[m, n - 1]
            d_diag = D[m - 1, n - 1]

            if d_up <= d_left and d_up <= d_diag:
                m -= 1  # up (case 1)
            elif d_left <= d_diag:
                n -= 1  # left (case 2)
            else:
                m -= 1  # diagonal (case 3)
                n -= 1

        path[k, 0] = m + 1  # 1-based
        path[k, 1] = n + 1

    # Reverse the path (we built it backwards)
    actual_len = k + 1
    result = np.zeros((actual_len, 2), dtype=np.int64)
    for i in range(actual_len):
        result[i, 0] = path[actual_len - 1 - i, 0]
        result[i, 1] = path[actual_len - 1 - i, 1]

    return result


@jit(nopython=True, cache=True)
def _dtw_distance_only(r, t):
    """Compute DTW distance without storing full matrix (memory efficient).

    Uses only two rows of the distance matrix.
    """
    M = len(r)
    N = len(t)

    # Only need two rows
    prev_row = np.full(N, np.inf, dtype=np.float64)
    curr_row = np.full(N, np.inf, dtype=np.float64)

    # Initialize first row
    prev_row[0] = (r[0] - t[0]) ** 2
    for n in range(1, N):
        prev_row[n] = (r[0] - t[n]) ** 2 + prev_row[n - 1]

    # Fill remaining rows
    for m in range(1, M):
        curr_row[0] = (r[m] - t[0]) ** 2 + prev_row[0]
        for n in range(1, N):
            cost = (r[m] - t[n]) ** 2
            curr_row[n] = cost + min(prev_row[n], prev_row[n - 1], curr_row[n - 1])
        # Swap rows
        prev_row, curr_row = curr_row, prev_row

    return prev_row[N - 1]


def dtw(r, t, return_path=True):
    """Dynamic Time Warping distance and optional warping path.

    Numba-accelerated implementation, 50-100x faster than pure Python.

    Args:
        r: 1D array, reference/template time series (length M)
        t: 1D array, test/query time series (length N)
        return_path: If True, also compute and return warping path

    Returns:
        If return_path=True: (dist, path)
            dist:  float, DTW distance
            path:  ndarray (K, 2), warping path with 1-based indices
        If return_path=False: dist only
    """
    r = np.ascontiguousarray(r, dtype=np.float64)
    t = np.ascontiguousarray(t, dtype=np.float64)

    if return_path:
        dist, D = _dtw_distance_matrix(r, t)
        path = _backtrack_path(D)
        return dist, path
    else:
        return _dtw_distance_only(r, t)


# ============ Batch DTW for multiple templates ============

@jit(nopython=True, parallel=True, cache=True)
def dtw_batch_distances(templates, test_seq):
    """Compute DTW distances from test sequence to all templates in parallel.

    Args:
        templates: 2D array (num_templates, template_length)
        test_seq: 1D array (test_length,)

    Returns:
        distances: 1D array (num_templates,)
    """
    num_templates = templates.shape[0]
    distances = np.zeros(num_templates, dtype=np.float64)

    for i in prange(num_templates):
        distances[i] = _dtw_distance_only(templates[i], test_seq)

    return distances


@jit(nopython=True, cache=True)
def dtw_with_path_for_template(template, test_seq):
    """Compute DTW with path for a single template.

    Returns (distance, path) tuple.
    """
    dist, D = _dtw_distance_matrix(template, test_seq)
    path = _backtrack_path(D)
    return dist, path
