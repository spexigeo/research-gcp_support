"""
Mock GCP generator for testing purposes.
This generates sample GCPs that can be used to test the export and filtering functionality.
"""

import random
from typing import List, Dict, Tuple


class MockGCPGenerator:
    """Generate mock GCPs for testing."""
    
    @staticmethod
    def generate_gcps_in_bbox(
        bbox: Tuple[float, float, float, float],
        count: int = 10,
        accuracy_range: Tuple[float, float] = (0.1, 2.0),
        source: str = 'usgs'
    ) -> List[Dict]:
        """
        Generate mock GCPs within a bounding box.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            count: Number of GCPs to generate
            accuracy_range: Tuple of (min_accuracy, max_accuracy) in meters
            source: Source identifier ('usgs' or 'noaa')
            
        Returns:
            List of mock GCP dictionaries
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        
        gcps = []
        gcp_types = [
            'road intersection',
            'building corner',
            'landmark',
            'structure corner',
            'survey marker'
        ]
        
        for i in range(count):
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            z = random.uniform(0, 500)  # Elevation in meters
            accuracy = random.uniform(accuracy_range[0], accuracy_range[1])
            gcp_type = random.choice(gcp_types)
            
            gcp = {
                'id': f'{source.upper()}_GCP_{i+1:04d}',
                'label': f'{source.upper()}_GCP_{i+1:04d}',
                'lat': lat,
                'lon': lon,
                'latitude': lat,  # Alternative key
                'longitude': lon,  # Alternative key
                'z': z,
                'elevation': z,  # Alternative key
                'altitude': z,  # Alternative key
                'accuracy': accuracy,
                'rmse': accuracy,  # Alternative key
                'type': gcp_type,
                'description': f'{source.upper()} {gcp_type} at {lat:.6f}, {lon:.6f}',
                'photo_identifiable': True,
                'source': source.upper()
            }
            
            gcps.append(gcp)
        
        return gcps
    
    @staticmethod
    def generate_gcps_for_wrs2(
        path: int,
        row: int,
        count: int = 5
    ) -> List[Dict]:
        """
        Generate mock GCPs for a WRS-2 Path/Row.
        
        This is a simplified implementation that generates GCPs in a rough area
        corresponding to the path/row.
        
        Args:
            path: WRS-2 path number
            row: WRS-2 row number
            count: Number of GCPs to generate
            
        Returns:
            List of mock GCP dictionaries
        """
        # Rough approximation of path/row to lat/lon
        # This is simplified - in reality, you'd use proper WRS-2 geometry
        base_lon = -180 + (path - 1) * 7.5
        base_lat = 80 - (row - 1) * 0.05
        
        # Create a small bounding box around the approximate center
        bbox = (
            base_lat - 0.1,
            base_lon - 0.1,
            base_lat + 0.1,
            base_lon + 0.1
        )
        
        return MockGCPGenerator.generate_gcps_in_bbox(bbox, count)

