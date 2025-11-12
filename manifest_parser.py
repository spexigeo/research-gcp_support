"""
Utility to parse input manifest files and extract H3 cell information.
"""

import json
import os
from typing import List, Set, Tuple, Optional
import re


def parse_manifest(manifest_path: str) -> Tuple[List[str], Optional[str]]:
    """
    Parse a manifest file and extract H3 cell identifiers.
    
    The manifest file is a JSON array containing:
    - First element: dict with "prefix" key (S3 path)
    - Remaining elements: image filenames in format "h3cell_flightnumber_imageID.jpg"
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Tuple of (list of unique H3 cells, prefix string)
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    if not isinstance(manifest_data, list) or len(manifest_data) == 0:
        raise ValueError("Manifest must be a non-empty JSON array")
    
    # Extract prefix (first element should be a dict with "prefix" key)
    prefix = None
    if isinstance(manifest_data[0], dict) and "prefix" in manifest_data[0]:
        prefix = manifest_data[0]["prefix"]
        # Extract H3 cell from prefix path if present
        # Format: s3://bucket/path/h3cell/flightnumber/
        prefix_h3_match = re.search(r'/([0-9a-f]{15})/', prefix)
        if prefix_h3_match:
            prefix_h3 = prefix_h3_match.group(1)
        else:
            prefix_h3 = None
    else:
        prefix_h3 = None
    
    # Extract H3 cells from filenames
    # Format: "h3cell_flightnumber_imageID.jpg"
    h3_cells: Set[str] = set()
    
    # Pattern to match H3 cell at start of filename (15 hex characters)
    h3_pattern = re.compile(r'^([0-9a-f]{15})_')
    
    for item in manifest_data[1:]:  # Skip first element (prefix)
        if isinstance(item, str):
            # Try to extract H3 cell from filename
            match = h3_pattern.match(item)
            if match:
                h3_cell = match.group(1)
                h3_cells.add(h3_cell)
    
    # Add prefix H3 cell if found and different
    if prefix_h3:
        h3_cells.add(prefix_h3)
    
    if not h3_cells:
        raise ValueError("No H3 cells found in manifest file")
    
    return sorted(list(h3_cells)), prefix


def get_h3_cells_from_manifest(manifest_path: str) -> List[str]:
    """
    Convenience function to get just the H3 cells from a manifest file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        List of unique H3 cell identifiers
    """
    h3_cells, _ = parse_manifest(manifest_path)
    return h3_cells

