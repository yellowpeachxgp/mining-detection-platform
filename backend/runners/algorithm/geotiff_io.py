"""
GeoTIFF I/O helpers using rasterio.

Handles multi-band read (NDVI time series) and single-band write (results),
preserving CRS and geotransform from the input data.
"""

import numpy as np
import rasterio


def read_multiband_geotiff(path):
    """Read multi-band GeoTIFF, return (data, profile).

    rasterio reads as (bands, rows, cols) = (l, m, n).
    We transpose to (m, n, l) to match MATLAB's [m, n, l] = size(a).

    Args:
        path: path to GeoTIFF file
    Returns:
        (data, profile):
            data: numpy array (m, n, l) as float64
            profile: rasterio profile dict (CRS, transform, etc.)
    """
    with rasterio.open(path) as ds:
        data = ds.read()  # (l, m, n)
        profile = ds.profile.copy()
    data = data.transpose(1, 2, 0).astype(np.float64)  # -> (m, n, l)
    return data, profile


def write_singleband_geotiff(path, data, reference_profile):
    """Write a 2D array as single-band GeoTIFF preserving spatial reference.

    Uses CRS and transform from the reference profile (input NDVI file).

    Args:
        path: output file path
        data: 2D numpy array (m, n)
        reference_profile: rasterio profile from the input GeoTIFF
    """
    profile = reference_profile.copy()
    profile.update(
        count=1,
        dtype='float64',
        driver='GTiff',
        compress='lzw',
    )
    # Remove multi-band tiling settings that may cause issues
    for key in ('blockxsize', 'blockysize', 'tiled', 'interleave'):
        profile.pop(key, None)

    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(data.astype(np.float64), 1)
