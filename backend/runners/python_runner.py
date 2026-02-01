"""
Python detection engine - full pipeline.

Direct port of detectMiningDisturbance.m using NumPy/SciPy/PyWavelets.
Produces identical 7 GeoTIFF output files as the MATLAB version.
"""

import os
import logging
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.ndimage import binary_opening, generate_binary_structure, label, median_filter

from .base_runner import DetectionRunner
from .algorithm.utils import ljpl
from .algorithm.sample_generator import creat_sample
from .algorithm.knn_dtw import knn_classify
from .algorithm.geotiff_io import read_multiband_geotiff, write_singleband_geotiff

logger = logging.getLogger(__name__)


def _resample_to_target(src_path, target_shape, target_transform, target_crs):
    """Resample a GeoTIFF to match target grid dimensions.

    Args:
        src_path: path to source GeoTIFF
        target_shape: (height, width) of target grid
        target_transform: rasterio Affine transform of target grid
        target_crs: CRS of target grid
    Returns:
        numpy array (height, width, bands) resampled to target grid
    """
    with rasterio.open(src_path) as src:
        src_bands = src.count
        # Create output array matching target dimensions
        dst_data = np.zeros((target_shape[0], target_shape[1], src_bands), dtype=np.float64)

        for band_idx in range(src_bands):
            src_band = src.read(band_idx + 1).astype(np.float64)
            dst_band = np.zeros(target_shape, dtype=np.float64)

            reproject(
                source=src_band,
                destination=dst_band,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=target_transform,
                dst_crs=target_crs,
                resampling=Resampling.nearest
            )
            dst_data[:, :, band_idx] = dst_band

        return dst_data


def _disk_structuring_element(radius):
    """Generate disk structuring element matching MATLAB strel('disk', radius).

    Avoids scikit-image dependency for this single function.
    """
    L = 2 * radius + 1
    Y, X = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return (X ** 2 + Y ** 2) <= radius ** 2


