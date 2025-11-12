"""
Simple test script using mock data - ready to run!
This demonstrates the full workflow with mock GCPs.
"""

try:
    # Try relative imports first (when run as module: python -m gcp_support.test_with_mock)
    from . import GCPFinder
    from .mock_gcp import MockGCPGenerator
    from .h3_utils import h3_cells_to_bbox
    from .manifest_parser import parse_manifest, get_h3_cells_from_manifest
except ImportError:
    # Fall back to absolute imports (when run directly: python test_with_mock.py)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from gcp_support import GCPFinder
    from gcp_support.mock_gcp import MockGCPGenerator
    from gcp_support.h3_utils import h3_cells_to_bbox
    from gcp_support.manifest_parser import parse_manifest, get_h3_cells_from_manifest

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


def main():
    print("=" * 70)
    print("GCP Support - Testing with Mock Data")
    print("=" * 70)
    print()
    
    # Create output directory
    output_dir = './gcps_output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(output_dir, f'test_with_mock_{timestamp}.log')
    
    # Set up dual output (console + log file)
    tee = TeeOutput(log_file)
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        print("=" * 70)
        print("GCP Support - Testing with Mock Data")
        print(f"Log file: {log_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # Get H3 cells and bounding box from manifest file
        manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
        h3_cells, prefix = parse_manifest(manifest_path)
        print(f"Parsed manifest: {len(h3_cells)} H3 cell(s) found")
        print(f"  H3 cells: {h3_cells}")
        if prefix:
            print(f"  S3 prefix: {prefix}")
        print()
        
        # Get bounding box from H3 cells
        bbox = h3_cells_to_bbox(h3_cells)
        
        # Example 1: Generate mock GCPs from a bounding box
        print("Example 1: Generate mock GCPs from bounding box (from manifest H3 cells)")
        print("-" * 70)
        print(f"Bounding box: {bbox}")
        
        mock_gcps = MockGCPGenerator.generate_gcps_in_bbox(bbox, count=20)
        print(f"Generated {len(mock_gcps)} mock GCPs")
        
        # Export using GCPFinder
        finder = GCPFinder()
        finder.export_all(mock_gcps, output_dir, 'mock_bbox')
        print(f"✓ Exported all formats to {output_dir}/mock_bbox_*\n")
        
        # Example 2: Find GCPs using GCPFinder with H3 cells from manifest
        print("Example 2: Find GCPs using GCPFinder with H3 cells from manifest")
        print("-" * 70)
        print(f"Using H3 cells from manifest: {h3_cells}")
        
        # Find GCPs using the H3 cells
        gcps_from_finder = finder.find_gcps(h3_cells=h3_cells, max_results=20)
        print(f"Found {len(gcps_from_finder)} GCPs using GCPFinder")
        
        # Display spatial distribution metrics if available
        if finder.last_spatial_metrics and len(gcps_from_finder) >= 2:
            metrics = finder.last_spatial_metrics
            print(f"  Spatial distribution metrics:")
            print(f"    Spread score: {metrics.get('spread_score', 0):.3f}")
            print(f"    Confidence score: {metrics.get('confidence_score', 0):.3f}")
        
        # Export
        finder.export_all(gcps_from_finder, output_dir, 'mock_h3')
        print(f"✓ Exported all formats to {output_dir}/mock_h3_*\n")
        
        # Example 3: Test filtering
        print("Example 3: Test GCP filtering")
        print("-" * 70)
        try:
            from .gcp_filter import GCPFilter
        except ImportError:
            from gcp_support.gcp_filter import GCPFilter
        
        # Generate GCPs with varying accuracy
        all_gcps = MockGCPGenerator.generate_gcps_in_bbox(
            bbox, 
            count=30, 
            accuracy_range=(0.1, 3.0)  # Accuracy from 0.1m to 3.0m
        )
        print(f"Generated {len(all_gcps)} GCPs with varying accuracy")
        
        # Filter for high accuracy (<= 1.0m)
        filter_obj = GCPFilter(min_accuracy=1.0)
        filtered_gcps = filter_obj.filter_gcps(all_gcps, bbox=bbox)
        print(f"Filtered to {len(filtered_gcps)} GCPs with accuracy <= 1.0m")
        
        # Display spatial distribution metrics
        if len(filtered_gcps) >= 2:
            try:
                from .gcp_filter import calculate_spatial_distribution_score
            except ImportError:
                from gcp_support.gcp_filter import calculate_spatial_distribution_score
            
            spatial_metrics = calculate_spatial_distribution_score(filtered_gcps, bbox)
            print(f"  Spatial distribution metrics:")
            print(f"    Spread score: {spatial_metrics.get('spread_score', 0):.3f} (0-1, higher is better)")
            print(f"    Confidence score: {spatial_metrics.get('confidence_score', 0):.3f} (0-1, higher is better)")
            print(f"    Convex hull ratio: {spatial_metrics.get('convex_hull_ratio', 0):.3f}")
            print(f"    Grid coverage: {spatial_metrics.get('grid_coverage', 0):.3f}")
        
        # Export filtered results
        finder.export_all(filtered_gcps, output_dir, 'mock_filtered')
        print(f"✓ Exported filtered GCPs to {output_dir}/mock_filtered_*\n")
        
        # Example 4: Test spatial distribution filtering
        print("Example 4: Test spatial distribution filtering")
        print("-" * 70)
        
        # Generate clustered GCPs (simulate poor distribution)
        # Make them more clustered by using a smaller area in the center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        small_bbox = (
            center_lat - (bbox[2] - bbox[0]) * 0.1,
            center_lon - (bbox[3] - bbox[1]) * 0.1,
            center_lat + (bbox[2] - bbox[0]) * 0.1,
            center_lon + (bbox[3] - bbox[1]) * 0.1
        )
        clustered_gcps = MockGCPGenerator.generate_gcps_in_bbox(small_bbox, count=15)
        
        # Test with spatial distribution filter
        finder_with_filter = GCPFinder(min_confidence_score=0.5)
        filtered_clustered = finder_with_filter.find_gcps(bbox=bbox, max_results=20)
        
        # Manually check distribution
        spatial_metrics_clustered = calculate_spatial_distribution_score(clustered_gcps, bbox)
        print(f"Clustered GCPs distribution:")
        print(f"  Spread score: {spatial_metrics_clustered.get('spread_score', 0):.3f}")
        print(f"  Confidence score: {spatial_metrics_clustered.get('confidence_score', 0):.3f}")
        if spatial_metrics_clustered.get('confidence_score', 0) < 0.5:
            print("  ⚠️  Warning: Poor spatial distribution detected!")
        print()
        
        # Example 5: Show what files were created
        print("Example 5: Generated files")
        print("-" * 70)
        files = [f for f in os.listdir(output_dir) if f.startswith('mock_')]
        for file in sorted(files):
            filepath = os.path.join(output_dir, file)
            size = os.path.getsize(filepath)
            print(f"  {file} ({size} bytes)")
        
        print()
        print("=" * 70)
        print("✓ All tests completed successfully!")
        print(f"✓ Check the '{output_dir}' directory for exported files")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log saved to: {log_file}")
        print("=" * 70)
    
    finally:
        # Restore stdout and close log file
        sys.stdout = original_stdout
        tee.close()
        print(f"\nTest log saved to: {log_file}")


if __name__ == '__main__':
    main()

