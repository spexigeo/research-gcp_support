"""
Command-line interface for GCP Support.
"""

import argparse
import sys
from typing import List, Optional

from .gcp_finder import GCPFinder


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Find and export Ground Control Points for drone imagery processing'
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--h3-cells',
        nargs='+',
        help='H3 cell identifiers'
    )
    input_group.add_argument(
        '--bbox',
        nargs=4,
        type=float,
        metavar=('MIN_LAT', 'MIN_LON', 'MAX_LAT', 'MAX_LON'),
        help='Bounding box as min_lat min_lon max_lat max_lon'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        default='./gcps',
        help='Output directory for GCP files (default: ./gcps)'
    )
    parser.add_argument(
        '--base-name',
        default='gcps',
        help='Base name for output files (default: gcps)'
    )
    parser.add_argument(
        '--format',
        choices=['all', 'metashape', 'arcgis'],
        default='all',
        help='Output format (default: all)'
    )
    
    # Filtering options
    parser.add_argument(
        '--min-accuracy',
        type=float,
        default=1.0,
        help='Minimum geometric accuracy in meters (default: 1.0)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Maximum number of GCPs to return (default: 100)'
    )
    parser.add_argument(
        '--min-gcp-threshold',
        type=int,
        default=10,
        help='Minimum number of GCPs from USGS before searching NOAA (default: 10)'
    )
    
    # USGS credentials (optional)
    parser.add_argument(
        '--usgs-username',
        help='USGS EarthExplorer username'
    )
    parser.add_argument(
        '--usgs-password',
        help='USGS EarthExplorer password'
    )
    
    # NOAA credentials (optional)
    parser.add_argument(
        '--noaa-api-key',
        help='NOAA API key'
    )
    
    # Other options
    parser.add_argument(
        '--no-wrs2',
        action='store_true',
        help='Do not use WRS-2 Path/Row for searching'
    )
    
    args = parser.parse_args()
    
    # Initialize finder
    finder = GCPFinder(
        usgs_username=args.usgs_username,
        usgs_password=args.usgs_password,
        noaa_api_key=args.noaa_api_key,
        min_accuracy=args.min_accuracy,
        min_gcp_threshold=args.min_gcp_threshold
    )
    
    # Get bounding box
    if args.h3_cells:
        print(f"Processing {len(args.h3_cells)} H3 cells...")
        bbox = finder.h3_cells_to_bbox(args.h3_cells)
        h3_cells = args.h3_cells
        print(f"Bounding box: {bbox}")
    else:
        bbox = tuple(args.bbox)
        h3_cells = None
        print(f"Using bounding box: {bbox}")
    
    # Find GCPs
    print("Searching for GCPs...")
    gcps = finder.find_gcps(
        bbox=bbox if not args.h3_cells else None,
        h3_cells=h3_cells,
        use_wrs2=not args.no_wrs2,
        max_results=args.max_results,
        min_gcp_threshold=args.min_gcp_threshold
    )
    
    print(f"Found {len(gcps)} GCPs after filtering")
    
    if len(gcps) == 0:
        print("Warning: No GCPs found. You may need to:")
        print("  1. Configure the USGS API endpoint")
        print("  2. Check your bounding box/H3 cells")
        print("  3. Adjust filtering criteria")
        sys.exit(1)
    
    # Export GCPs
    print(f"Exporting GCPs to {args.output_dir}...")
    
    if args.format == 'all':
        finder.export_all(gcps, args.output_dir, args.base_name)
    elif args.format == 'metashape':
        finder.export_metashape(
            gcps,
            f"{args.output_dir}/{args.base_name}_metashape.txt"
        )
    elif args.format == 'arcgis':
        finder.export_arcgis(
            gcps,
            f"{args.output_dir}/{args.base_name}_arcgis.csv"
        )
    
    print("Done!")


if __name__ == '__main__':
    main()

