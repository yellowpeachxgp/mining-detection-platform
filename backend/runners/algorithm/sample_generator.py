"""
Training sample template generation - 49 disturbance/recovery patterns.

Direct port of creat_sample.m. Each template is a synthetic NDVI time
series representing a specific disturbance timing + recovery behaviour.
"""

import numpy as np
from .utils import matlab_round, vegetation_recovery


def creat_sample(s, length, p1, p2):
    """Generate 49 training sample templates.

    Direct port of creat_sample.m.

    Template categories:
        Labels  1-9:   Disturbance only (drop from s[1] to s[0])
        Labels 10-36:  Disturbance + exponential recovery
        Label  37:     Stable high NDVI (no disturbance)
        Labels 38-40:  Stable low NDVI (persistent disturbance)
        Labels 41-49:  Recovery only (no prior disturbance)

    Args:
        s: [low, high] from ljpl() - NDVI percentile bounds
           s[0] = 0.5th percentile (low/disturbed value)
           s[1] = 99.5th percentile (high/vegetated value)
        length: number of temporal bands (l)
        p1: amplitude factor 1 (typically 0.8)
        p2: amplitude factor 2 (typically 0.6)
    Returns:
        numpy array (49, length+1) where last column is label (1-49)
    """
    L = length
    r = matlab_round
    sample = np.zeros((49, L + 1))

    # ===== Labels 1-3: Full disturbance, no recovery =====
    # MATLAB: sample(1,:)=[s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,len-round(0.25*len)+1) 1]
    sample[0] = _build_row(s[1], r(0.25 * L) - 1,
                           s[0], L - r(0.25 * L) + 1,
                           label=1, total=L)
    # MATLAB: sample(2,:)=[s(2)*ones(1,round(len/2)-1) s(1)*ones(1,len-round(len/2)+1) 2]
    sample[1] = _build_row(s[1], r(L / 2) - 1,
                           s[0], L - r(L / 2) + 1,
                           label=2, total=L)
    # MATLAB: sample(3,:)=[s(2)*ones(1,round(0.75*len)-1) s(1)*ones(1,len-round(0.75*len)+1) 3]
    sample[2] = _build_row(s[1], r(0.75 * L) - 1,
                           s[0], L - r(0.75 * L) + 1,
                           label=3, total=L)

    # ===== Labels 4-6: p1-scaled disturbance, no recovery =====
    sample[3] = _build_row(p1 * s[1], r(0.25 * L) - 1,
                           s[0], L - r(0.25 * L) + 1,
                           label=4, total=L)
    sample[4] = _build_row(p1 * s[1], r(L / 2) - 1,
                           s[0], L - r(L / 2) + 1,
                           label=5, total=L)
    sample[5] = _build_row(p1 * s[1], r(0.75 * L) - 1,
                           s[0], L - r(0.75 * L) + 1,
                           label=6, total=L)

    # ===== Labels 7-9: p2-scaled disturbance, no recovery =====
    sample[6] = _build_row(p2 * s[1], r(0.25 * L) - 1,
                           s[0], L - r(0.25 * L) + 1,
                           label=7, total=L)
    sample[7] = _build_row(p2 * s[1], r(L / 2) - 1,
                           s[0], L - r(L / 2) + 1,
                           label=8, total=L)
    sample[8] = _build_row(p2 * s[1], r(0.75 * L) - 1,
                           s[0], L - r(0.75 * L) + 1,
                           label=9, total=L)

    # ===== Labels 10-36: Disturbance + recovery =====
    # 9 groups of 3 (by amplitude combo), each with 3 drop positions

    # Group: 1*s[1] disturbance, recovery toward s
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=1.0, rec_target=s, start_label=10)
    # Group: p1*s[1] disturbance, recovery toward s
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p1, rec_target=s, start_label=13)
    # Group: 1*s[1] disturbance, recovery toward [s[0], p1*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=1.0, rec_target=[s[0], p1 * s[1]], start_label=16)
    # Group: p1*s[1] disturbance, recovery toward [s[0], p1*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p1, rec_target=[s[0], p1 * s[1]], start_label=19)
    # Group: p2*s[1] disturbance, recovery toward s
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p2, rec_target=s, start_label=22)
    # Group: 1*s[1] disturbance, recovery toward [s[0], p2*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=1.0, rec_target=[s[0], p2 * s[1]], start_label=25)
    # Group: p2*s[1] disturbance, recovery toward [s[0], p2*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p2, rec_target=[s[0], p2 * s[1]], start_label=28)
    # Group: p2*s[1] disturbance, recovery toward [s[0], p1*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p2, rec_target=[s[0], p1 * s[1]], start_label=31)
    # Group: p1*s[1] disturbance, recovery toward [s[0], p2*s[1]]
    _fill_recovery_group(sample, s, L, p1, p2,
                         dist_amp=p1, rec_target=[s[0], p2 * s[1]], start_label=34)

    # ===== Label 37: Stable high NDVI (no disturbance) =====
    # MATLAB: sample(37,:)=[s(1)*ones(1, len) 37]
    sample[36] = np.append(s[0] * np.ones(L), 37)

    # ===== Labels 38-40: Stable low NDVI (persistent disturbance) =====
    # MATLAB: sample(38,:)=[s(2)*ones(1, len) 38]
    sample[37] = np.append(s[1] * np.ones(L), 38)
    # MATLAB: sample(39,:)=[p1*s(2)*ones(1, len) 39]
    sample[38] = np.append(p1 * s[1] * np.ones(L), 39)
    # MATLAB: sample(40,:)=[p2*s(2)*ones(1, len) 40]
    sample[39] = np.append(p2 * s[1] * np.ones(L), 40)

    # ===== Labels 41-49: Recovery only (no prior disturbance) =====
    # Group: recovery toward s
    _fill_recovery_only_group(sample, s, L, rec_target=s, start_label=41)
    # Group: recovery toward [s[0], p1*s[1]]
    _fill_recovery_only_group(sample, s, L, rec_target=[s[0], p1 * s[1]], start_label=44)
    # Group: recovery toward [s[0], p2*s[1]]
    _fill_recovery_only_group(sample, s, L, rec_target=[s[0], p2 * s[1]], start_label=47)

    return sample


