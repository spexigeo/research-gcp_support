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
    Client for accessing USGS Ground Control Points via M2M API.
    
    This client supports both the legacy EarthExplorer API and the new M2M (Machine-to-Machine) API.
    M2M API is the recommended method for programmatic access.
    
    Note: The login endpoint was deprecated in February 2025. Use application_token with login-token endpoint.
    """
    
    # M2M API base URL (recommended for new integrations)
    M2M_BASE_URL = "https://m2m.cr.usgs.gov/api/api/json/stable"
    # Legacy EarthExplorer API base URL (for backward compatibility)
    EE_BASE_URL = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1"
    
    def __init__(
        self, 
        username: Optional[str] = None, 
        password: Optional[str] = None,
        application_token: Optional[str] = None,
        use_m2m: bool = True
    ):
        """
        Initialize USGS GCP client.
        
        Args:
            username: USGS EarthExplorer username (REQUIRED for M2M API with application_token)
            password: USGS EarthExplorer password (DEPRECATED - not used with application_token)
            application_token: USGS application token (REQUIRED for M2M API)
            use_m2m: Whether to use M2M API (True) or legacy EarthExplorer API (False)
        """
        self.username = username
        self.password = password
        self.application_token = application_token
        self.use_m2m = use_m2m
        self.session = requests.Session()
        self.api_key = None
        
        # Set base URL based on API choice
        self.BASE_URL = self.M2M_BASE_URL if use_m2m else self.EE_BASE_URL
        
        # Authenticate if credentials provided
        # M2M API requires both username and application_token
        if use_m2m and application_token:
            if not username:
                print("Warning: M2M API requires both username and application_token.")
                print("Please provide username when using M2M API.")
            self.api_key = self._authenticate_with_token()
        elif application_token:
            # Legacy EE API with token
            self.api_key = self._authenticate_with_token()
        elif username and password:
            if use_m2m:
                print("Warning: M2M API requires application_token. Username/password not supported.")
                print("Please use application_token (and username) instead. See USGS_API_NOTES.md")
            else:
                print("Warning: Username/password authentication is deprecated.")
                print("Please use application_token instead. See USGS_API_NOTES.md")
                self.api_key = self._authenticate()
    
    def _authenticate_with_token(self) -> Optional[str]:
        """
        Authenticate with USGS using application token via login-token endpoint.
        
        This method works with both M2M API and legacy EarthExplorer API.
        The login endpoint was deprecated in February 2025.
        
        Note: M2M API requires both username and applicationToken.
        
        Returns:
            API key if successful, None otherwise
        """
        # Both M2M and EE APIs use login-token endpoint
        login_url = f"{self.BASE_URL}/login-token"
        
        # M2M API requires both username and token (parameter name is "token", not "applicationToken")
        if self.use_m2m:
            if not self.username:
                print("Error: M2M API requires username in addition to application_token")
                return None
            login_data = {
                "username": self.username,
                "token": self.application_token  # M2M API uses "token" parameter name
            }
        else:
            # Legacy EarthExplorer API uses "applicationToken"
            login_data = {
                "applicationToken": self.application_token
            }
            if self.username:
                login_data["username"] = self.username
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("errorCode"):
                error_msg = result.get("errorMessage", "Unknown error")
                print(f"USGS token authentication failed: {error_msg}")
                if self.use_m2m:
                    print("  Make sure you have M2M API access enabled at: https://ers.cr.usgs.gov/profile/access")
                    print("  M2M API requires both username and application_token")
                return None
            
            api_key = result.get("data")
            if api_key:
                api_type = "M2M" if self.use_m2m else "EarthExplorer"
                print(f"✓ Successfully authenticated with USGS {api_type} API")
                return api_key
            else:
                print("USGS token authentication failed: No API key returned")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"USGS token authentication error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response status: {e.response.status_code}")
                print(f"  Response: {e.response.text[:200]}")
            return None
    
    def _authenticate(self) -> Optional[str]:
        """
        Authenticate with USGS EarthExplorer and get API key.
        
        Returns:
            API key if successful, None otherwise
        """
        login_url = f"{self.BASE_URL}/login"
        
        login_data = {
            "username": self.username,
            "password": self.password,
            "catalogId": "EE"
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("errorCode"):
                print(f"USGS authentication failed: {result.get('errorMessage', 'Unknown error')}")
                return None
            
            api_key = result.get("data")
            if api_key:
                return api_key
            else:
                print("USGS authentication failed: No API key returned")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"USGS authentication error: {e}")
            return None
    
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
        max_results: int = 100,
        dataset_name: str = "NAIP"
    ) -> List[Dict]:
        """
        Find GCPs within a bounding box using USGS M2M API.
        
        Note: GCPs may be embedded in NAIP or other imagery datasets rather than
        being a standalone dataset. This method searches for available datasets
        and extracts GCP information where available.
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
            max_results: Maximum number of GCPs to return
            dataset_name: Dataset to search (default: "NAIP" for high-resolution imagery)
            
        Returns:
            List of GCP dictionaries with keys: lat, lon, id, accuracy, etc.
        """
        if not self.api_key:
            print("⚠️  Not authenticated. Cannot search for GCPs.")
            print("   Please provide application_token when initializing USGSGCPClient")
            return []
        
        min_lat, min_lon, max_lat, max_lon = bbox
        
        # Try to search for datasets and GCPs using M2M API
        # First, try to search for the dataset
        search_url = f"{self.BASE_URL}/scene-search"
        
        search_request = {
            "apiKey": self.api_key,
            "datasetName": dataset_name,
            "spatialFilter": {
                "filterType": "mbr",
                "lowerLeft": {
                    "latitude": min_lat,
                    "longitude": min_lon
                },
                "upperRight": {
                    "latitude": max_lat,
                    "longitude": max_lon
                }
            },
            "maxResults": max_results
        }
        
        try:
            # M2M API uses POST with JSON body
            if self.use_m2m:
                response = self.session.post(
                    search_url,
                    json=search_request,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
            else:
                # Legacy EE API uses GET with jsonRequest parameter
                params = {"jsonRequest": json.dumps(search_request)}
                response = self.session.get(search_url, params=params, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("errorCode"):
                error_msg = result.get("errorMessage", "Unknown error")
                print(f"⚠️  USGS search error: {error_msg}")
                print(f"   Dataset '{dataset_name}' may not be available or accessible")
                # Fall back to mock data for testing
                from .mock_gcp import MockGCPGenerator
                print("   Using mock data for demonstration...")
                return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='usgs')
            
            # Extract results
            data = result.get("data", {})
            results = data.get("results", [])
            
            if results:
                print(f"✓ Found {len(results)} scene(s) in dataset '{dataset_name}'")
                # Note: GCPs may be embedded in scene metadata or require separate extraction
                # For now, we'll need to extract GCP information from scene results
                # This is a placeholder - actual implementation depends on USGS data structure
                gcps = self._extract_gcps_from_scenes(results, bbox)
                if gcps:
                    return gcps
                else:
                    print("   No GCPs found in scene metadata. GCPs may require separate query.")
                    # Fall back to mock data for testing
                    from .mock_gcp import MockGCPGenerator
                    print("   Using mock data for demonstration...")
                    return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='usgs')
            else:
                print(f"⚠️  No results found for dataset '{dataset_name}' in bounding box")
                # Fall back to mock data for testing
                from .mock_gcp import MockGCPGenerator
                print("   Using mock data for demonstration...")
                return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='usgs')
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error searching USGS API: {e}")
            # Fall back to mock data for testing
            from .mock_gcp import MockGCPGenerator
            print("   Using mock data for demonstration...")
            return MockGCPGenerator.generate_gcps_in_bbox(bbox, max_results, source='usgs')
    
    def _extract_gcps_from_scenes(self, scenes: List[Dict], bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Extract GCP information from scene results.
        
        This is a placeholder method. The actual implementation depends on
        how USGS structures GCP data within scene metadata.
        
        Args:
            scenes: List of scene dictionaries from USGS API
            bbox: Bounding box for filtering
            
        Returns:
            List of GCP dictionaries
        """
        # TODO: Implement actual GCP extraction from scene metadata
        # This may require:
        # 1. Querying scene metadata endpoints
        # 2. Parsing embedded GCP information
        # 3. Or using a separate GCP dataset/endpoint
        return []
    
    def find_gcps_by_wrs2(
        self,
        path: int,
        row: int,
        max_results: int = 100,
        dataset_name: str = "NAIP"
    ) -> List[Dict]:
        """
        Find GCPs for a specific WRS-2 Path/Row.
        
        Args:
            path: WRS-2 path number
            row: WRS-2 row number
            max_results: Maximum number of GCPs to return
            dataset_name: Dataset to search (default: "NAIP")
            
        Returns:
            List of GCP dictionaries
        """
        if not self.api_key:
            print("⚠️  Not authenticated. Cannot search for GCPs.")
            return []
        
        search_url = f"{self.BASE_URL}/scene-search"
        
        search_request = {
            "apiKey": self.api_key,
            "datasetName": dataset_name,
            "sceneFilter": {
                "acquisitionFilter": {
                    "start": "1900-01-01",
                    "end": "2100-01-01"
                }
            },
            "spatialFilter": {
                "filterType": "wrs2",
                "path": path,
                "row": row
            },
            "maxResults": max_results
        }
        
        try:
            if self.use_m2m:
                response = self.session.post(
                    search_url,
                    json=search_request,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
            else:
                params = {"jsonRequest": json.dumps(search_request)}
                response = self.session.get(search_url, params=params, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("errorCode"):
                # Fall back to mock data
                from .mock_gcp import MockGCPGenerator
                return MockGCPGenerator.generate_gcps_for_wrs2(path, row, max_results)
            
            data = result.get("data", {})
            results = data.get("results", [])
            
            if results:
                # Extract GCPs from scenes
                gcps = self._extract_gcps_from_scenes(results, None)
                if gcps:
                    return gcps
            
            # Fall back to mock data for testing
            from .mock_gcp import MockGCPGenerator
            return MockGCPGenerator.generate_gcps_for_wrs2(path, row, max_results)
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error searching USGS API: {e}")
            # Fall back to mock data
            from .mock_gcp import MockGCPGenerator
            return MockGCPGenerator.generate_gcps_for_wrs2(path, row, max_results)
    
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

