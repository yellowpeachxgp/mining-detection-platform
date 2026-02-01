"""
Basic utility functions - Python equivalents of MATLAB helpers.

Ports: ljpl.m, vegetation_recovery.m, and MATLAB-compatible rounding.
"""

import math
import numpy as np


def matlab_round(x):
    """MATLAB-compatible rounding: 0.5 rounds away from zero.

    MATLAB: round(0.5)=1, round(1.5)=2, round(-0.5)=-1
    Python: round(0.5)=0, round(1.5)=2 (banker's rounding)
    """
    if isinstance(x, np.ndarray):
        return np.floor(x + 0.5).astype(int)
    return int(math.floor(float(x) + 0.5))


def ljpl(a):
    """Compute 0.5th and 99.5th percentile of non-zero, non-NaN values.

    Direct port of ljpl.m:
        a1 = reshape(a1, m*n*l, 1);
        a1(a1==0) = [];
        a1(isnan(a1)) = [];
        a1 = sort(a1);
        s = [a1(floor(len*0.005)), a1(floor(len*0.995))];

    Args:
        a: 3D numpy array (m, n, l)
    Returns:
        [low, high] - list of two floats
    """
    flat = a.ravel()
    flat = flat[flat != 0]
    flat = flat[~np.isnan(flat)]
    flat = np.sort(flat)
    length = len(flat)
    # MATLAB floor(len*0.005) is 1-indexed; Python needs -1 for 0-indexed
    low_idx = int(np.floor(length * 0.005)) - 1
    high_idx = int(np.floor(length * 0.995)) - 1
    return [float(flat[low_idx]), float(flat[high_idx])]


def vegetation_recovery(a, b):
    """Exponential recovery curve.

    Direct port of vegetation_recovery.m:
        s = (a(1)-a(2)) * exp(-0.5*b) + a(2)

    Models NDVI recovery after mining disturbance.

    Args:
        a: [low_value, target_value] - two-element list/array
        b: numpy array of time indices (MATLAB 1-based: [1, 2, ..., n])
    Returns:
        numpy array of recovery trajectory values
    """
    b = np.asarray(b, dtype=float)
    return (a[0] - a[1]) * np.exp(-0.5 * b) + a[1]
