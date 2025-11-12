"""
Basic test script to verify the GCP support functionality.
"""

import os
import tempfile
import shutil
import sys
from datetime import datetime

try:
    # Try relative imports first (when run as module)
    from . import GCPFinder, h3_cells_to_bbox
    from .mock_gcp import MockGCPGenerator
    from .h3_utils import h3_cells_to_polygon
    from .manifest_parser import parse_manifest, get_h3_cells_from_manifest
except ImportError:
    # Fall back to absolute imports (when run directly)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from gcp_support import GCPFinder, h3_cells_to_bbox
    from gcp_support.mock_gcp import MockGCPGenerator
    from gcp_support.h3_utils import h3_cells_to_polygon
    from gcp_support.manifest_parser import parse_manifest, get_h3_cells_from_manifest


class TeeOutput:
    """Class to write to both console and log file."""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        if self.log:
            self.log.close()


def test_h3_to_bbox():
    """Test H3 cell to bounding box conversion."""
    print("Testing H3 to bounding box conversion...")
    
    # Get H3 cells from manifest file
    manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
    h3_cells = get_h3_cells_from_manifest(manifest_path)
    bbox = h3_cells_to_bbox(h3_cells)
    
    print(f"  H3 cells from manifest: {h3_cells}")
    print(f"  Bounding box: {bbox}")
    assert len(bbox) == 4, "Bounding box should have 4 elements"
    assert bbox[0] < bbox[2], "min_lat should be less than max_lat"
    assert bbox[1] < bbox[3], "min_lon should be less than max_lon"
    print("  ✓ H3 to bbox conversion works\n")


def test_mock_gcp_generation():
    """Test mock GCP generation."""
    print("Testing mock GCP generation...")
    
    # Get bounding box from manifest H3 cells
    manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
    h3_cells = get_h3_cells_from_manifest(manifest_path)
    bbox = h3_cells_to_bbox(h3_cells)
    
    gcps = MockGCPGenerator.generate_gcps_in_bbox(bbox, count=5)
    
    print(f"  Generated {len(gcps)} mock GCPs")
    assert len(gcps) == 5, "Should generate 5 GCPs"
    
    for gcp in gcps:
        assert 'lat' in gcp, "GCP should have 'lat'"
        assert 'lon' in gcp, "GCP should have 'lon'"
        assert 'id' in gcp, "GCP should have 'id'"
        assert bbox[0] <= gcp['lat'] <= bbox[2], "GCP should be within bbox"
        assert bbox[1] <= gcp['lon'] <= bbox[3], "GCP should be within bbox"
    
    print("  ✓ Mock GCP generation works\n")


def test_export_formats():
    """Test export formats."""
    print("Testing export formats...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Get bounding box from manifest H3 cells
        manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
        h3_cells = get_h3_cells_from_manifest(manifest_path)
        bbox = h3_cells_to_bbox(h3_cells)
        
        # Generate mock GCPs
        gcps = MockGCPGenerator.generate_gcps_in_bbox(bbox, count=3)
        
        finder = GCPFinder()
        
        # Test MetaShape export
        metashape_path = os.path.join(temp_dir, 'test_metashape.txt')
        finder.export_metashape(gcps, metashape_path)
        assert os.path.exists(metashape_path), "MetaShape file should be created"
        print(f"  ✓ MetaShape export: {metashape_path}")
        
        # Test ArcGIS CSV export
        arcgis_path = os.path.join(temp_dir, 'test_arcgis.csv')
        finder.export_arcgis(gcps, arcgis_path)
        assert os.path.exists(arcgis_path), "ArcGIS CSV file should be created"
        print(f"  ✓ ArcGIS CSV export: {arcgis_path}")
        
        # Test export all
        finder.export_all(gcps, temp_dir, 'test_all')
        assert os.path.exists(os.path.join(temp_dir, 'test_all_metashape.txt'))
        assert os.path.exists(os.path.join(temp_dir, 'test_all_arcgis.csv'))
        print(f"  ✓ Export all formats works")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("  ✓ Export formats work\n")


def test_gcp_filtering():
    """Test GCP filtering."""
    print("Testing GCP filtering...")
    
    try:
        from .gcp_filter import GCPFilter
    except ImportError:
        from gcp_support.gcp_filter import GCPFilter
    from shapely.geometry import Point, Polygon
    
    # Get bounding box from manifest H3 cells
    manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
    h3_cells = get_h3_cells_from_manifest(manifest_path)
    bbox = h3_cells_to_bbox(h3_cells)
    
    # Generate GCPs with varying accuracy
    gcps = MockGCPGenerator.generate_gcps_in_bbox(bbox, count=10, accuracy_range=(0.1, 5.0))
    
    # Filter for high accuracy
    filter_obj = GCPFilter(min_accuracy=1.0)
    filtered = filter_obj.filter_gcps(gcps)
    
    print(f"  Original: {len(gcps)} GCPs")
    print(f"  Filtered (accuracy <= 1.0m): {len(filtered)} GCPs")
    
    # Verify all filtered GCPs meet criteria
    for gcp in filtered:
        accuracy = gcp.get('accuracy', float('inf'))
        assert accuracy <= 1.0 or accuracy == float('inf'), "Filtered GCPs should meet accuracy requirement"
    
    print("  ✓ GCP filtering works\n")


def main():
    """Run all tests."""
    # Create output directory and log file
    output_dir = './gcps_output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(output_dir, f'test_basic_{timestamp}.log')
    
    # Set up dual output (console + log file)
    tee = TeeOutput(log_file)
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        print("=" * 60)
        print("GCP Support - Basic Functionality Tests")
        print(f"Log file: {log_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        test_h3_to_bbox()
        test_mock_gcp_generation()
        test_export_formats()
        test_gcp_filtering()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log saved to: {log_file}")
        print("=" * 60)
        
        result = 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        result = 1
    
    finally:
        # Restore stdout and close log file
        sys.stdout = original_stdout
        tee.close()
        print(f"\nTest log saved to: {log_file}")
    
    return result


if __name__ == '__main__':
    exit(main())

