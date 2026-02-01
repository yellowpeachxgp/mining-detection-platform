"""
End-to-end KNN-DTW pipeline test with synthetic data.

Creates realistic synthetic NDVI data and runs the full classification
pipeline, verifying the results make physical sense.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runners.algorithm.dtw import dtw, _dtw_distance_only, _dtw_distance_matrix
from runners.algorithm.bwlvbo import bwlvbo
from runners.algorithm.sample_generator import creat_sample
from runners.algorithm.utils import matlab_round, ljpl, vegetation_recovery
from runners.algorithm.knn_dtw import knn_classify, _extract_years, _adjust_path_for_nans


def test_knn_dtw_pipeline():
    """Test full KNN-DTW classification pipeline on synthetic data."""
    print("=" * 60)
    print("End-to-End KNN-DTW Pipeline Test")
    print("=" * 60)

    np.random.seed(42)
    L = 15  # 15-year time series

    # -- Generate percentile bounds (mimicking ljpl output) --
    s = [0.15, 0.75]  # [low, high]

    # -- Generate 49 templates --
    samples = creat_sample(s, L, 0.8, 0.6)
    labels = samples[:, -1]
    train_data = samples[:, :-1]

    print(f"\nTemplates: {train_data.shape[0]} templates, length {train_data.shape[1]}")

    # -- Create synthetic test pixels --
    num_pixels = 7
    test_data = np.zeros((num_pixels, L))

    # Pixel 0: Stable high vegetation (should match label 38-40)
    test_data[0] = 0.75 + np.random.randn(L) * 0.02

    # Pixel 1: Disturbance at 50% (should match label 2, 5, or 8)
    test_data[1] = np.concatenate([
        0.72 * np.ones(7) + np.random.randn(7) * 0.02,
        0.18 * np.ones(8) + np.random.randn(8) * 0.02
    ])

    # Pixel 2: Stable low (should match label 37)
    test_data[2] = 0.15 + np.random.randn(L) * 0.02

    # Pixel 3: Disturbance at 25% + recovery (should match label 10-12 range)
    dist_point = matlab_round(0.25 * L) - 1
    stable_len = matlab_round(0.375 * L - 0.5)
    rec_len = L - dist_point - stable_len
    rec_vals = vegetation_recovery(s, np.arange(1, rec_len + 1))
    test_data[3] = np.concatenate([
        0.72 * np.ones(dist_point),
        0.15 * np.ones(stable_len),
        rec_vals[:max(0, L - dist_point - stable_len)]
    ])[:L] + np.random.randn(L) * 0.01

    # Pixel 4: Recovery only at 25% (should match label 41-49)
    rec_point = matlab_round(0.25 * L) - 1
    rec_vals2 = vegetation_recovery(s, np.arange(1, L - rec_point + 1))
    test_data[4] = np.concatenate([
        0.15 * np.ones(rec_point),
        rec_vals2
    ])[:L] + np.random.randn(L) * 0.01

    # Pixel 5: All NaN (edge case)
    test_data[5] = np.full(L, np.nan)

    # Pixel 6: Disturbance at 75% (should match label 3, 6, or 9)
    test_data[6] = np.concatenate([
        0.72 * np.ones(11) + np.random.randn(11) * 0.02,
        0.18 * np.ones(4) + np.random.randn(4) * 0.02
    ])

    # -- Run classification --
    print("\nRunning KNN classification...")
    class_labels, yd, yr = knn_classify(train_data, labels, test_data, k=1, n_jobs=1)

    # -- Verify results --
    print("\n" + "-" * 60)
    print("Results:")
    print("-" * 60)

    expected_types = {
        0: ("Stable high vegetation", [38, 39, 40]),
        1: ("Disturbance at 50%", [2, 5, 8]),
        2: ("Stable low", [37]),
        3: ("Disturbance + recovery", list(range(10, 37))),
        4: ("Recovery only", list(range(41, 50))),
        5: ("All NaN", [0]),
        6: ("Disturbance at 75%", [3, 6, 9]),
    }

    all_pass = True
    for i in range(num_pixels):
        desc, valid_labels = expected_types[i]
        label = int(class_labels[i])
        dist_yr = int(yd[i])
        rec_yr = int(yr[i])

        match = label in valid_labels
        status = "✓" if match else "✗"
        if not match:
            all_pass = False

        print(f"\n  Pixel {i}: {desc}")
        print(f"    Label: {label} {status} (expected one of {valid_labels})")
        print(f"    Disturbance year: {dist_yr}")
        print(f"    Recovery year: {rec_yr}")

    return all_pass


def test_dtw_distance_consistency():
    """Verify _dtw_distance_only and _dtw_distance_matrix return same distance."""
    print("\n" + "=" * 60)
    print("DTW Distance Consistency Test")
    print("=" * 60)

    np.random.seed(123)
    all_pass = True

    for trial in range(20):
        M = np.random.randint(5, 20)
        N = np.random.randint(5, 20)
        r = np.random.rand(M).astype(np.float64)
        t = np.random.rand(N).astype(np.float64)

        dist_only = _dtw_distance_only(r, t)
        dist_matrix, _ = _dtw_distance_matrix(r, t)

        diff = abs(dist_only - dist_matrix)
        match = diff < 1e-10

        if not match:
            all_pass = False
            print(f"  Trial {trial}: MISMATCH! only={dist_only:.6f}, matrix={dist_matrix:.6f}")
        else:
            if trial < 5:
                print(f"  Trial {trial}: M={M}, N={N}, dist={dist_only:.6f} ✓")

    if all_pass:
        print(f"  All 20 trials consistent ✓")
    return all_pass


def test_bwlvbo_edge_cases():
    """Test BWlvbo with various edge cases."""
    print("\n" + "=" * 60)
    print("BWlvbo Edge Cases Test")
    print("=" * 60)

    all_pass = True

    # Case 1: Very short signal
    short = np.array([0.5, 0.6, 0.7])
    result = bwlvbo(short)
    print(f"  Short signal (len=3): output len = {len(result)}")
    assert len(result) == 4, f"Expected 4, got {len(result)}"

    # Case 2: Constant signal
    const = np.array([0.5] * 10)
    result = bwlvbo(const)
    print(f"  Constant signal: output range = [{result.min():.4f}, {result.max():.4f}]")

    # Case 3: Signal with zeros (Python adds protection)
    with_zeros = np.array([0.8, 0.0, 0.8, 0.7, 0.75])
    result = bwlvbo(with_zeros)
    print(f"  Signal with zero: output len = {len(result)}")

    # Case 4: Monotonically increasing
    increasing = np.linspace(0.1, 0.9, 12)
    result = bwlvbo(increasing)
    print(f"  Monotonic signal: output len = {len(result)}")

    print("  All edge cases handled ✓")
    return True


def test_nan_handling_in_knn():
    """Test NaN handling in the KNN classification pipeline."""
    print("\n" + "=" * 60)
    print("NaN Handling Test")
    print("=" * 60)

    L = 15
    s = [0.15, 0.75]
    samples = creat_sample(s, L, 0.8, 0.6)
    labels = samples[:, -1]
    train_data = samples[:, :-1]

    # Create test data with NaN at various positions
    test_data = np.zeros((4, L))

    # NaN at beginning
    test_data[0] = 0.70 * np.ones(L) + np.random.randn(L) * 0.01
    test_data[0, 0] = np.nan

    # NaN in middle
    test_data[1] = 0.70 * np.ones(L) + np.random.randn(L) * 0.01
    test_data[1, 7] = np.nan

    # Multiple NaN
    test_data[2] = 0.70 * np.ones(L) + np.random.randn(L) * 0.01
    test_data[2, [2, 5, 10]] = np.nan

    # All NaN
    test_data[3] = np.full(L, np.nan)

    class_labels, yd, yr = knn_classify(train_data, labels, test_data, k=1, n_jobs=1)

    print(f"  NaN at start: label={int(class_labels[0])}")
    print(f"  NaN in middle: label={int(class_labels[1])}")
    print(f"  Multiple NaN: label={int(class_labels[2])}")
    print(f"  All NaN: label={int(class_labels[3])} (expected 0)")

    assert class_labels[3] == 0, "All-NaN pixel should return label 0"
    print("  NaN handling tests passed ✓")
    return True


def test_creat_sample_detailed():
    """Detailed template generation verification."""
    print("\n" + "=" * 60)
    print("Detailed Template Verification")
    print("=" * 60)

    s = [0.2, 0.8]
    L = 15
    p1 = 0.8
    p2 = 0.6
    r = matlab_round

    samples = creat_sample(s, L, p1, p2)
    all_pass = True

    # Verify labels 1-9 (disturbance only)
    for label in range(1, 10):
        row = samples[label - 1]
        assert row[-1] == label, f"Label {label}: wrong label value"

    # Verify label 1: s[1]*ones at start, s[0]*ones at end
    t1 = samples[0, :-1]
    pre_len = r(0.25 * L) - 1  # = 3
    post_len = L - r(0.25 * L) + 1  # = 12
    expected_pre = s[1] * np.ones(pre_len)
    expected_post = s[0] * np.ones(post_len)
    assert np.allclose(t1[:pre_len], expected_pre), f"Template 1 pre-disturbance mismatch"
    assert np.allclose(t1[pre_len:pre_len + post_len], expected_post), f"Template 1 post-disturbance mismatch"
    print(f"  Template 1 (dist@25%, amp=1.0): ✓")

    # Verify label 4: p1*s[1]*ones at start, s[0]*ones at end
    t4 = samples[3, :-1]
    expected_pre4 = p1 * s[1] * np.ones(pre_len)
    assert np.allclose(t4[:pre_len], expected_pre4), f"Template 4 pre-disturbance mismatch"
    print(f"  Template 4 (dist@25%, amp=p1): ✓")

    # Verify label 37: stable s[0]
    t37 = samples[36, :-1]
    assert np.allclose(t37, s[0] * np.ones(L)), f"Template 37 should be all {s[0]}"
    print(f"  Template 37 (stable low): ✓")

    # Verify label 38: stable s[1]
    t38 = samples[37, :-1]
    assert np.allclose(t38, s[1] * np.ones(L)), f"Template 38 should be all {s[1]}"
    print(f"  Template 38 (stable high): ✓")

    # Verify labels 41-43: recovery only toward s
    for i, pos_frac in enumerate([0.25, 0.5, 0.75]):
        label = 41 + i
        row = samples[label - 1, :-1]
        pos = r(pos_frac * L)
        pre_len = pos - 1
        rec_len = L - pre_len

        # Pre-recovery should be s[0]
        expected_pre = s[0] * np.ones(pre_len)
        assert np.allclose(row[:pre_len], expected_pre, atol=1e-10), \
            f"Template {label} pre-recovery mismatch"

        # Recovery should follow vegetation_recovery
        rec_b = np.arange(1, rec_len + 1)
        expected_rec = vegetation_recovery(s, rec_b)
        actual_rec = row[pre_len:pre_len + rec_len]
        assert np.allclose(actual_rec, expected_rec[:len(actual_rec)], atol=1e-10), \
            f"Template {label} recovery curve mismatch"

        print(f"  Template {label} (recovery@{int(pos_frac*100)}%): ✓")

    print("  All template verifications passed ✓")
    return all_pass


def run_all_tests():
    """Run all end-to-end tests."""
    tests = [
        ("DTW distance consistency", test_dtw_distance_consistency),
        ("BWlvbo edge cases", test_bwlvbo_edge_cases),
        ("Template generation detailed", test_creat_sample_detailed),
        ("NaN handling in KNN", test_nan_handling_in_knn),
        ("Full KNN-DTW pipeline", test_knn_dtw_pipeline),
    ]

    results = []
    for name, func in tests:
        try:
            passed = func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("END-TO-END TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p, _ in results if p)
    for name, p, error in results:
        status = "✓ PASS" if p else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")

    print(f"\nTotal: {passed}/{len(results)} passed")
    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
