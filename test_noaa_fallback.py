"""
Test script to demonstrate NOAA fallback functionality.
"""

try:
    from . import GCPFinder
    from .mock_gcp import MockGCPGenerator
    from .manifest_parser import get_h3_cells_from_manifest
    from .h3_utils import h3_cells_to_bbox
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from gcp_support import GCPFinder
    from gcp_support.mock_gcp import MockGCPGenerator
    from gcp_support.manifest_parser import get_h3_cells_from_manifest
    from gcp_support.h3_utils import h3_cells_to_bbox

import os
import sys
from datetime import datetime


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


def test_noaa_fallback():
    """Test that NOAA is searched when USGS returns few GCPs."""
    # Create output directory and log file
    output_dir = './gcps_output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(output_dir, f'test_noaa_fallback_{timestamp}.log')
    
    # Set up dual output (console + log file)
    tee = TeeOutput(log_file)
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        print("=" * 70)
        print("Testing NOAA Fallback Functionality")
        print(f"Log file: {log_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # Get H3 cells and bounding box from manifest file
        manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
        h3_cells = get_h3_cells_from_manifest(manifest_path)
        bbox = h3_cells_to_bbox(h3_cells)
        
        print(f"Using H3 cells from manifest: {h3_cells}")
        print(f"Bounding box: {bbox}")
        print()
        
        # Test 1: Low threshold - should trigger NOAA search
        print("Test 1: Threshold = 5, USGS returns 3 GCPs (should search NOAA)")
        print("-" * 70)
        finder = GCPFinder(min_gcp_threshold=5)
        
        # Temporarily modify USGS client to return fewer GCPs
        original_find = finder.usgs_client.find_gcps_by_bbox
        def limited_usgs_find(bbox, max_results):
            gcps = original_find(bbox, max_results)
            return gcps[:3]  # Return only 3 GCPs
        finder.usgs_client.find_gcps_by_bbox = limited_usgs_find
        
        gcps = finder.find_gcps(h3_cells=h3_cells, max_results=20, min_gcp_threshold=5)
        print(f"Result: Found {len(gcps)} total GCPs")
        print()
        
        # Test 2: High threshold - should NOT trigger NOAA search
        print("Test 2: Threshold = 5, USGS returns 10 GCPs (should NOT search NOAA)")
        print("-" * 70)
        finder2 = GCPFinder(min_gcp_threshold=5)
        
        # Temporarily modify USGS client to return more GCPs
        original_find2 = finder2.usgs_client.find_gcps_by_bbox
        def many_usgs_find(bbox, max_results):
            gcps = original_find2(bbox, max_results)
            return gcps[:10]  # Return 10 GCPs
        finder2.usgs_client.find_gcps_by_bbox = many_usgs_find
        
        gcps2 = finder2.find_gcps(h3_cells=h3_cells, max_results=20, min_gcp_threshold=5)
        print(f"Result: Found {len(gcps2)} total GCPs")
        print()
        
        # Test 3: Custom threshold in find_gcps call
        print("Test 3: Override threshold in find_gcps call (threshold = 15)")
        print("-" * 70)
        finder3 = GCPFinder(min_gcp_threshold=10)  # Default is 10
        gcps3 = finder3.find_gcps(h3_cells=h3_cells, max_results=20, min_gcp_threshold=15)
        print(f"Result: Found {len(gcps3)} total GCPs")
        print()
        
        print("=" * 70)
        print("✓ NOAA fallback tests completed!")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log saved to: {log_file}")
        print("=" * 70)
    
    finally:
        # Restore stdout and close log file
        sys.stdout = original_stdout
        tee.close()
        print(f"\nTest log saved to: {log_file}")


if __name__ == '__main__':
    test_noaa_fallback()



