"""
Rigorous DTW path priority test.

This test verifies that the Python DTW implementation exactly matches
MATLAB's tie-breaking behavior when multiple directions have equal cost.

MATLAB: min([D(m-1,n), D(m,n-1), D(m-1,n-1)])
Priority when equal: up (index 1) > left (index 2) > diagonal (index 3)
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runners.algorithm.dtw import _dtw_distance_matrix, _backtrack_path


def test_dtw_path_priority_detailed():
    """Detailed test of DTW path priority."""
    print("=" * 60)
    print("Detailed DTW Path Priority Test")
    print("=" * 60)

    # Test case: All equal values means all directions have same cost
    # The path choice will depend entirely on the tie-breaking priority
    r = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)
    t = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)

    dist, D = _dtw_distance_matrix(r, t)
    path = _backtrack_path(D)

    print(f"\nTest: r = t = [1, 1, 1, 1]")
    print(f"\nDistance Matrix D:")
    print(D)
    print(f"\nBacktracked Path (1-based indices):")
    print(path)

    # With MATLAB priority (up > left > diagonal), from (4,4):
    # - At (4,4): D[3,3]=0, D[2,3]=0, D[3,2]=0 -> up wins (go to (3,4))
    # - At (3,4): D[2,3]=0, D[2,2]=0, D[3,2]=0 -> up wins (go to (2,4))
    # - At (2,4): D[1,3]=0, D[0,3]=0, D[1,2]=0 -> up wins (go to (1,4))
    # - At (1,4): m=0, so can only go left -> (1,3)
    # - At (1,3): m=0, so can only go left -> (1,2)
    # - At (1,2): m=0, so can only go left -> (1,1)

    # Expected path with up-priority:
    # Start: (4,4) -> (3,4) -> (2,4) -> (1,4) -> (1,3) -> (1,2) -> (1,1)
    # Reversed: (1,1) -> (1,2) -> (1,3) -> (1,4) -> (2,4) -> (3,4) -> (4,4)

    expected_path = np.array([
        [1, 1],
        [1, 2],
        [1, 3],
        [1, 4],
        [2, 4],
        [3, 4],
        [4, 4]
    ], dtype=np.int64)

    print(f"\nExpected path (MATLAB priority up > left > diag):")
    print(expected_path)

    match = np.array_equal(path, expected_path)
    print(f"\nPath matches MATLAB expected: {'✓ YES' if match else '✗ NO'}")

    if not match:
        print("\nDifferences:")
        for i in range(max(len(path), len(expected_path))):
            if i < len(path) and i < len(expected_path):
                if not np.array_equal(path[i], expected_path[i]):
                    print(f"  Index {i}: got {path[i]}, expected {expected_path[i]}")
            elif i >= len(path):
                print(f"  Index {i}: missing, expected {expected_path[i]}")
            else:
                print(f"  Index {i}: got {path[i]}, unexpected")

    return match


def test_dtw_path_priority_asymmetric():
    """Test with asymmetric sequences where priority matters."""
    print("\n" + "=" * 60)
    print("Asymmetric Sequence Test")
    print("=" * 60)

    # Sequence where template is shorter - forces alignment decisions
    r = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    t = np.array([1.0, 1.5, 2.0, 2.5, 3.0], dtype=np.float64)

    dist, D = _dtw_distance_matrix(r, t)
    path = _backtrack_path(D)

    print(f"\nTest: r = [1, 2, 3], t = [1, 1.5, 2, 2.5, 3]")
    print(f"\nDistance Matrix D:")
    print(D)
    print(f"\nBacktracked Path:")
    print(path)

    # Verify path validity
    assert path[0, 0] == 1 and path[0, 1] == 1, "Path must start at (1,1)"
    assert path[-1, 0] == 3 and path[-1, 1] == 5, "Path must end at (3,5)"

    # Verify path continuity (each step moves by at most 1 in each direction)
    for i in range(1, len(path)):
        dm = path[i, 0] - path[i - 1, 0]
        dn = path[i, 1] - path[i - 1, 1]
        assert dm in [0, 1] and dn in [0, 1], f"Invalid step at index {i}"
        assert dm + dn >= 1, f"No movement at index {i}"

    print("Path validity: ✓")
    return True


def test_dtw_specific_values():
    """Test DTW with specific values that produce predictable results."""
    print("\n" + "=" * 60)
    print("Specific Values Test")
    print("=" * 60)

    # Two sequences that should have perfect diagonal alignment
    r = np.array([0.5, 0.6, 0.7, 0.8, 0.9], dtype=np.float64)
    t = np.array([0.5, 0.6, 0.7, 0.8, 0.9], dtype=np.float64)

    dist, D = _dtw_distance_matrix(r, t)
    path = _backtrack_path(D)

    print(f"\nTest: r = t = [0.5, 0.6, 0.7, 0.8, 0.9]")
    print(f"Distance: {dist}")
    print(f"Path: {path.T}")

    assert dist == 0, f"Expected distance 0, got {dist}"

    # Should be perfect diagonal
    expected = np.array([[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=np.int64)
    match = np.array_equal(path, expected)
    print(f"Perfect diagonal path: {'✓' if match else '✗'}")

    return match


def run_all_priority_tests():
    """Run all priority tests."""
    results = []

    results.append(("Detailed priority test", test_dtw_path_priority_detailed()))
    results.append(("Asymmetric test", test_dtw_path_priority_asymmetric()))
    results.append(("Specific values test", test_dtw_specific_values()))

    print("\n" + "=" * 60)
    print("PRIORITY TEST SUMMARY")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False

    return all_pass


if __name__ == "__main__":
    success = run_all_priority_tests()
    sys.exit(0 if success else 1)
