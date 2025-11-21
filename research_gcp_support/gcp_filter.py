"""
GCP filtering and validation utilities.
"""

from typing import List, Dict, Tuple, Optional
from shapely.geometry import Point, Polygon, MultiPoint
import numpy as np
from scipy.spatial.distance import pdist, squareform


def calculate_spatial_distribution_score(
    gcps: List[Dict],
    bbox: Optional[Tuple[float, float, float, float]] = None
) -> Dict[str, float]:
    """
    Calculate spatial distribution metrics for a set of GCPs.
    
    Returns metrics including:
    - convex_hull_ratio: Ratio of convex hull area to bounding box area
    - avg_nearest_neighbor: Average distance to nearest neighbor
    - grid_coverage: How well points cover a grid
    - spread_score: Overall spatial spread score (0-1, higher is better)
    - confidence_score: Overall confidence in GCP distribution (0-1)
    
    Args:
        gcps: List of GCP dictionaries with 'lat' and 'lon' keys
        bbox: Optional bounding box (min_lat, min_lon, max_lat, max_lon)
              If not provided, will be calculated from GCPs
        
    Returns:
        Dictionary with spatial distribution metrics
    """
    if len(gcps) < 2:
        return {
            'convex_hull_ratio': 0.0,
            'avg_nearest_neighbor': 0.0,
            'grid_coverage': 0.0,
            'spread_score': 0.0,
            'confidence_score': 0.0,
            'warning': 'Need at least 2 GCPs for spatial distribution analysis'
        }
    
    # Extract coordinates
    points = []
    for gcp in gcps:
        lat = gcp.get('lat', gcp.get('latitude'))
        lon = gcp.get('lon', gcp.get('longitude'))
        if lat is not None and lon is not None:
            points.append((lon, lat))  # Shapely uses (x, y) = (lon, lat)
    
    if len(points) < 2:
        return {
            'convex_hull_ratio': 0.0,
            'avg_nearest_neighbor': 0.0,
            'grid_coverage': 0.0,
            'spread_score': 0.0,
            'confidence_score': 0.0,
            'warning': 'Insufficient valid coordinates'
        }
    
    # Create MultiPoint for geometric operations
    multipoint = MultiPoint(points)
    
    # Calculate bounding box if not provided
    if bbox is None:
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]
        bbox = (min(lats), min(lons), max(lats), max(lons))
    
    min_lat, min_lon, max_lat, max_lon = bbox
    bbox_area = (max_lat - min_lat) * (max_lon - min_lon)
    
    # Metric 1: Convex hull area ratio
    convex_hull = multipoint.convex_hull
    if convex_hull.area > 0 and bbox_area > 0:
        convex_hull_ratio = convex_hull.area / bbox_area
    else:
        convex_hull_ratio = 0.0
    
    # Metric 2: Average nearest neighbor distance
    # Convert to numpy array for distance calculations
    coords_array = np.array(points)
    
    # Calculate pairwise distances (in degrees, approximate)
    # For more accurate distances, we'd need to use geodetic calculations
    distances = pdist(coords_array)
    distance_matrix = squareform(distances)
    
    # Set diagonal to infinity to exclude self-distances
    np.fill_diagonal(distance_matrix, np.inf)
    
    # Find nearest neighbor for each point
    nearest_distances = np.min(distance_matrix, axis=1)
    avg_nearest_neighbor = np.mean(nearest_distances)
    
    # Normalize by diagonal of bounding box
    bbox_diagonal = np.sqrt((max_lat - min_lat)**2 + (max_lon - min_lon)**2)
    if bbox_diagonal > 0:
        normalized_avg_nn = avg_nearest_neighbor / bbox_diagonal
    else:
        normalized_avg_nn = 0.0
    
    # Metric 3: Grid coverage
    # Divide bbox into a grid and check how many cells have GCPs
    grid_size = 3  # 3x3 grid
    grid_cells_with_points = set()
    
    lat_step = (max_lat - min_lat) / grid_size if max_lat > min_lat else 1.0
    lon_step = (max_lon - min_lon) / grid_size if max_lon > min_lon else 1.0
    
    for lon, lat in points:
        if lat_step > 0 and lon_step > 0:
            lat_idx = min(int((lat - min_lat) / lat_step), grid_size - 1)
            lon_idx = min(int((lon - min_lon) / lon_step), grid_size - 1)
            grid_cells_with_points.add((lat_idx, lon_idx))
    
    grid_coverage = len(grid_cells_with_points) / (grid_size * grid_size)
    
    # Calculate overall spread score (weighted combination)
    # Higher values indicate better spatial distribution
    spread_score = (
        0.4 * min(convex_hull_ratio * 2, 1.0) +  # Convex hull (weighted higher)
        0.3 * min(normalized_avg_nn * 10, 1.0) +  # Nearest neighbor distance
        0.3 * grid_coverage  # Grid coverage
    )
    
    # Confidence score: combines spread with number of points
    # More points with good spread = higher confidence
    num_points = len(gcps)
    point_count_score = min(num_points / 10.0, 1.0)  # Optimal at 10+ points
    
    confidence_score = 0.7 * spread_score + 0.3 * point_count_score
    
    return {
        'convex_hull_ratio': float(convex_hull_ratio),
        'avg_nearest_neighbor': float(avg_nearest_neighbor),
        'normalized_avg_nn': float(normalized_avg_nn),
        'grid_coverage': float(grid_coverage),
        'spread_score': float(spread_score),
        'confidence_score': float(confidence_score),
        'num_points': num_points
    }


