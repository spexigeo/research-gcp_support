"""
Test script to verify USGS EarthExplorer API access and GCP availability.

This script tests:
1. Authentication with USGS EarthExplorer
2. Access to GCP datasets
3. Ability to search for GCPs in a bounding box

Note: USGS has transitioned to application token authentication.
- Username/password authentication is DEPRECATED
- You need to:
  1. Request M2M API access: https://ers.cr.usgs.gov/profile/access
  2. Create an application token in your profile's "Applications" section
  3. Use the token with the /login-token endpoint
- See: https://www.usgs.gov/media/files/m2m-application-token-documentation
"""

import os
import sys
from typing import Dict, Optional

try:
    from .usgs_gcp import USGSGCPClient
    from .h3_utils import h3_cells_to_bbox
    from .manifest_parser import get_h3_cells_from_manifest
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from research_gcp_support.usgs_gcp import USGSGCPClient
    from research_gcp_support.h3_utils import h3_cells_to_bbox
    from research_gcp_support.manifest_parser import get_h3_cells_from_manifest

import requests
import json


def test_usgs_authentication(username: str, password: str) -> Optional[str]:
    """
    Test USGS EarthExplorer authentication and get API key.
    
    Args:
        username: USGS EarthExplorer username
        password: USGS EarthExplorer password
        
    Returns:
        API key if successful, None otherwise
    """
    print("=" * 70)
    print("Testing USGS EarthExplorer Authentication")
    print("=" * 70)
    
    session = requests.Session()
    
    # Method 1: Try JSON API endpoint with form data
    login_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/login"
    
    # Try as form data first (some APIs expect this)
    login_data_form = {
        "username": username,
        "password": password,
        "catalogId": "EE"
    }
    
    try:
        print(f"Attempting to authenticate with username: {username}")
        print("Trying method 1: POST with form data...")
        
        # Try as form-encoded data
        response = session.post(login_url, data=login_data_form, timeout=30)
        print(f"  Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("errorCode"):
                    print(f"  ❌ API error: {result.get('errorMessage', 'Unknown error')}")
                else:
                    api_key = result.get("data")
                    if api_key:
                        print(f"  ✓ Authentication successful!")
                        print(f"  API Key: {api_key[:20]}... (truncated)")
                        return api_key
            except json.JSONDecodeError:
                print(f"  ⚠️  Response is not JSON: {response.text[:200]}")
        
        # Try as JSON
        print("Trying method 2: POST with JSON...")
        response = session.post(login_url, json=login_data_form, timeout=30)
        print(f"  Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("errorCode"):
                    print(f"  ❌ API error: {result.get('errorMessage', 'Unknown error')}")
                else:
                    api_key = result.get("data")
                    if api_key:
                        print(f"  ✓ Authentication successful!")
                        print(f"  API Key: {api_key[:20]}... (truncated)")
                        return api_key
            except json.JSONDecodeError:
                print(f"  ⚠️  Response is not JSON: {response.text[:200]}")
        
        # Method 3: Try web login first, then get API key
        print("Trying method 3: Web login then API key...")
        web_login_url = "https://earthexplorer.usgs.gov/login"
        
        # First, get the login page to establish session
        login_page = session.get(web_login_url, timeout=30)
        print(f"  Login page status: {login_page.status_code}")
        
        # Try to login via web form
        web_login_data = {
            "username": username,
            "password": password
        }
        
        web_response = session.post(web_login_url, data=web_login_data, timeout=30, allow_redirects=True)
        print(f"  Web login status: {web_response.status_code}")
        print(f"  Final URL: {web_response.url}")
        
        # Now try API login with session cookies
        if "earthexplorer.usgs.gov" in web_response.url and web_response.status_code in [200, 302]:
            print("  Web login appears successful, trying API with session...")
            api_response = session.post(login_url, data=login_data_form, timeout=30)
            print(f"  API status: {api_response.status_code}")
            
            if api_response.status_code == 200:
                try:
                    result = api_response.json()
                    api_key = result.get("data")
                    if api_key:
                        print(f"  ✓ Authentication successful via web session!")
                        print(f"  API Key: {api_key[:20]}... (truncated)")
                        return api_key
                except json.JSONDecodeError:
                    pass
        
        # If all methods fail, show error details
        print(f"\n❌ All authentication methods failed")
        print(f"  Last response status: {response.status_code}")
        print(f"  Last response headers: {dict(response.headers)}")
        if response.status_code == 403:
            print(f"\n  403 Forbidden error suggests:")
            print(f"  - Account may need activation or special permissions")
            print(f"  - API access might require separate registration")
            print(f"  - Check if your account has API access enabled")
            print(f"  - Try logging into https://earthexplorer.usgs.gov/ manually first")
        
        return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during authentication: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response status: {e.response.status_code}")
            print(f"  Response text: {e.response.text[:200]}")
        return None


def test_dataset_search(api_key: str, dataset_name: str = "GCP") -> bool:
    """
    Test if we can search for datasets, specifically GCP datasets.
    
    Args:
        api_key: USGS API key from authentication
        dataset_name: Name of dataset to search for
        
    Returns:
        True if dataset is found, False otherwise
    """
    print("\n" + "=" * 70)
    print(f"Testing Dataset Search for '{dataset_name}'")
    print("=" * 70)
    
    # EarthExplorer API datasets endpoint
    datasets_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/datasets"
    
    params = {
        "apiKey": api_key,
        "datasetName": dataset_name
    }
    
    try:
        print(f"Searching for dataset: {dataset_name}")
        response = requests.get(datasets_url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("errorCode"):
            print(f"❌ Dataset search failed: {result.get('errorMessage', 'Unknown error')}")
            return False
        
        data = result.get("data", [])
        if data:
            print(f"✓ Found {len(data)} dataset(s) matching '{dataset_name}':")
            for dataset in data:
                print(f"  - {dataset.get('datasetName', 'Unknown')}: {dataset.get('datasetFullName', 'No description')}")
            return True
        else:
            print(f"⚠️  No datasets found matching '{dataset_name}'")
            print("  This might mean:")
            print("  1. GCPs are not available as a separate dataset")
            print("  2. GCPs might be part of another dataset")
            print("  3. Different dataset name is required")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during dataset search: {e}")
        return False


def test_gcp_search(api_key: str, bbox: tuple) -> bool:
    """
    Test searching for GCPs in a bounding box.
    
    Args:
        api_key: USGS API key
        bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
        
    Returns:
        True if search succeeds (even if no results), False on error
    """
    print("\n" + "=" * 70)
    print("Testing GCP Search in Bounding Box")
    print("=" * 70)
    
    min_lat, min_lon, max_lat, max_lon = bbox
    print(f"Bounding box: ({min_lat:.6f}, {min_lon:.6f}, {max_lat:.6f}, {max_lon:.6f})")
    
    # Try different possible dataset names for GCPs
    possible_datasets = ["GCP", "GROUND_CONTROL_POINTS", "GROUND_CONTROL", "GCP_POINTS"]
    
    for dataset_name in possible_datasets:
        print(f"\nTrying dataset name: {dataset_name}")
        
        search_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/search"
        
        search_request = {
            "apiKey": api_key,
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
            "maxResults": 10
        }
        
        params = {
            "jsonRequest": json.dumps(search_request)
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("errorCode"):
                error_msg = result.get("errorMessage", "Unknown error")
                print(f"  ❌ Search failed: {error_msg}")
                # Continue to next dataset name
                continue
            
            data = result.get("data", {})
            results = data.get("results", [])
            
            if results:
                print(f"  ✓ Found {len(results)} result(s) for dataset '{dataset_name}'")
                print(f"  Total available: {data.get('totalHits', 'Unknown')}")
                return True
            else:
                print(f"  ⚠️  No results found for dataset '{dataset_name}'")
                # Continue to next dataset name
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error during search: {e}")
            continue
    
    print("\n⚠️  No GCP results found with any dataset name")
    print("  This might mean:")
    print("  1. GCPs are not available through the standard EarthExplorer API")
    print("  2. GCPs require special access or different endpoint")
    print("  3. GCPs might be available through a different USGS service")
    return False


def test_list_all_datasets(api_key: str) -> None:
    """
    List all available datasets to help identify GCP-related datasets.
    
    Args:
        api_key: USGS API key
    """
    print("\n" + "=" * 70)
    print("Listing All Available Datasets")
    print("=" * 70)
    
    datasets_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/datasets"
    
    params = {
        "apiKey": api_key
    }
    
    try:
        response = requests.get(datasets_url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("errorCode"):
            print(f"❌ Failed to list datasets: {result.get('errorMessage', 'Unknown error')}")
            return
        
        datasets = result.get("data", [])
        print(f"✓ Found {len(datasets)} total datasets")
        
        # Look for GCP-related datasets
        gcp_related = [d for d in datasets if "GCP" in d.get("datasetName", "").upper() or 
                      "GROUND" in d.get("datasetName", "").upper() or
                      "CONTROL" in d.get("datasetName", "").upper()]
        
        if gcp_related:
            print(f"\nFound {len(gcp_related)} potentially GCP-related dataset(s):")
            for dataset in gcp_related:
                print(f"  - {dataset.get('datasetName')}: {dataset.get('datasetFullName', 'No description')}")
        else:
            print("\n⚠️  No obvious GCP-related datasets found")
            print("  Searching for datasets with 'GCP', 'GROUND', or 'CONTROL' in name...")
            print("  You may need to check USGS documentation for GCP dataset names")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing datasets: {e}")


def test_token_authentication(application_token: str) -> Optional[str]:
    """
    Test USGS EarthExplorer authentication using application token (new method).
    
    Args:
        application_token: USGS application token
        
    Returns:
        API key if successful, None otherwise
    """
    print("=" * 70)
    print("Testing USGS EarthExplorer Token Authentication (New Method)")
    print("=" * 70)
    
    login_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/login-token"
    
    login_data = {
        "applicationToken": application_token
    }
    
    try:
        print("Attempting to authenticate with application token...")
        response = requests.post(login_url, json=login_data, timeout=30)
        print(f"  Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("errorCode"):
                    print(f"  ❌ API error: {result.get('errorMessage', 'Unknown error')}")
                    return None
                
                api_key = result.get("data")
                if api_key:
                    print(f"  ✓ Token authentication successful!")
                    print(f"  API Key: {api_key[:20]}... (truncated)")
                    return api_key
                else:
                    print(f"  ❌ No API key returned")
                    print(f"  Response: {result}")
                    return None
            except json.JSONDecodeError:
                print(f"  ⚠️  Response is not JSON: {response.text[:200]}")
                return None
        else:
            print(f"  ❌ Authentication failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during token authentication: {e}")
        return None


def main():
    """Main test function."""
    print("=" * 70)
    print("USGS EarthExplorer GCP Access Test")
    print("=" * 70)
    print()
    print("NOTE: USGS now requires application tokens for API access.")
    print("Username/password authentication is deprecated.")
    print()
    print("To get an application token:")
    print("1. Log into https://earthexplorer.usgs.gov/")
    print("2. Request M2M API access: https://ers.cr.usgs.gov/profile/access")
    print("3. Create an application token in your profile's 'Applications' section")
    print()
    
    # Try token authentication first (new method)
    application_token = os.getenv("USGS_APPLICATION_TOKEN")
    if not application_token:
        print("Do you have a USGS application token? (y/n): ", end="")
        has_token = input().strip().lower()
        if has_token == 'y':
            import getpass
            application_token = getpass.getpass("Enter your application token: ").strip()
    
    api_key = None
    if application_token:
        api_key = test_token_authentication(application_token)
    
    # Fallback to username/password (deprecated but might work for some accounts)
    if not api_key:
        print("\n" + "=" * 70)
        print("Trying deprecated username/password method (may not work)...")
        print("=" * 70)
        
        username = os.getenv("USGS_USERNAME")
        password = os.getenv("USGS_PASSWORD")
        
        if not username:
            username = input("Enter USGS EarthExplorer username (or press Enter to skip): ").strip()
        
        if username:
            if not password:
                import getpass
                password = getpass.getpass("Enter USGS EarthExplorer password: ").strip()
            
            if username and password:
                api_key = test_usgs_authentication(username, password)
    
    if not api_key:
        print("\n" + "=" * 70)
        print("❌ Could not authenticate with any method")
        print("=" * 70)
        print("\nTo get API access:")
        print("1. Request M2M API access: https://ers.cr.usgs.gov/profile/access")
        print("2. Create an application token in your profile")
        print("3. Use the token with this script: export USGS_APPLICATION_TOKEN='your_token'")
        print("\nDocumentation: https://www.usgs.gov/media/files/m2m-application-token-documentation")
        return
    
    # api_key should already be set from main() function
    if not api_key:
        return
    
    # Test 2: List all datasets to find GCP-related ones
    test_list_all_datasets(api_key)
    
    # Test 3: Search for GCP dataset specifically
    test_dataset_search(api_key, "GCP")
    
    # Test 4: Try to search for GCPs in a bounding box
    # Use H3 cells from manifest if available, otherwise use a test bbox
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), 'input', 'input-file.manifest')
        if os.path.exists(manifest_path):
            h3_cells = get_h3_cells_from_manifest(manifest_path)
            bbox = h3_cells_to_bbox(h3_cells)
            print(f"\nUsing bounding box from manifest H3 cells: {h3_cells}")
        else:
            # Use a test bounding box (New York area)
            bbox = (40.0, -75.0, 41.0, -74.0)
            print(f"\nUsing test bounding box (New York area)")
    except Exception as e:
        print(f"\n⚠️  Could not get bounding box from manifest: {e}")
        bbox = (40.0, -75.0, 41.0, -74.0)
        print(f"Using test bounding box (New York area)")
    
    test_gcp_search(api_key, bbox)
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("✓ Authentication: Successful")
    print("⚠️  GCP Access: Check results above")
    print("\nNext steps:")
    print("1. If GCP datasets were found, update usgs_gcp.py with the correct dataset name")
    print("2. If no GCP datasets found, check USGS documentation or contact USGS support")
    print("3. GCPs might be available through a different USGS service or portal")


if __name__ == "__main__":
    main()