def _build_row(val1, len1, val2, len2, label, total):
    """Build a two-segment row: [val1*ones(len1), val2*ones(len2), label].

    Ensures total length is exactly (total + 1) including the label.
    """
    seg1 = val1 * np.ones(max(0, len1))
    seg2 = val2 * np.ones(max(0, len2))
    row = np.concatenate([seg1, seg2, [label]])
    # Pad or trim to total+1 if rounding causes off-by-one
    result = np.zeros(total + 1)
    result[:min(len(row), total + 1)] = row[:total + 1]
    result[-1] = label
    return result


def _fill_recovery_group(sample, s, L, p1, p2, dist_amp, rec_target, start_label):
    """Fill 3 recovery templates (one per drop position) for a given amplitude combo.

    MATLAB pattern for label N at drop position dp:
        sample(N,:) = [dist_amp*s(2)*ones(1, dp-1)
                       s(1)*ones(1, stable_len)
                       vegetation_recovery(rec_target, [1:rec_len])
                       N]

    Drop positions and stable durations:
        dp=0.25: stable = round(0.375*L - 0.5)
        dp=0.50: stable = round(0.25*L - 0.5)
        dp=0.75: stable = round(0.125*L - 0.5)
    """
    r = matlab_round
    configs = [
        (r(0.25 * L), r(0.375 * L - 0.5)),   # drop at 25%, stable duration
        (r(L / 2),     r(0.25 * L - 0.5)),    # drop at 50%
        (r(0.75 * L),  r(0.125 * L - 0.5)),   # drop at 75%
    ]

    for i, (dp, stable_len) in enumerate(configs):
        label = start_label + i
        pre_len = dp - 1
        rec_len = L - pre_len - stable_len
        if rec_len < 1:
            rec_len = 1

        rec_b = np.arange(1, rec_len + 1)  # MATLAB [1:rec_len]
        rec_vals = vegetation_recovery(rec_target, rec_b)

        row = np.concatenate([
            dist_amp * s[1] * np.ones(max(0, pre_len)),
            s[0] * np.ones(max(0, stable_len)),
            rec_vals,
            [label]
        ])

        # Ensure exact length L+1
        result = np.zeros(L + 1)
        result[:min(len(row), L + 1)] = row[:L + 1]
        result[-1] = label
        sample[label - 1] = result


def _fill_recovery_only_group(sample, s, L, rec_target, start_label):
    """Fill 3 recovery-only templates (labels 41-49).

    MATLAB pattern:
        sample(41,:) = [s(1)*ones(1,round(0.25*len)-1)
                        vegetation_recovery(rec_target,[1:len-round(0.25*len)+1])
                        41]
    """
    r = matlab_round
    positions = [r(0.25 * L), r(L / 2), r(0.75 * L)]

    for i, pos in enumerate(positions):
        label = start_label + i
        pre_len = pos - 1
        rec_len = L - pre_len

        rec_b = np.arange(1, rec_len + 1)  # MATLAB [1:rec_len]
        rec_vals = vegetation_recovery(rec_target, rec_b)

        row = np.concatenate([
            s[0] * np.ones(max(0, pre_len)),
            rec_vals,
            [label]
        ])

        result = np.zeros(L + 1)
        result[:min(len(row), L + 1)] = row[:L + 1]
        result[-1] = label
        sample[label - 1] = result