class PythonRunner(DetectionRunner):
    """Detection runner using pure Python (NumPy/SciPy) algorithms."""

    def run_detect(self, ndvi_path, coal_path, out_dir, startyear):
        os.makedirs(out_dir, exist_ok=True)
        logger.info(f"Python engine: starting detection (startyear={startyear})")

        # Output file paths (must match detectMiningDisturbance.m exactly)
        out_mask = os.path.join(out_dir, 'mining_disturbance_mask.tif')
        out_dist_year = os.path.join(out_dir, 'mining_disturbance_year.tif')
        out_recv_year = os.path.join(out_dir, 'mining_recovery_year.tif')
        out_potential = os.path.join(out_dir, 'potential_disturbance.tif')
        out_res_type = os.path.join(out_dir, 'res_disturbance_type.tif')
        out_year_disturb = os.path.join(out_dir, 'year_disturbance_raw.tif')
        out_year_recovery = os.path.join(out_dir, 'year_recovery_raw.tif')

        # ====== Step 1: Load NDVI GeoTIFF ======
        logger.info("Step 1/7: Loading NDVI data")
        a, ndvi_profile = read_multiband_geotiff(ndvi_path)  # (m, n, l)

        # ====== Step 2: Clean data ======
        # MATLAB: a(a==0)=NaN; a(a>=1)=NaN; a(a<-1)=0
        a[a == 0] = np.nan
        a[a >= 1] = np.nan
        a[a < -1] = 0
        m, n, l = a.shape
        logger.info(f"  Data shape: {m}x{n}, {l} bands")

        # ====== Step 3: Normalize ======
        logger.info("Step 2/7: Computing normalization bounds")
        s = ljpl(a)
        logger.info(f"  Percentile bounds: s={s}")

        # Clip to [0, 1]
        a[a > 1] = 1
        a[a < 0] = 0

        # ====== Step 4: Reshape and filter ======
        # MATLAB reshape is column-major → order='F'
        b = a.reshape(m * n, l, order='F')
        b[np.all(np.isnan(b), axis=1)] = 0
        del a

        e = b.copy()  # keep original for zero-position tracking
        zero_mask = np.all(b == 0, axis=1)
        b_valid = b[~zero_mask]  # remove all-zero rows
        logger.info(f"  Valid pixels: {b_valid.shape[0]} / {m * n}")

        # ====== Step 5: Generate training samples ======
        logger.info("Step 3/7: Generating 49 training templates")
        sample = creat_sample(s, l, 0.8, 0.6)
        sample_label = sample[:, l].astype(np.float32)
        train_data = sample[:, :l].astype(np.float32)

        # ====== Step 6: KNN classification with DTW ======
        logger.info("Step 4/7: Running KNN-DTW classification")
        c, y1, y2 = knn_classify(train_data, sample_label, b_valid, k=1)

        # ====== Step 7: Restore full pixel grid ======
        logger.info("Step 5/7: Restoring spatial grid")
        full_c = np.zeros(m * n, dtype=c.dtype)
        full_y1 = np.zeros(m * n, dtype=y1.dtype)
        full_y2 = np.zeros(m * n, dtype=y2.dtype)
        full_c[~zero_mask] = c
        full_y1[~zero_mask] = y1
        full_y2[~zero_mask] = y2

        # Reshape back to (m, n) - column-major
        res_disturbance = full_c.reshape(m, n, order='F')
        yeardisturbance = full_y1.reshape(m, n, order='F')
        yearrecovery = full_y2.reshape(m, n, order='F')

        # ====== Step 8: Spatial filtering ======
        logger.info("Step 6/7: Applying spatial filters")

        # Morphological opening
        # MATLAB: bw(bw==38|bw==39|bw==40|isnan(bw))=0; bw(bw~=0)=1
        bw = res_disturbance.astype(float)
        bw[(bw == 38) | (bw == 39) | (bw == 40) | np.isnan(bw)] = 0
        bw[bw != 0] = 1

        # MATLAB: se = strel('disk',2); openbw = imopen(bw, se)
        se = _disk_structuring_element(2)
        openbw = binary_opening(bw.astype(bool), structure=se).astype(int)

        # Connected component labeling (8-connectivity)
        # MATLAB: [polygon_disturbance, ~] = bwlabel(openbw, 8)
        struct_8conn = generate_binary_structure(2, 2)
        polygon_disturbance, num_features = label(openbw, structure=struct_8conn)
        potential_disturbance = polygon_disturbance.copy()
        logger.info(f"  Found {num_features} connected components")

        # ====== Step 9: Bare coal validation ======
        logger.info("Step 6b/7: Loading and resampling coal data")
        # Resample coal data to match NDVI grid if dimensions differ
        coal_data, coal_profile = read_multiband_geotiff(coal_path)
        if coal_data.shape[:2] != (m, n):
            logger.info(f"  Resampling coal from {coal_data.shape[:2]} to {(m, n)}")
            coal_data = _resample_to_target(
                coal_path,
                target_shape=(m, n),
                target_transform=ndvi_profile['transform'],
                target_crs=ndvi_profile['crs']
            )
        coal_data[np.isnan(coal_data)] = 0
        coal_data[coal_data <= 0.5] = 0
        coal_data[coal_data > 0.5] = 1
        sum_barecoal = np.sum(coal_data, axis=2)
        sum_barecoal[sum_barecoal != 0] = 1
        sum_barecoal = median_filter(sum_barecoal.astype(np.float64), size=(5, 5))
        del coal_data

        # ====== Step 10: Area and coverage filtering ======
        union_map = sum_barecoal * polygon_disturbance
        union_flat = union_map.ravel()
        union_flat = union_flat[union_flat != 0]
        unique_labels = np.unique(union_flat).astype(int)

        kept = 0
        for lbl in unique_labels:
            region_mask = (polygon_disturbance == lbl).astype(float)
            total_num = np.sum(region_mask)
            coal_in_region = region_mask * sum_barecoal
            coal_in_region[coal_in_region != 0] = 1
            union_num = np.sum(coal_in_region)
            # MATLAB: if total_num >= 1111 && (union_num >= 222 && union_num/total_num >= 0.02)
            if total_num >= 1111 and union_num >= 222 and union_num / total_num >= 0.02:
                polygon_disturbance[polygon_disturbance == lbl] = -1
                kept += 1

        polygon_disturbance[polygon_disturbance != -1] = 0
        polygon_disturbance[polygon_disturbance == -1] = 1
        logger.info(f"  Kept {kept} mining regions after filtering")

        # ====== Step 11: Convert relative years to absolute ======
        year_miningdisturbance = polygon_disturbance * yeardisturbance
        year_miningdisturbance = year_miningdisturbance + startyear - 1
        year_miningdisturbance[year_miningdisturbance == startyear - 1] = 0

        year_miningrecovery = polygon_disturbance * yearrecovery
        year_miningrecovery = year_miningrecovery + startyear - 1
        year_miningrecovery[year_miningrecovery == startyear - 1] = 0

        # ====== Step 12: Write output GeoTIFFs ======
        logger.info("Step 7/7: Writing output files")
        write_singleband_geotiff(out_mask, polygon_disturbance.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_dist_year, year_miningdisturbance.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_recv_year, year_miningrecovery.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_potential, potential_disturbance.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_res_type, res_disturbance.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_year_disturb, yeardisturbance.astype(np.float64), ndvi_profile)
        write_singleband_geotiff(out_year_recovery, yearrecovery.astype(np.float64), ndvi_profile)

        logger.info("Python engine: detection complete")

        return {
            "mask": out_mask,
            "disturbance_year": out_dist_year,
            "recovery_year": out_recv_year,
            "potential": out_potential,
            "res_type": out_res_type,
            "year_disturb_raw": out_year_disturb,
            "year_recovery_raw": out_year_recovery,
        }
