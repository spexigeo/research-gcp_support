"""
Example usage of the GCP Support library.
"""

try:
    # Try relative imports first (when run as module)
    from . import GCPFinder, h3_cells_to_bbox
except ImportError:
    # Fall back to absolute imports (when run directly)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from research_gcp_support import GCPFinder, h3_cells_to_bbox


def example_from_h3_cells():
    """Example: Find GCPs from H3 cells."""
    # Initialize finder
    finder = GCPFinder(min_accuracy=1.0)
    
    # Example H3 cells (replace with your actual cells)
    # Generate valid H3 cells for New York area
    import h3
    test_lat, test_lon = 40.7, -74.0
    h3_cells = [
        h3.latlng_to_cell(test_lat, test_lon, 8),
        h3.latlng_to_cell(test_lat + 0.01, test_lon + 0.01, 8)
    ]
    
    # Get bounding box
    bbox = finder.h3_cells_to_bbox(h3_cells)
    print(f"Bounding box: {bbox}")
    
    # Find GCPs
    gcps = finder.find_gcps(h3_cells=h3_cells, max_results=50)
    print(f"Found {len(gcps)} GCPs")
    
    # Export for MetaShape
    finder.export_metashape(gcps, 'gcps_metashape.txt')
    print("Exported to gcps_metashape.txt")
    
    # Export for ArcGIS Pro
    finder.export_arcgis(gcps, 'gcps_arcgis.csv')
    print("Exported to gcps_arcgis.csv")
    
    # Export all formats
    finder.export_all(gcps, './gcps_output', 'my_gcps')
    print("Exported all formats to ./gcps_output/")


def example_from_bbox():
    """Example: Find GCPs from bounding box."""
    finder = GCPFinder(min_accuracy=0.5)  # Stricter accuracy requirement
    
    # Example bounding box: New York City area
    bbox = (40.5, -74.3, 40.9, -73.7)  # min_lat, min_lon, max_lat, max_lon
    
    # Find GCPs
    gcps = finder.find_gcps(bbox=bbox, max_results=100)
    print(f"Found {len(gcps)} GCPs")
    
    # Export
    finder.export_all(gcps, './gcps_output', 'nyc_gcps')


def example_with_filtering():
    """Example: Custom filtering."""
    try:
        from .gcp_filter import GCPFilter
        from .h3_utils import h3_cells_to_polygon
    except ImportError:
        from research_gcp_support.gcp_filter import GCPFilter
        from research_gcp_support.h3_utils import h3_cells_to_polygon
    
    finder = GCPFinder()
    
    import h3
    h3_cells = [h3.latlng_to_cell(40.7, -74.0, 8)]
    bbox = finder.h3_cells_to_bbox(h3_cells)
    
    # Get target area polygon
    target_area = h3_cells_to_polygon(h3_cells)
    
    # Find GCPs
    gcps = finder.find_gcps(h3_cells=h3_cells)
    
    # Apply additional custom filtering
    custom_filter = GCPFilter(
        min_accuracy=0.5,
        require_photo_identifiable=True,
        target_area=target_area
    )
    
    filtered_gcps = custom_filter.filter_gcps(gcps)
    print(f"Filtered from {len(gcps)} to {len(filtered_gcps)} GCPs")
    
    finder.export_all(filtered_gcps, './gcps_output', 'filtered_gcps')


if __name__ == '__main__':
    print("GCP Support Example")
    print("=" * 50)
    
    # Note: These examples require the USGS API to be configured
    # See USGS_API_NOTES.md for configuration instructions
    
    print("\nExample 1: From H3 cells")
    print("-" * 50)
    try:
        example_from_h3_cells()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: USGS API needs to be configured. See USGS_API_NOTES.md")
    
    print("\nExample 2: From bounding box")
    print("-" * 50)
    try:
        example_from_bbox()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: USGS API needs to be configured. See USGS_API_NOTES.md")

