"""
Main GCP finder class that orchestrates the entire workflow.
"""

from typing import List, Dict, Tuple, Optional
import os

from .h3_utils import h3_cells_to_bbox, h3_cells_to_polygon
from .wrs2_utils import bbox_to_wrs2_paths_rows
from .usgs_gcp import USGSGCPClient, AlternativeGCPClient
from .noaa_gcp import NOAAGCPClient
from .gcp_filter import GCPFilter
from .exporters import MetaShapeExporter, ArcGISExporter


class GCPFinder:
    """
    Main class for finding and exporting Ground Control Points.
    """
    
    def __init__(
        self,
        usgs_username: Optional[str] = None,
        usgs_password: Optional[str] = None,
        usgs_application_token: Optional[str] = None,
        noaa_api_key: Optional[str] = None,
        min_accuracy: float = 1.0,
        require_photo_identifiable: bool = True,
        min_gcp_threshold: int = 10,
        min_spread_score: Optional[float] = None,
        min_confidence_score: Optional[float] = None
    ):
        """
        Initialize GCP finder.
        
        Args:
            usgs_username: USGS EarthExplorer username (DEPRECATED - use usgs_application_token)
            usgs_password: USGS EarthExplorer password (DEPRECATED - use usgs_application_token)
            usgs_application_token: USGS application token (NEW METHOD - recommended)
            noaa_api_key: NOAA API key (optional, currently not required for NGS archive)
            min_accuracy: Minimum geometric accuracy in meters
            require_photo_identifiable: Whether to require photo-identifiable GCPs
            min_gcp_threshold: Minimum number of GCPs from USGS before searching NOAA (default: 10)
            min_spread_score: Minimum spatial spread score (0-1). If None, only warns.
            min_confidence_score: Minimum confidence score (0-1). If None, only warns.
        """
        self.usgs_client = USGSGCPClient(
            username=usgs_username, 
            password=usgs_password,
            application_token=usgs_application_token
        )
        self.noaa_client = NOAAGCPClient(api_key=noaa_api_key)
        self.min_accuracy = min_accuracy
        self.require_photo_identifiable = require_photo_identifiable
        self.min_gcp_threshold = min_gcp_threshold
        self.min_spread_score = min_spread_score
        self.min_confidence_score = min_confidence_score
        self.last_spatial_metrics = None  # Store spatial metrics from last filter operation
    
    def h3_cells_to_bbox(self, h3_cells: List[str]) -> Tuple[float, float, float, float]:
        """
        Convert H3 cells to bounding box.
        
        Args:
            h3_cells: List of H3 cell identifiers
            
        Returns:
            Tuple of (min_lat, min_lon, max_lat, max_lon)
        """
        return h3_cells_to_bbox(h3_cells)
    
    def find_gcps(
        self,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        h3_cells: Optional[List[str]] = None,
        use_wrs2: bool = True,
        max_results: int = 100,
        min_gcp_threshold: Optional[int] = None
    ) -> List[Dict]:
        """
        Find GCPs for a given area.
        
        Searches USGS first, then NOAA if the number of GCPs found is below
        the threshold.
        
        Args:
            bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
            h3_cells: List of H3 cell identifiers (alternative to bbox)
            use_wrs2: Whether to use WRS-2 Path/Row for searching
            max_results: Maximum number of GCPs to return
            min_gcp_threshold: Override the default threshold for searching NOAA
            
        Returns:
            List of filtered GCP dictionaries
        """
        # Use provided threshold or default
        threshold = min_gcp_threshold if min_gcp_threshold is not None else self.min_gcp_threshold
        
        # Get bounding box
        if bbox is None:
            if h3_cells is None:
                raise ValueError("Either bbox or h3_cells must be provided")
            bbox = self.h3_cells_to_bbox(h3_cells)
        
        # Get target area polygon for filtering
        target_area = None
        if h3_cells:
            try:
                target_area = h3_cells_to_polygon(h3_cells)
            except Exception as e:
                print(f"Warning: Could not create target area polygon: {e}")
        
        # Step 1: Search USGS (primary source)
        print("Searching USGS for GCPs...")
        usgs_gcps = []
        
        if use_wrs2:
            # Try finding GCPs by WRS-2 Path/Row
            path_rows = bbox_to_wrs2_paths_rows(bbox)
            print(f"  Searching {len(path_rows)} WRS-2 Path/Row combinations...")
            
            for path, row in path_rows:
                gcps = self.usgs_client.find_gcps_by_wrs2(path, row, max_results)
                usgs_gcps.extend(gcps)
        
        # Also search by bounding box
        bbox_gcps = self.usgs_client.find_gcps_by_bbox(bbox, max_results)
        usgs_gcps.extend(bbox_gcps)
        
        # Remove duplicates from USGS results
        unique_usgs_gcps = self._deduplicate_gcps(usgs_gcps)
        print(f"  Found {len(unique_usgs_gcps)} GCPs from USGS")
        
        # Step 2: Check if we need to search NOAA
        all_gcps = unique_usgs_gcps.copy()
        
        if len(unique_usgs_gcps) < threshold:
            print(f"  USGS results ({len(unique_usgs_gcps)}) below threshold ({threshold})")
            print("  Searching NOAA for additional GCPs...")
            
            # Search NOAA
            noaa_gcps = self.noaa_client.find_gcps_by_bbox(bbox, max_results)
            print(f"  Found {len(noaa_gcps)} GCPs from NOAA")
            
            # Combine USGS and NOAA results
            all_gcps.extend(noaa_gcps)
            
            # Remove duplicates across both sources
            all_gcps = self._deduplicate_gcps(all_gcps)
            print(f"  Total unique GCPs after combining sources: {len(all_gcps)}")
        else:
            print(f"  USGS results ({len(unique_usgs_gcps)}) meet threshold ({threshold}), skipping NOAA search")
        
        # Filter GCPs
        filter_obj = GCPFilter(
            min_accuracy=self.min_accuracy,
            require_photo_identifiable=self.require_photo_identifiable,
            target_area=target_area,
            min_spread_score=self.min_spread_score,
            min_confidence_score=self.min_confidence_score
        )
        filtered_gcps = filter_obj.filter_gcps(all_gcps, bbox=bbox)
        
        # Store spatial metrics for access later
        self.last_spatial_metrics = getattr(filter_obj, 'last_spatial_metrics', None)
        
        # Print spatial distribution summary if available
        if self.last_spatial_metrics and len(filtered_gcps) >= 2:
            metrics = self.last_spatial_metrics
            print(f"  Spatial distribution metrics:")
            print(f"    Spread score: {metrics.get('spread_score', 0):.3f} (0-1, higher is better)")
            print(f"    Confidence score: {metrics.get('confidence_score', 0):.3f} (0-1, higher is better)")
            print(f"    Convex hull ratio: {metrics.get('convex_hull_ratio', 0):.3f}")
            print(f"    Grid coverage: {metrics.get('grid_coverage', 0):.3f}")
        
        print(f"  Final filtered GCPs: {len(filtered_gcps)}")
        
        return filtered_gcps
    
    def _deduplicate_gcps(self, gcps: List[Dict]) -> List[Dict]:
        """Remove duplicate GCPs based on ID or location."""
        seen = set()
        unique = []
        
        for gcp in gcps:
            # Try to use ID first
            gcp_id = gcp.get('id', gcp.get('label'))
            if gcp_id:
                if gcp_id in seen:
                    continue
                seen.add(gcp_id)
            else:
                # Use location as fallback
                lat = gcp.get('lat', gcp.get('latitude'))
                lon = gcp.get('lon', gcp.get('longitude'))
                if lat is not None and lon is not None:
                    location_key = (round(lat, 6), round(lon, 6))  # Round to ~0.1m
                    if location_key in seen:
                        continue
                    seen.add(location_key)
            
            unique.append(gcp)
        
        return unique
    
    def export_metashape(
        self,
        gcps: List[Dict],
        output_path: str,
        format: str = 'csv'
    ):
        """
        Export GCPs for MetaShape.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output file
            format: Export format ('csv' or 'xml')
        """
        if format == 'xml':
            MetaShapeExporter.export_marker_file(gcps, output_path)
        else:
            MetaShapeExporter.export(gcps, output_path)
    
    def export_arcgis(
        self,
        gcps: List[Dict],
        output_path: str,
        format: str = 'csv'
    ):
        """
        Export GCPs for ArcGIS Pro.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output file
            format: Export format ('csv', 'shp', or 'geojson')
        """
        if format == 'shp':
            ArcGISExporter.export_shapefile(gcps, output_path)
        elif format == 'geojson':
            ArcGISExporter.export_geojson(gcps, output_path)
        else:
            ArcGISExporter.export_csv(gcps, output_path)
    
    def export_all(
        self,
        gcps: List[Dict],
        output_dir: str,
        base_name: str = 'gcps'
    ):
        """
        Export GCPs in all supported formats.
        
        Args:
            gcps: List of GCP dictionaries
            output_dir: Directory to save output files
            base_name: Base name for output files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # MetaShape formats
        self.export_metashape(gcps, os.path.join(output_dir, f'{base_name}_metashape.txt'), 'csv')
        self.export_metashape(gcps, os.path.join(output_dir, f'{base_name}_metashape.xml'), 'xml')
        
        # ArcGIS formats
        self.export_arcgis(gcps, os.path.join(output_dir, f'{base_name}_arcgis.csv'), 'csv')
        self.export_arcgis(gcps, os.path.join(output_dir, f'{base_name}_arcgis.geojson'), 'geojson')
        
        # Try shapefile (may fail if geopandas not available)
        try:
            self.export_arcgis(gcps, os.path.join(output_dir, f'{base_name}_arcgis.shp'), 'shp')
        except Exception as e:
            print(f"Warning: Could not export shapefile: {e}")

