"""
USGS Ground Control Point client for downloading GCPs.
"""

import requests
import json
from typing import List, Dict, Tuple, Optional
import time
from urllib.parse import urlencode


class USGSGCPClient:
    """
    Client for accessing USGS Ground Control Points.
    
    Note: USGS GCP data may be available through various APIs or data portals.
    This implementation provides a framework that can be adapted to the specific
    USGS API endpoints available.
    """
    
    BASE_URL = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize USGS GCP client.
        
        Args:
            username: USGS EarthExplorer username (optional, may be required for some endpoints)
            password: USGS EarthExplorer password (optional)
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_key = None
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make a request to the USGS API."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {}
    
    def find_gcps_by_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        max_results: int = 100
    ) -> List[Dict]:
        """
        Find GCPs within a bounding box.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            max_results: Maximum number of GCPs to return
            
        Returns:
            List of GCP dictionaries with keys: lat, lon, id, accuracy, etc.
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        
        # Note: This is a placeholder implementation. The actual USGS API
        # may require different endpoints and parameters. You may need to:
        # 1. Use the EarthExplorer API with proper authentication
        # 2. Query the USGS GCP database directly
        # 3. Use alternative sources like OpenAerialMap or other GCP repositories
        
        # For now, we'll provide a structure that can be adapted
        gcps = []
        
        # Example: If USGS provides a spatial search endpoint
        params = {
            "lowerLeft": {"latitude": min_lat, "longitude": min_lon},
            "upperRight": {"latitude": max_lat, "longitude": max_lon},
            "datasetName": "GCP",  # Dataset identifier
            "maxResults": max_results
        }
        
        # This would need to be adapted to the actual USGS API
        # For demonstration, we'll return an empty list with a note
        print("Note: USGS GCP API integration requires specific endpoint configuration.")
        print("Please configure the actual USGS API endpoint in usgs_gcp.py")
        print("For testing, you can use MockGCPGenerator from mock_gcp.py")
        
        # For testing: use mock data if no real API configured
        # Uncomment the following to use mock data for testing:
        from .mock_gcp import MockGCPGenerator
        return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='usgs')
        
        # return gcps  # Uncomment when real API is configured
    
    def find_gcps_by_wrs2(
        self,
        path: int,
        row: int,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Find GCPs for a specific WRS-2 Path/Row.
        
        Args:
            path: WRS-2 path number
            row: WRS-2 row number
            max_results: Maximum number of GCPs to return
            
        Returns:
            List of GCP dictionaries
        """
        # Similar to bbox search but filtered by WRS-2 path/row
        params = {
            "path": path,
            "row": row,
            "datasetName": "GCP",
            "maxResults": max_results
        }
        
        # For testing: use mock data if no real API configured
        # Uncomment the following to use mock data for testing:
        from .mock_gcp import MockGCPGenerator
        return MockGCPGenerator.generate_gcps_for_wrs2(path, row, max_results)
        
        # return []  # Uncomment when real API is configured
    
    def get_gcp_details(self, gcp_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific GCP.
        
        Args:
            gcp_id: Unique identifier for the GCP
            
        Returns:
            Dictionary with GCP details or None
        """
        params = {
            "entityId": gcp_id,
            "datasetName": "GCP"
        }
        
        return None


class AlternativeGCPClient:
    """
    Alternative GCP client that can use other sources.
    
    This can be extended to use other GCP sources like:
    - OpenAerialMap
    - Local GCP databases
    - Custom GCP repositories
    """
    
    def __init__(self, source: str = "usgs"):
        self.source = source
    
    def find_gcps_by_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        max_results: int = 100
    ) -> List[Dict]:
        """
        Find GCPs from alternative sources.
        
        This is a placeholder for alternative implementations.
        """
        return []

