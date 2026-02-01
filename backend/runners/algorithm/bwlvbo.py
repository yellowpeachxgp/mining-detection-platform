"""
Time series smoothing: spike removal + wavelet denoising.

Optimized with Numba JIT for spike removal.
Replaces MATLAB's wden() with PyWavelets.
"""

import numpy as np
from numba import jit
import pywt


@jit(nopython=True, cache=True)
def _spike_removal_numba(a):
    """Remove dip-spikes using a sliding window of 3.

    Numba-accelerated version.

    MATLAB BWlvbo.m spike removal logic:
        For each triplet [c1, c2, c3]:
          p1 = (c1-c2)/c1;  p2 = (c3-c2)/c3
          p3 = c3-c2;       p4 = c1-c2
          if p1>0.2 && p2>0.2 && p3/p4>0.4: a[i+1] = (c1+c3)/2
    """
    n = len(a)
    result = a.copy()

    for i in range(n - 2):
        c0 = result[i]
        c1 = result[i + 1]
        c2 = result[i + 2]

        if c0 == 0.0 or c2 == 0.0:
            continue

        p1 = (c0 - c1) / c0
        p2 = (c2 - c1) / c2
        p3 = c2 - c1
        p4 = c0 - c1

        if p4 == 0.0:
            continue

        if p1 > 0.2 and p2 > 0.2 and p3 / p4 > 0.4:
            result[i + 1] = (c0 + c2) / 2.0

    return result


def spike_removal(a):
    """Remove dip-spikes using a sliding window of 3.

    Wrapper for Numba-accelerated implementation.
    """
    a = np.ascontiguousarray(a, dtype=np.float64)
    return _spike_removal_numba(a)


def _minimaxi_threshold(n):
    """MATLAB minimaxi threshold rule (from thselect).

    For signal length n:
      if n <= 32: thr = 0
      else: thr = 0.3936 + 0.1829 * log2(n)
    """
    if n <= 32:
        return 0.0
    return 0.3936 + 0.1829 * np.log2(n)


def _wden_minimaxi_soft_mln(signal, wavelet='db7', level=2):
    """Replicate MATLAB wden(signal, 'minimaxi', 's', 'mln', level, wavelet).

    Parameters of MATLAB wden:
        'minimaxi' - minimax threshold selection
        's'        - soft thresholding
        'mln'      - level-dependent noise estimation via MAD
        level      - wavelet decomposition level
        wavelet    - wavelet basis function
    """
    # Adjust level if signal is too short
    max_level = pywt.dwt_max_level(len(signal), pywt.Wavelet(wavelet).dec_len)
    level = min(level, max_level)

    if level < 1:
        return signal.copy()

    coeffs = pywt.wavedec(signal, wavelet, level=level)
    # coeffs = [cA_n, cD_n, cD_n-1, ..., cD_1]

    n = len(signal)
    base_thr = _minimaxi_threshold(n)

    denoised_coeffs = [coeffs[0]]  # keep approximation unchanged

    for i in range(1, len(coeffs)):
        detail = coeffs[i]
        if len(detail) == 0:
            denoised_coeffs.append(detail)
            continue
        # Estimate noise sigma using MAD (Median Absolute Deviation)
        sigma = np.median(np.abs(detail)) / 0.6745
        thr = base_thr * sigma
        # Soft thresholding
        denoised = pywt.threshold(detail, value=thr, mode='soft')
        denoised_coeffs.append(denoised)

    reconstructed = pywt.waverec(denoised_coeffs, wavelet)
    return reconstructed


def bwlvbo(a):
    """Combined spike removal + wavelet denoising.

    Direct port of BWlvbo.m:
        1. Spike removal (sliding window)
        2. wden([a a(n)], 'minimaxi', 's', 'mln', 2, 'db7')
           Note: appends last element to extend signal by 1

    Args:
        a: 1D numpy array - NDVI time series
    Returns:
        1D numpy array - denoised time series
    """
    a = np.asarray(a, dtype=np.float64).ravel()

    if len(a) == 0:
        return a.copy()

    a = spike_removal(a)

    # Extend by duplicating last element (MATLAB: [a a(n)])
    extended = np.append(a, a[-1])

    denoised = _wden_minimaxi_soft_mln(extended, wavelet='db7', level=2)

    # waverec may return slightly different length; trim to extended length
    if len(denoised) > len(extended):
        denoised = denoised[:len(extended)]
    elif len(denoised) < len(extended):
        # Pad if needed (rare)
        denoised = np.pad(denoised, (0, len(extended) - len(denoised)), mode='edge')

    return denoised
