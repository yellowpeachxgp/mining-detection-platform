"""
Runner factory - selects detection engine (Python or MATLAB).

Usage:
    from runners import get_runner
    runner = get_runner('python')  # or 'matlab', or None for config default
    result = runner.run_detect(ndvi_path, coal_path, out_dir, startyear)
"""

import logging
from .base_runner import DetectionRunner

logger = logging.getLogger(__name__)


def get_runner(engine: str = None) -> DetectionRunner:
    """Factory: return the appropriate detection runner.

    Args:
        engine: 'python' or 'matlab'. If None, reads from config.DETECTION_ENGINE.
    Returns:
        DetectionRunner instance
    Raises:
        ValueError: if engine name is unknown
    """
    if engine is None:
        import sys
        import os
        # Ensure backend dir is in path for config import
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from config import DETECTION_ENGINE
        engine = DETECTION_ENGINE

    engine = engine.lower().strip()

    if engine == 'matlab':
        from .matlab_runner_adapter import MatlabRunner
        logger.info("Using MATLAB detection engine")
        return MatlabRunner()
    elif engine == 'python':
        from .python_runner import PythonRunner
        logger.info("Using Python detection engine")
        return PythonRunner()
    else:
        raise ValueError(f"Unknown engine: '{engine}'. Must be 'python' or 'matlab'.")
