"""MATLAB detection engine adapter.

Wraps the existing matlab_runner.py without any modifications to it.
"""

import sys
import os
import logging

from .base_runner import DetectionRunner

logger = logging.getLogger(__name__)

# Add backend directory to path so we can import matlab_runner
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


class MatlabRunner(DetectionRunner):
    """Detection runner using the original MATLAB algorithm."""

    def run_detect(self, ndvi_path, coal_path, out_dir, startyear):
        from matlab_runner import run_matlab_detect
        from config import MATLAB_DIR

        logger.info("Running detection with MATLAB engine")
        return run_matlab_detect(
            MATLAB_DIR, ndvi_path, coal_path, out_dir, startyear
        )
