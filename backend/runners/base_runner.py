"""Abstract base class for mining disturbance detection engines."""

from abc import ABC, abstractmethod
from typing import Dict


class DetectionRunner(ABC):
    """Abstract base class for detection runners.

    Both MATLAB and Python engines implement this interface,
    producing identical output file structures.
    """

    @abstractmethod
    def run_detect(self, ndvi_path: str, coal_path: str,
                   out_dir: str, startyear: int) -> Dict[str, str]:
        """Run mining disturbance detection algorithm.

        Args:
            ndvi_path:  Path to multi-band NDVI GeoTIFF
            coal_path:  Path to bare coal probability GeoTIFF
            out_dir:    Output directory for result GeoTIFFs
            startyear:  Starting year of the time series

        Returns:
            Dict with keys:
                mask, disturbance_year, recovery_year,
                potential, res_type, year_disturb_raw, year_recovery_raw
            Each value is the full path to the output GeoTIFF.
        """
        pass
