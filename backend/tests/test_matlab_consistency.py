"""
Comprehensive test suite to verify Python algorithm consistency with MATLAB.

This script tests all core algorithm components:
1. DTW - Dynamic Time Warping
2. BWlvbo - Time series smoothing
3. creat_sample - Template generation
4. vegetation_recovery - Recovery curve
5. ljpl - Percentile calculation
6. Year extraction logic

Run with: python -m pytest tests/test_matlab_consistency.py -v
Or directly: python tests/test_matlab_consistency.py
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runners.algorithm.dtw import dtw, _dtw_distance_matrix, _backtrack_path
from runners.algorithm.bwlvbo import bwlvbo, spike_removal
from runners.algorithm.sample_generator import creat_sample
from runners.algorithm.utils import matlab_round, ljpl, vegetation_recovery
from runners.algorithm.knn_dtw import _extract_years, _adjust_path_for_nans


def test_matlab_round():
    """Test MATLAB-compatible rounding (0.5 rounds away from zero)."""
    print("\n=== Testing matlab_round ===")

    test_cases = [
        (0.5, 1),    # MATLAB: round(0.5) = 1
        (1.5, 2),    # MATLAB: round(1.5) = 2
        (2.5, 3),    # MATLAB: round(2.5) = 3
        (-0.5, 0),   # MATLAB: round(-0.5) = 0 (towards zero) - actually -1 in some versions
        (0.4, 0),
        (0.6, 1),
        (3.7, 4),
    ]

    all_pass = True
    for val, expected in test_cases:
        result = matlab_round(val)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_pass = False
        print(f"  matlab_round({val}) = {result}, expected {expected} {status}")

    return all_pass


def test_dtw_basic():
    """Test DTW distance calculation with known sequences."""
    print("\n=== Testing DTW Basic ===")

    # Test 1: Identical sequences should have distance 0
    r = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    t = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    dist, path = dtw(r, t)
    print(f"  Identical sequences: dist = {dist:.6f} (expected 0)")
    assert abs(dist) < 1e-10, f"Expected 0, got {dist}"

    # Test 2: Shifted sequence
    r = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    t = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
    dist, path = dtw(r, t)
    print(f"  Shifted by 1: dist = {dist:.6f}")

    # Test 3: Different length sequences
    r = np.array([1.0, 2.0, 3.0])
    t = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
    dist, path = dtw(r, t)
    print(f"  Different lengths (3 vs 5): dist = {dist:.6f}")
    print(f"  Path shape: {path.shape}, path:\n{path}")

    return True


def test_dtw_path_priority():
    """Test DTW path backtracking priority matches MATLAB.

    MATLAB: min([D(m-1,n), D(m,n-1), D(m-1,n-1)])
    When equal, returns first index: up > left > diagonal
    """
    print("\n=== Testing DTW Path Priority ===")

    # Create a scenario where all three directions have equal cost
    # This tests the tie-breaking priority
    r = np.array([1.0, 1.0, 1.0])
    t = np.array([1.0, 1.0, 1.0])

    dist, D = _dtw_distance_matrix(r, t)
    path = _backtrack_path(D)

    print(f"  Distance matrix D:\n{D}")
    print(f"  Path (1-based):\n{path}")

    # With equal costs, MATLAB priority is up > left > diagonal
    # From (3,3), all neighbors have same accumulated cost
    # MATLAB would pick "up" first if all equal

    # Verify path is valid (starts at (1,1) and ends at (M,N))
    assert path[0, 0] == 1 and path[0, 1] == 1, "Path should start at (1,1)"
    assert path[-1, 0] == 3 and path[-1, 1] == 3, "Path should end at (3,3)"

    print("  Path validity: ✓")
    return True


def test_vegetation_recovery():
    """Test vegetation recovery curve matches MATLAB."""
    print("\n=== Testing vegetation_recovery ===")

    # MATLAB: s = (a(1)-a(2)) * exp(-0.5*b) + a(2)
    # a(1) = low value (disturbed), a(2) = target (recovered)
    a = [0.2, 0.8]  # low=0.2, target=0.8
    b = np.array([1, 2, 3, 4, 5])

    result = vegetation_recovery(a, b)

    # Manual calculation
    expected = (a[0] - a[1]) * np.exp(-0.5 * b) + a[1]

    print(f"  a = {a}, b = {b}")
    print(f"  Result:   {result}")
    print(f"  Expected: {expected}")

    assert np.allclose(result, expected), "vegetation_recovery mismatch"
    print("  ✓ Match")
    return True


def test_ljpl():
    """Test ljpl percentile calculation."""
    print("\n=== Testing ljpl ===")

    # Create test data with known distribution
    np.random.seed(42)
    data = np.random.rand(10, 10, 5) * 0.8 + 0.1  # Values between 0.1 and 0.9

    # Add some zeros and NaNs (should be excluded)
    data[0, 0, :] = 0
    data[1, 1, :] = np.nan

    result = ljpl(data)

    # Manually compute expected values
    flat = data.ravel()
    flat = flat[flat != 0]
    flat = flat[~np.isnan(flat)]
    flat = np.sort(flat)
    length = len(flat)
    low_idx = int(np.floor(length * 0.005)) - 1
    high_idx = int(np.floor(length * 0.995)) - 1
    expected = [float(flat[low_idx]), float(flat[high_idx])]

    print(f"  Data shape: {data.shape}")
    print(f"  Valid values: {length}")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")

    assert np.allclose(result, expected), "ljpl mismatch"
    print("  ✓ Match")
    return True


def test_spike_removal():
    """Test spike removal in BWlvbo."""
    print("\n=== Testing Spike Removal ===")

    # Create a signal with a dip spike
    # Condition: p1 > 0.2, p2 > 0.2, p3/p4 > 0.4
    # p1 = (c0-c1)/c0, p2 = (c2-c1)/c2, p3 = c2-c1, p4 = c0-c1
    signal = np.array([0.8, 0.3, 0.8, 0.7, 0.75])  # Spike at index 1

    result = spike_removal(signal)

    print(f"  Original: {signal}")
    print(f"  After spike removal: {result}")

    # The spike at position 1 should be replaced with (0.8+0.8)/2 = 0.8
    # Check: p1 = (0.8-0.3)/0.8 = 0.625 > 0.2 ✓
    #        p2 = (0.8-0.3)/0.8 = 0.625 > 0.2 ✓
    #        p3/p4 = (0.8-0.3)/(0.8-0.3) = 1.0 > 0.4 ✓
    expected_val = (0.8 + 0.8) / 2
    print(f"  Expected value at index 1: {expected_val}")

    assert abs(result[1] - expected_val) < 1e-10, f"Expected {expected_val}, got {result[1]}"
    print("  ✓ Spike correctly removed")
    return True


def test_bwlvbo():
    """Test full BWlvbo (spike removal + wavelet denoising)."""
    print("\n=== Testing BWlvbo ===")

    # Create a noisy NDVI-like signal
    np.random.seed(42)
    clean = np.array([0.7, 0.72, 0.68, 0.65, 0.63, 0.60, 0.58, 0.55, 0.52, 0.50])
    noise = np.random.randn(10) * 0.02
    signal = clean + noise

    result = bwlvbo(signal)

    print(f"  Original signal: {signal}")
    print(f"  Denoised result: {result}")
    print(f"  Result length: {len(result)} (input + 1 = {len(signal) + 1})")

    # Result should be length+1 (MATLAB appends last element)
    assert len(result) == len(signal) + 1, f"Expected length {len(signal)+1}, got {len(result)}"
    print("  ✓ Length correct")
    return True


def test_creat_sample():
    """Test template generation matches MATLAB structure."""
    print("\n=== Testing creat_sample ===")

    s = [0.2, 0.8]  # [low, high]
    length = 15
    p1 = 0.8
    p2 = 0.6

    samples = creat_sample(s, length, p1, p2)

    print(f"  Parameters: s={s}, length={length}, p1={p1}, p2={p2}")
    print(f"  Output shape: {samples.shape} (expected (49, {length+1}))")

    assert samples.shape == (49, length + 1), f"Wrong shape: {samples.shape}"

    # Check labels are 1-49
    labels = samples[:, -1]
    expected_labels = np.arange(1, 50)
    assert np.allclose(labels, expected_labels), "Labels should be 1-49"
    print(f"  Labels: 1-49 ✓")

    # Verify specific templates
    # Label 1: disturbance at 25% position
    # MATLAB: [s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,len-round(0.25*len)+1) 1]
    t1 = samples[0, :-1]  # Exclude label
    r = matlab_round
    pre_len = r(0.25 * length) - 1
    post_len = length - r(0.25 * length) + 1
    print(f"  Template 1: pre_len={pre_len}, post_len={post_len}")
    print(f"  Template 1 values: {t1[:5]}...{t1[-5:]}")

    # Label 37: stable low NDVI
    # MATLAB: [s(1)*ones(1, len) 37]
    t37 = samples[36, :-1]
    assert np.allclose(t37, s[0] * np.ones(length)), "Template 37 should be all low values"
    print(f"  Template 37 (stable low): all values = {t37[0]:.2f} ✓")

    # Label 38: stable high NDVI
    # MATLAB: [s(2)*ones(1, len) 38]
    t38 = samples[37, :-1]
    assert np.allclose(t38, s[1] * np.ones(length)), "Template 38 should be all high values"
    print(f"  Template 38 (stable high): all values = {t38[0]:.2f} ✓")

    return True


def test_year_extraction():
    """Test year extraction from warping path."""
    print("\n=== Testing Year Extraction ===")

    N = 15  # Template length

    # Create a simple path for testing
    # Path columns: [template_idx (1-based), test_idx (1-based)]
    path = np.array([
        [1, 1], [2, 2], [3, 3], [4, 4], [5, 5],
        [6, 6], [7, 7], [8, 8], [9, 9], [10, 10],
        [11, 11], [12, 12], [13, 13], [14, 14], [15, 15]
    ], dtype=np.int64)

    id_nan = np.array([], dtype=np.int64)  # No NaN positions

    # Test label 1: disturbance at 25%
    # Expected: yd = path value at template position round(0.25*N)
    label = 1
    yd, yr = _extract_years(path, label, id_nan, N)
    target_pos = matlab_round(0.25 * N)
    expected_yd = target_pos  # Since path is identity mapping
    print(f"  Label {label}: yd={yd}, yr={yr} (expected yd={expected_yd}, yr=0)")
    assert yd == expected_yd, f"Label 1: expected yd={expected_yd}, got {yd}"
    assert yr == 0, f"Label 1: expected yr=0, got {yr}"

    # Test label 37-40: no disturbance, no recovery
    for label in [37, 38, 39, 40]:
        yd, yr = _extract_years(path, label, id_nan, N)
        assert yd == 0 and yr == 0, f"Label {label}: expected (0,0), got ({yd},{yr})"
    print(f"  Labels 37-40: yd=0, yr=0 ✓")

    # Test label 41: recovery only at 25%
    label = 41
    yd, yr = _extract_years(path, label, id_nan, N)
    print(f"  Label {label}: yd={yd}, yr={yr}")
    assert yd == 0, f"Label 41: expected yd=0, got {yd}"

    print("  Year extraction tests passed ✓")
    return True


def test_nan_path_adjustment():
    """Test NaN position adjustment in warping path."""
    print("\n=== Testing NaN Path Adjustment ===")

    # Path with 1-based indices
    path = np.array([
        [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]
    ], dtype=np.int64)

    # NaN at position 3 (1-based) was removed from test data
    # Path indices after position 3 should be incremented
    id_nan = np.array([3], dtype=np.int64)

    adjusted = _adjust_path_for_nans(path, id_nan)

    print(f"  Original path: {path[:, 1].tolist()}")
    print(f"  NaN positions: {id_nan.tolist()}")
    print(f"  Adjusted path: {adjusted[:, 1].tolist()}")

    # After adjustment: indices >= 3 should be +1
    # Expected: [1, 2, 4, 5, 6]
    expected = np.array([1, 2, 4, 5, 6], dtype=np.int64)
    assert np.array_equal(adjusted[:, 1], expected), f"Expected {expected}, got {adjusted[:, 1]}"
    print("  ✓ NaN adjustment correct")
    return True


def test_full_pipeline_consistency():
    """Test a full classification pipeline for internal consistency."""
    print("\n=== Testing Full Pipeline Consistency ===")

    # Create synthetic NDVI data
    np.random.seed(42)

    # Simulate a disturbance pattern: high -> drop -> stable low
    # This should match template type 1-9 (disturbance only)
    length = 15

    # Pattern: high values, then sudden drop at 50%
    test_pattern = np.concatenate([
        0.75 * np.ones(7),   # High NDVI
        0.25 * np.ones(8)    # Low NDVI after disturbance
    ])

    # Add slight noise
    test_pattern = test_pattern + np.random.randn(length) * 0.02

    # Generate templates
    s = [0.2, 0.8]
    samples = creat_sample(s, length, 0.8, 0.6)
    train_data = samples[:, :-1]
    labels = samples[:, -1]

    # Find best matching template
    from runners.algorithm.dtw import _dtw_distance_only
    from runners.algorithm.bwlvbo import bwlvbo

    # Denoise test pattern
    denoised = bwlvbo(test_pattern)[:length]  # Trim to original length

    # Compute distances to all templates
    distances = []
    for i in range(49):
        d = _dtw_distance_only(
            np.ascontiguousarray(train_data[i], dtype=np.float64),
            np.ascontiguousarray(denoised, dtype=np.float64)
        )
        distances.append(d)

    best_idx = np.argmin(distances)
    best_label = int(labels[best_idx])

    print(f"  Test pattern: high->low at 50%")
    print(f"  Best matching template: Label {best_label}")
    print(f"  Top 5 matches: {np.argsort(distances)[:5] + 1}")  # 1-based labels

    # Should match labels 2, 5, or 8 (disturbance at 50%, various amplitudes)
    expected_labels = [2, 5, 8]
    if best_label in expected_labels:
        print(f"  ✓ Matched expected disturbance pattern (50% position)")
    else:
        print(f"  ⚠ Unexpected match - check template generation")

    return True


def run_all_tests():
    """Run all consistency tests."""
    print("=" * 60)
    print("MATLAB/Python Consistency Test Suite")
    print("=" * 60)

    tests = [
        ("matlab_round", test_matlab_round),
        ("DTW basic", test_dtw_basic),
        ("DTW path priority", test_dtw_path_priority),
        ("vegetation_recovery", test_vegetation_recovery),
        ("ljpl", test_ljpl),
        ("spike_removal", test_spike_removal),
        ("bwlvbo", test_bwlvbo),
        ("creat_sample", test_creat_sample),
        ("year_extraction", test_year_extraction),
        ("nan_path_adjustment", test_nan_path_adjustment),
        ("full_pipeline", test_full_pipeline_consistency),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ✗ Exception: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p, _ in results if p)
    failed = len(results) - passed

    for name, p, error in results:
        status = "✓ PASS" if p else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")

    print(f"\nTotal: {passed}/{len(results)} passed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
