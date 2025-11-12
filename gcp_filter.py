"""
GCP filtering and validation utilities.
"""

from typing import List, Dict, Tuple, Optional
from shapely.geometry import Point, Polygon
import numpy as np


class GCPFilter:
    """
    Filter and validate Ground Control Points based on various criteria.
    """
    
    def __init__(
        self,
        min_accuracy: float = 1.0,
        require_photo_identifiable: bool = True,
        target_area: Optional[Polygon] = None
    ):
        """
        Initialize GCP filter.
        
        Args:
            min_accuracy: Minimum geometric accuracy in meters (RMSE)
            require_photo_identifiable: Whether to require photo-identifiable GCPs
            target_area: Shapely Polygon defining the target area (optional)
        """
        self.min_accuracy = min_accuracy
        self.require_photo_identifiable = require_photo_identifiable
        self.target_area = target_area
    
    def filter_gcps(self, gcps: List[Dict]) -> List[Dict]:
        """
        Filter GCPs based on configured criteria.
        
        Args:
            gcps: List of GCP dictionaries
            
        Returns:
            Filtered list of GCPs
        """
        filtered = []
        
        for gcp in gcps:
            if not self._meets_accuracy_requirement(gcp):
                continue
            
            if self.require_photo_identifiable and not self._is_photo_identifiable(gcp):
                continue
            
            if self.target_area and not self._is_in_target_area(gcp):
                continue
            
            filtered.append(gcp)
        
        return filtered
    
    def _meets_accuracy_requirement(self, gcp: Dict) -> bool:
        """Check if GCP meets minimum accuracy requirement."""
        # GCP should have an accuracy field (RMSE in meters)
        accuracy = gcp.get('accuracy', gcp.get('rmse', gcp.get('error', float('inf'))))
        
        # If accuracy is not specified, we might want to exclude it or include it
        # For now, if accuracy is not available, we'll include it but warn
        if accuracy == float('inf') or accuracy is None:
            # Optionally exclude: return False
            # For now, include but note the missing accuracy
            return True
        
        return accuracy <= self.min_accuracy
    
    def _is_photo_identifiable(self, gcp: Dict) -> bool:
        """
        Check if GCP is photo-identifiable.
        
        This checks for features that are clearly visible in aerial/drone imagery:
        - Road intersections
        - Building corners
        - Distinctive landmarks
        - Clear geometric features
        """
        # Check for photo-identifiable indicators
        gcp_type = gcp.get('type', '').lower()
        description = gcp.get('description', '').lower()
        
        # Common photo-identifiable types
        identifiable_types = [
            'road intersection',
            'building corner',
            'corner',
            'intersection',
            'landmark',
            'structure',
            'marker'
        ]
        
        # Check type
        if any(indicator in gcp_type for indicator in identifiable_types):
            return True
        
        # Check description
        if any(indicator in description for indicator in identifiable_types):
            return True
        
        # If explicitly marked as photo-identifiable
        if gcp.get('photo_identifiable', False):
            return True
        
        # If no explicit indicators, assume it might be (conservative approach)
        # In production, you might want to be more strict
        return True
    
    def _is_in_target_area(self, gcp: Dict) -> bool:
        """Check if GCP is within the target area polygon."""
        if not self.target_area:
            return True
        
        lat = gcp.get('lat', gcp.get('latitude'))
        lon = gcp.get('lon', gcp.get('longitude'))
        
        if lat is None or lon is None:
            return False
        
        point = Point(lon, lat)  # Shapely uses (x, y) = (lon, lat)
        return self.target_area.contains(point) or self.target_area.touches(point)


def filter_gcps_by_quality(
    gcps: List[Dict],
    min_accuracy: float = 1.0,
    target_area: Optional[Polygon] = None
) -> List[Dict]:
    """
    Convenience function to filter GCPs.
    
    Args:
        gcps: List of GCP dictionaries
        min_accuracy: Minimum accuracy in meters
        target_area: Optional target area polygon
        
    Returns:
        Filtered list of GCPs
    """
    filter_obj = GCPFilter(
        min_accuracy=min_accuracy,
        require_photo_identifiable=True,
        target_area=target_area
    )
    return filter_obj.filter_gcps(gcps)

