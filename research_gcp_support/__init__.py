"""
GCP Support - Ground Control Point finder and exporter for drone imagery processing.
"""

from .gcp_finder import GCPFinder
from .h3_utils import h3_cells_to_bbox
from .usgs_gcp import USGSGCPClient
from .noaa_gcp import NOAAGCPClient
from .gcp_filter import calculate_spatial_distribution_score, GCPFilter

__version__ = "0.1.0"
__all__ = [
    "GCPFinder",
    "h3_cells_to_bbox",
    "USGSGCPClient",
    "NOAAGCPClient",
    "calculate_spatial_distribution_score",
    "GCPFilter"
]

