"""
KNN classifier using DTW distance - optimized with parallel processing.

Performance optimizations vs original pure-Python version:
1. Numba JIT for DTW computation (50-100x over pure Python)
2. Only compute warping path for best-matching template (1 vs 49)
3. Parallel pixel processing via joblib multiprocessing (Nx for N cores)
4. Chunk-based data distribution for memory efficiency

Port of knn.m with identical algorithmic logic.
"""

import os
import logging
import time
import numpy as np

from .dtw import _dtw_distance_only, _dtw_distance_matrix, _backtrack_path
from .bwlvbo import bwlvbo, _spike_removal_numba
from .utils import matlab_round

try:
    from joblib import Parallel, delayed
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

logger = logging.getLogger(__name__)


def _warmup_numba():
    """Pre-compile all Numba functions so disk cache is ready for workers."""
    d = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    _dtw_distance_only(d, d)
    _dtw_distance_matrix(d, d)
    _backtrack_path(np.ones((3, 3), dtype=np.float64))
    _spike_removal_numba(np.array([0.5, 0.3, 0.5, 0.4, 0.5], dtype=np.float64))


def _process_pixel(test_ts, train_data, labels, N):
    """Process a single pixel: NaN removal -> bwlvbo -> DTW -> year extraction.

    Args:
        test_ts: 1D array, single pixel time series (may contain NaN)
        train_data: (49, L) float64 contiguous training templates
        labels: (49,) float64 template labels
        N: int, number of bands (template length)
    Returns:
        (class_label, disturbance_year, recovery_year)
    """
    try:
        nan_mask = np.isnan(test_ts)
        id_nan = np.where(nan_mask)[0] + 1  # 1-based for MATLAB compat
        test_clean = test_ts[~nan_mask]

        if len(test_clean) == 0:
            return 0, 0, 0

        # Spike removal + wavelet denoising
        denoised = bwlvbo(test_clean)
        denoised = np.ascontiguousarray(denoised, dtype=np.float64)

        # Find best-matching template (distance only, no path yet)
        n_templates = train_data.shape[0]
        best_dist = np.inf
        best_idx = 0
        for i in range(n_templates):
            d = _dtw_distance_only(train_data[i], denoised)
            if d < best_dist:
                best_dist = d
                best_idx = i

        best_label = int(labels[best_idx])

        # Compute warping path ONLY for the best template
        _, D = _dtw_distance_matrix(train_data[best_idx], denoised)
        path = _backtrack_path(D)

        # Extract disturbance/recovery years
        yd, yr = _extract_years(path, best_label, id_nan, N)
        return best_label, yd, yr
    except Exception:
        return 0, 0, 0


def _process_chunk(chunk_data, train_data, labels, N):
    """Process a chunk of pixels in a single worker.

    Args:
        chunk_data: (n_pixels, L) float64 array
        train_data: (49, L) float64 contiguous templates
        labels: (49,) float64 labels
        N: int, band count
    Returns:
        (n_pixels, 3) int64 array: [class_label, yd, yr]
    """
    n = chunk_data.shape[0]
    results = np.zeros((n, 3), dtype=np.int64)
    for i in range(n):
        c, yd, yr = _process_pixel(chunk_data[i], train_data, labels, N)
        results[i, 0] = c
        results[i, 1] = yd
        results[i, 2] = yr
    return results


def knn_classify(train_data, labels, test_data, k=1, n_jobs=-1, chunk_size=2000):
    """KNN classification with DTW distance - parallel optimized.

    Direct port of knn.m with performance optimizations.

    For each test pixel:
      1. Remove NaN values, record their positions
      2. Apply BWlvbo (spike removal + wavelet denoise)
      3. Compute DTW distance to all 49 templates
      4. Take nearest template (k=1)
      5. Extract disturbance/recovery year from warping path

    Args:
        train_data: (49, L) training templates
        labels: (49,) template labels (1-49)
        test_data: (num_pixels, L) test data (may contain NaN)
        k: number of neighbors (always 1)
        n_jobs: parallel workers (-1 = all CPU cores, 1 = sequential)
        chunk_size: pixels per parallel chunk
    Returns:
        (class_labels, disturbance_years, recovery_years)
        Each is (num_pixels,) array of ints
    """
    # Ensure correct dtypes for Numba
    train_f64 = np.ascontiguousarray(train_data, dtype=np.float64)
    labels_f64 = np.asarray(labels, dtype=np.float64)
    test_f64 = np.asarray(test_data, dtype=np.float64)

    M_test, N = test_f64.shape

    if M_test == 0:
        empty = np.zeros(0, dtype=int)
        return empty.copy(), empty.copy(), empty.copy()

    # Pre-compile Numba functions (disk cache for workers)
    logger.info("Warming up Numba JIT compilation cache...")
    _warmup_numba()

    # Resolve n_jobs
    if n_jobs == -1:
        import multiprocessing
        n_jobs = multiprocessing.cpu_count()

    t0 = time.time()

    if n_jobs <= 1 or not HAS_JOBLIB or M_test <= chunk_size:
        # Sequential mode
        logger.info(f"KNN-DTW sequential: {M_test} pixels")
        class_test, class_yd, class_yr = _classify_sequential(
            train_f64, labels_f64, test_f64, N
        )
    else:
        # Parallel mode
        n_chunks = (M_test + chunk_size - 1) // chunk_size
        logger.info(f"KNN-DTW parallel: {M_test} pixels, {n_chunks} chunks, {n_jobs} workers")
        class_test, class_yd, class_yr = _classify_parallel(
            train_f64, labels_f64, test_f64, N, n_jobs, chunk_size
        )

    elapsed = time.time() - t0
    rate = M_test / elapsed if elapsed > 0 else 0
    logger.info(f"KNN classification complete: {M_test} pixels in {elapsed:.1f}s ({rate:.0f} px/s)")
    return class_test, class_yd, class_yr


