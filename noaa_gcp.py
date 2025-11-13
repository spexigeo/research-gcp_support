"""
NOAA Ground Control Point client for downloading GCPs.
"""

import requests
import json
from typing import List, Dict, Tuple, Optional
import time
from urllib.parse import urlencode
import os
from pathlib import Path

# Try to import KMZ parser
try:
    from .noaa_kmz_parser import load_noaa_gcps_from_kmz
    KMZ_PARSER_AVAILABLE = True
except ImportError:
    try:
        from noaa_kmz_parser import load_noaa_gcps_from_kmz
        KMZ_PARSER_AVAILABLE = True
    except ImportError:
        KMZ_PARSER_AVAILABLE = False
        load_noaa_gcps_from_kmz = None


class NOAAGCPClient:
    """
    Client for accessing NOAA Ground Control Points.
    
    NOAA (National Oceanic and Atmospheric Administration) maintains GCP databases
    that can be used as a supplement or alternative to USGS GCPs.
    
    Supports loading GCPs from NGS Imagery Ground Control Point Archive KMZ files.
    """
    
    BASE_URL = "https://www.ngs.noaa.gov/cgi-bin/datasheet.prl"  # Example endpoint
    # Alternative: NOAA's National Geodetic Survey (NGS) database
    
    def __init__(self, api_key: Optional[str] = None, kmz_path: Optional[str] = None):
        """
        Initialize NOAA GCP client.
        
        Args:
            api_key: NOAA API key (optional, may be required for some endpoints)
            kmz_path: Path to NGS Photo Control Archive KMZ file (optional)
                     If None, looks for NGS_NOAA_PhotoControlArchive.kmz in input directory
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        
        # Load GCPs from KMZ file if available
        self._gcps_cache = None
        self._kmz_path = kmz_path
        self._load_gcps_from_kmz()
    
    def _load_gcps_from_kmz(self):
        """Load GCPs from KMZ file if available."""
        if not KMZ_PARSER_AVAILABLE:
            return
        
        try:
            gcps = load_noaa_gcps_from_kmz(self._kmz_path)
            if gcps:
                self._gcps_cache = gcps
                print(f"Loaded {len(gcps)} GCPs from NOAA KMZ archive")
        except Exception as e:
            print(f"Warning: Could not load GCPs from KMZ file: {e}")
            self._gcps_cache = None
    
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
        
        # First, try to use GCPs loaded from KMZ file
        if self._gcps_cache is not None:
            filtered_gcps = []
            for gcp in self._gcps_cache:
                lat = gcp.get('lat')
                lon = gcp.get('lon')
                
                if lat is None or lon is None:
                    continue
                
                # Check if GCP is within bounding box
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    filtered_gcps.append(gcp)
                    if len(filtered_gcps) >= max_results:
                        break
            
            if filtered_gcps:
                print(f"Found {len(filtered_gcps)} GCPs from NOAA KMZ archive in bounding box")
                return filtered_gcps
        
        # If no KMZ data available, try API (if configured)
        # Note: This is a placeholder for future API implementation
        params = {
            "north": max_lat,
            "south": min_lat,
            "east": max_lon,
            "west": min_lon,
            "format": "json",
            "limit": max_results
        }
        
        # For now, if no KMZ data, use mock data for testing
        if self._gcps_cache is None:
            print("Note: No NOAA KMZ file found. Using mock data for testing.")
            print("Place NGS_NOAA_PhotoControlArchive.kmz in the input/ directory to use real NOAA data.")
            from .mock_gcp import MockGCPGenerator
            return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='noaa')
        
        # If KMZ loaded but no GCPs in bbox, return empty list
        return []
    
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