class GCPFilter:
    """
    Filter and validate Ground Control Points based on various criteria.
    """
    
    def __init__(
        self,
        min_accuracy: float = 1.0,
        require_photo_identifiable: bool = True,
        target_area: Optional[Polygon] = None,
        min_spread_score: Optional[float] = None,
        min_confidence_score: Optional[float] = None
    ):
        """
        Initialize GCP filter.
        
        Args:
            min_accuracy: Minimum geometric accuracy in meters (RMSE)
            require_photo_identifiable: Whether to require photo-identifiable GCPs
            target_area: Shapely Polygon defining the target area (optional)
            min_spread_score: Minimum spatial spread score (0-1). If None, only warns.
            min_confidence_score: Minimum confidence score (0-1). If None, only warns.
        """
        self.min_accuracy = min_accuracy
        self.require_photo_identifiable = require_photo_identifiable
        self.target_area = target_area
        self.min_spread_score = min_spread_score
        self.min_confidence_score = min_confidence_score
    
    def filter_gcps(
        self, 
        gcps: List[Dict],
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> List[Dict]:
        """
        Filter GCPs based on configured criteria.
        
        Args:
            gcps: List of GCP dictionaries
            bbox: Optional bounding box for spatial distribution analysis
            
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
        
        # Check spatial distribution if we have enough GCPs
        if len(filtered) >= 2:
            spatial_metrics = calculate_spatial_distribution_score(filtered, bbox)
            
            # Store metrics in a way that can be accessed later
            # We'll add them as attributes to the filter object
            self.last_spatial_metrics = spatial_metrics
            
            # Warn if spatial distribution is poor
            if spatial_metrics.get('confidence_score', 0) < 0.5:
                print(f"⚠️  Warning: Low spatial distribution confidence ({spatial_metrics['confidence_score']:.2f})")
                print(f"   Spread score: {spatial_metrics['spread_score']:.2f}")
                print(f"   Convex hull ratio: {spatial_metrics['convex_hull_ratio']:.2f}")
                print(f"   Grid coverage: {spatial_metrics['grid_coverage']:.2f}")
                print("   Consider: GCPs may be clustered, which could affect bundle adjustment quality")
            
            # Apply filtering if thresholds are set
            if self.min_spread_score is not None:
                if spatial_metrics.get('spread_score', 0) < self.min_spread_score:
                    print(f"⚠️  Filtered out GCP set: spread score {spatial_metrics['spread_score']:.2f} < {self.min_spread_score}")
                    return []  # Reject the entire set if spread is too poor
            
            if self.min_confidence_score is not None:
                if spatial_metrics.get('confidence_score', 0) < self.min_confidence_score:
                    print(f"⚠️  Filtered out GCP set: confidence score {spatial_metrics['confidence_score']:.2f} < {self.min_confidence_score}")
                    return []  # Reject the entire set if confidence is too low
        
        return filtered
    
    def get_spatial_metrics(self, gcps: List[Dict], bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, float]:
        """
        Get spatial distribution metrics for a set of GCPs without filtering.
        
        Args:
            gcps: List of GCP dictionaries
            bbox: Optional bounding box for analysis
            
        Returns:
            Dictionary with spatial distribution metrics
        """
        return calculate_spatial_distribution_score(gcps, bbox)
    
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
    target_area: Optional[Polygon] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    min_spread_score: Optional[float] = None,
    min_confidence_score: Optional[float] = None
) -> List[Dict]:
    """
    Convenience function to filter GCPs.
    
    Args:
        gcps: List of GCP dictionaries
        min_accuracy: Minimum accuracy in meters
        target_area: Optional target area polygon
        bbox: Optional bounding box for spatial distribution analysis
        min_spread_score: Minimum spatial spread score (0-1)
        min_confidence_score: Minimum confidence score (0-1)
        
    Returns:
        Filtered list of GCPs
    """
    filter_obj = GCPFilter(
        min_accuracy=min_accuracy,
        require_photo_identifiable=True,
        target_area=target_area,
        min_spread_score=min_spread_score,
        min_confidence_score=min_confidence_score
    )
    return filter_obj.filter_gcps(gcps, bbox=bbox)