def _classify_sequential(train_data, labels, test_data, N):
    """Sequential pixel processing with progress logging."""
    M_test = test_data.shape[0]
    class_test = np.zeros(M_test, dtype=int)
    class_yd = np.zeros(M_test, dtype=int)
    class_yr = np.zeros(M_test, dtype=int)

    log_interval = max(1, M_test // 20)  # Log ~20 times

    for i in range(M_test):
        if i > 0 and i % log_interval == 0:
            logger.info(f"  Progress: {i}/{M_test} ({100 * i // M_test}%)")

        c, yd, yr = _process_pixel(test_data[i], train_data, labels, N)
        class_test[i] = c
        class_yd[i] = yd
        class_yr[i] = yr

    return class_test, class_yd, class_yr


def _classify_parallel(train_data, labels, test_data, N, n_jobs, chunk_size):
    """Parallel pixel processing via joblib multiprocessing."""
    M_test = test_data.shape[0]
    n_chunks = (M_test + chunk_size - 1) // chunk_size

    # Build chunk list (slices get pickled as copies automatically)
    chunk_args = []
    for i in range(0, M_test, chunk_size):
        end = min(i + chunk_size, M_test)
        chunk_args.append(test_data[i:end])

    # Parallel execution
    # verbose=10: one line per completed chunk
    results_list = Parallel(
        n_jobs=n_jobs,
        verbose=10,
        prefer="processes"
    )(
        delayed(_process_chunk)(chunk, train_data, labels, N)
        for chunk in chunk_args
    )

    combined = np.vstack(results_list)
    return (
        combined[:, 0].astype(int),
        combined[:, 1].astype(int),
        combined[:, 2].astype(int),
    )


# ============================================================
# Year extraction logic (port of knn.m switch statement)
# ============================================================

def _adjust_path_for_nans(py, id_nan):
    """Adjust warping path column 2 for removed NaN positions.

    Direct port of the NaN correction loop in knn.m:
        for s=1:length(id_nan)
            h = find(py(:,2) == id_nan(s));
            if ~isempty(h)
                py(h(1):end, 2) = py(h(1):end, 2) + 1;
            end
        end

    Shifts test-data indices in the path to restore original
    (pre-NaN-removal) positions.
    """
    py = py.copy()
    for nan_pos in id_nan:
        matches = np.where(py[:, 1] == nan_pos)[0]
        if len(matches) > 0:
            first_match = matches[0]
            py[first_match:, 1] += 1
    return py


def _extract_years(py, label, id_nan, N):
    """Extract disturbance and recovery year from warping path.

    Direct port of the switch statement in knn.m.

    N is the template length (number of bands).
    Path column 0 = template index (1-based).
    Path column 1 = test index (1-based).
    The "year" is the test-data index for a specific template position.

    Args:
        py: (K, 2) warping path, 1-based indices
        label: int, best-match template label (1-49)
        id_nan: 1D array of NaN positions (1-based)
        N: int, template length
    Returns:
        (yd, yr) - disturbance year, recovery year (ints, 0 = not applicable)
    """
    r = matlab_round

    # Adjust path for NaN removal (all cases except 37-40)
    if label not in (37, 38, 39, 40):
        py = _adjust_path_for_nans(py, id_nan)

    yd = 0
    yr = 0

    # --- Disturbance only: patterns 1-9 ---
    if label in (1, 4, 7):
        target = r(0.25 * N)
        t_dis = np.where(py[:, 0] == target)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])

    elif label in (2, 5, 8):
        target = r(N / 2)
        t_dis = np.where(py[:, 0] == target)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])

    elif label in (3, 6, 9):
        target = r(0.75 * N)
        t_dis = np.where(py[:, 0] == target)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])

    # --- Disturbance + recovery at 25% drop point ---
    elif label in (10, 13, 16, 19, 22, 25, 28, 31, 34):
        target_d = r(0.25 * N)
        t_dis = np.where(py[:, 0] == target_d)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])
        target_r = r(0.25 * N) - 1 + r(0.375 * N - 0.5) + 1
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    # --- Disturbance + recovery at 50% drop point ---
    elif label in (11, 14, 17, 20, 23, 26, 29, 32, 35):
        target_d = r(N / 2)
        t_dis = np.where(py[:, 0] == target_d)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])
        target_r = r(N / 2) - 1 + r(0.25 * N - 0.5) + 1
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    # --- Disturbance + recovery at 75% drop point ---
    elif label in (12, 15, 18, 21, 24, 27, 30, 33, 36):
        target_d = r(0.75 * N)
        t_dis = np.where(py[:, 0] == target_d)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])
        target_r = r(0.75 * N) - 1 + r(0.125 * N - 0.5) + 1
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    # --- Stable patterns: no disturbance, no recovery ---
    elif label in (37, 38, 39, 40):
        yd = 0
        yr = 0

    # --- Recovery only at 25% ---
    elif label in (41, 44, 47):
        target_r = r(0.25 * N)
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    # --- Recovery only at 50% ---
    elif label in (42, 45, 48):
        target_r = r(N / 2)
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    # --- Recovery only at 75% ---
    elif label in (43, 46, 49):
        target_r = r(0.75 * N)
        t_rec = np.where(py[:, 0] == target_r)[0]
        if len(t_rec) > 0:
            yr = int(py[t_rec[0], 1])

    return yd, yr
