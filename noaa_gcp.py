"""
NOAA Ground Control Point client for downloading GCPs.
"""

import requests
import json
from typing import List, Dict, Tuple, Optional
import time
from urllib.parse import urlencode


class NOAAGCPClient:
    """
    Client for accessing NOAA Ground Control Points.
    
    NOAA (National Oceanic and Atmospheric Administration) maintains GCP databases
    that can be used as a supplement or alternative to USGS GCPs.
    """
    
    BASE_URL = "https://www.ngs.noaa.gov/cgi-bin/datasheet.prl"  # Example endpoint
    # Alternative: NOAA's National Geodetic Survey (NGS) database
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NOAA GCP client.
        
        Args:
            api_key: NOAA API key (optional, may be required for some endpoints)
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make a request to the NOAA API."""
        url = f"{self.BASE_URL}/{endpoint}" if endpoint else self.BASE_URL
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to NOAA API {url}: {e}")
            return {}
    
    def find_gcps_by_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        max_results: int = 100
    ) -> List[Dict]:
        """
        Find GCPs within a bounding box from NOAA databases.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            max_results: Maximum number of GCPs to return
            
        Returns:
            List of GCP dictionaries with keys: lat, lon, id, accuracy, etc.
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        
        # Note: This is a placeholder implementation. The actual NOAA API
        # may require different endpoints and parameters. NOAA's NGS (National
        # Geodetic Survey) maintains control point databases that can be accessed
        # through various methods:
        # 1. NGS datasheet database
        # 2. NOAA's API endpoints
        # 3. Direct database queries
        
        gcps = []
        
        # Example: If NOAA provides a spatial search endpoint
        params = {
            "north": max_lat,
            "south": min_lat,
            "east": max_lon,
            "west": min_lon,
            "format": "json",
            "limit": max_results
        }
        
        # This would need to be adapted to the actual NOAA API
        # For demonstration, we'll return an empty list with a note
        print("Note: NOAA GCP API integration requires specific endpoint configuration.")
        print("Please configure the actual NOAA API endpoint in noaa_gcp.py")
        print("For testing, you can use MockGCPGenerator from mock_gcp.py")
        
        # For testing: use mock data if no real API configured
        # Uncomment the following to use mock data for testing:
        from .mock_gcp import MockGCPGenerator
        return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='noaa')
        
        # return gcps  # Uncomment when real API is configured
    
    def find_gcps_by_state(
        self,
        state: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Find GCPs by US state (for NOAA/NGS databases).
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            max_results: Maximum number of GCPs to return
            
        Returns:
            List of GCP dictionaries
        """
        params = {
            "state": state.upper(),
            "format": "json",
            "limit": max_results
        }
        
        return []
    
    def get_gcp_details(self, gcp_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific GCP from NOAA.
        
        Args:
            gcp_id: Unique identifier for the GCP
            
        Returns:
            Dictionary with GCP details or None
        """
        params = {
            "id": gcp_id,
            "format": "json"
        }
        
        return None

