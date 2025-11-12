"""
Utilities for working with H3 cells and converting them to bounding boxes.
"""

import h3
from typing import List, Tuple
import numpy as np


def h3_cells_to_bbox(h3_cells: List[str]) -> Tuple[float, float, float, float]:
    """
    Convert a list of H3 cell identifiers to a latitude/longitude bounding box.
    
    Args:
        h3_cells: List of H3 cell identifiers (hex strings)
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    if not h3_cells:
        raise ValueError("H3 cells list cannot be empty")
    
    all_lats = []
    all_lons = []
    
    for cell in h3_cells:
        # Validate H3 cell
        if not h3.is_valid_cell(cell):
            raise ValueError(f"Invalid H3 cell: {cell}")
        
        # Get cell boundary (tuple of (lat, lng) tuples)
        boundary = h3.cell_to_boundary(cell)
        
        # Extract latitudes and longitudes
        for lat, lon in boundary:
            all_lats.append(lat)
            all_lons.append(lon)
    
    min_lat = min(all_lats)
    max_lat = max(all_lats)
    min_lon = min(all_lons)
    max_lon = max(all_lons)
    
    return (min_lat, min_lon, max_lat, max_lon)


def h3_cells_to_polygon(h3_cells: List[str]):
    """
    Convert H3 cells to a Shapely polygon representing the union of all cells.
    
    Args:
        h3_cells: List of H3 cell identifiers
        
    Returns:
        Shapely Polygon or MultiPolygon
    """
    from shapely.geometry import Polygon, MultiPolygon
    
    polygons = []
    
    for cell in h3_cells:
        if not h3.is_valid_cell(cell):
            continue
        
        boundary = h3.cell_to_boundary(cell)
        # Convert to Shapely polygon
        coords = [(lon, lat) for lat, lon in boundary]  # Shapely uses (x, y) = (lon, lat)
        polygons.append(Polygon(coords))
    
    if not polygons:
        raise ValueError("No valid polygons created from H3 cells")
    
    # Union all polygons
    from shapely.ops import unary_union
    result = unary_union(polygons)
    
    return result

