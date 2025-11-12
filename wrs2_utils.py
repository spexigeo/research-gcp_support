"""
Utilities for working with Landsat WRS-2 (Worldwide Reference System 2) Path and Row.
"""

from typing import Tuple, List
import math


def lat_lon_to_wrs2_path_row(lat: float, lon: float) -> Tuple[int, int]:
    """
    Convert latitude/longitude to Landsat WRS-2 Path and Row.
    
    This is a simplified implementation. For production use, consider using
    the official Landsat WRS-2 shapefiles or more precise algorithms.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees (negative for west)
        
    Returns:
        Tuple of (path, row)
    """
    # WRS-2 parameters
    # Path calculation (based on longitude)
    # Paths are numbered 1-233, starting at 180 degrees west
    path = int((180.0 + lon) / 7.5) + 1
    
    # Ensure path is in valid range
    if path < 1:
        path = 233 + path  # Wrap around
    elif path > 233:
        path = path - 233
    
    # Row calculation (based on latitude)
    # Rows are numbered differently for ascending vs descending orbits
    # This is a simplified calculation
    if lat >= 0:  # Northern hemisphere
        row = int((80.0 - lat) / 0.05) + 1
    else:  # Southern hemisphere
        row = int((80.0 + abs(lat)) / 0.05) + 1
    
    # Row range is approximately 1-248
    row = max(1, min(248, row))
    
    return (path, row)


def bbox_to_wrs2_paths_rows(bbox: Tuple[float, float, float, float]) -> List[Tuple[int, int]]:
    """
    Convert a bounding box to a list of WRS-2 Path/Row combinations that cover it.
    
    Args:
        bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
        
    Returns:
        List of (path, row) tuples
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    
    # Get path/row for corners and center
    corners = [
        (min_lat, min_lon),
        (min_lat, max_lon),
        (max_lat, min_lon),
        (max_lat, max_lon),
        ((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)  # Center
    ]
    
    path_rows = set()
    for lat, lon in corners:
        path, row = lat_lon_to_wrs2_path_row(lat, lon)
        path_rows.add((path, row))
    
    # Also check adjacent paths/rows to ensure coverage
    for path, row in list(path_rows):
        for dp in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                new_path = path + dp
                new_row = row + dr
                if 1 <= new_path <= 233 and 1 <= new_row <= 248:
                    path_rows.add((new_path, new_row))
    
    return sorted(list(path_rows))

