# USGS API Integration Notes

## Overview

The `usgs_gcp.py` module provides access to USGS Ground Control Points via the M2M (Machine-to-Machine) API. The M2M API is the recommended method for programmatic access to USGS data.

## USGS M2M API Setup

### Step 1: Request M2M API Access

1. **Register for an account**: Create a free account at https://earthexplorer.usgs.gov/
2. **Request M2M API Access**: 
   - Log into your account
   - Visit: https://ers.cr.usgs.gov/profile/access
   - Request Machine-to-Machine (M2M) API access
   - Wait for approval (may take some time)
3. **Create Application Token**:
   - After M2M access is approved, go to your profile's "Applications" section
   - Generate a new application token
   - Save this token securely (you'll need it for authentication)

### Step 2: Use the M2M API

**M2M API Base URL**: `https://m2m.cr.usgs.gov/api/api/json/stable`

**Authentication Endpoint**: `/login-token` (POST request with `username` and `applicationToken`)

**Important Notes**:
- The `/login` endpoint was **deprecated in February 2025**
- You **must** use the `/login-token` endpoint with both `username` and `applicationToken`
- M2M API **requires both** your USGS username and application token for authentication
- Username/password authentication is **DEPRECATED** and may not work

**API Documentation**: 
- M2M API Test Page: https://m2m.cr.usgs.gov/
- M2M API Documentation: Available at https://m2m.cr.usgs.gov/ (after login)
- Application Token Documentation: https://www.usgs.gov/media/files/m2m-application-token-documentation

### Legacy EarthExplorer API (Not Recommended)

The legacy EarthExplorer API is still available but not recommended for new integrations:
- Base URL: `https://earthexplorer.usgs.gov/inventory/json/v/1.4.1`
- Documentation: https://earthexplorer.usgs.gov/inventory/documentation/json-docs

### Option 2: USGS GCP Database Direct Access

USGS may provide direct database access or bulk downloads. Check:
- https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-aerial-photo-single-frames
- Contact USGS for bulk data access options

### Option 3: Alternative Sources

If USGS API access is limited, consider these alternatives:

1. **OpenAerialMap**: Community-driven aerial imagery with GCPs
   - API: https://api.openaerialmap.org/
   
2. **NOAA GCPs**: National Oceanic and Atmospheric Administration may have GCP data
   
3. **State/Local Sources**: Many states and local governments maintain GCP databases

4. **Commercial Sources**: Services like Maxar, Planet, etc. may provide GCP data

## Implementation Steps

To complete the USGS integration:

1. **Identify the correct API endpoint** for GCP data
2. **Implement authentication** if required
3. **Parse the API response** to extract GCP information
4. **Map API fields** to the expected GCP dictionary format:
   ```python
   {
       'id': str,           # Unique identifier
       'lat': float,        # Latitude
       'lon': float,        # Longitude
       'z': float,          # Elevation/altitude
       'accuracy': float,   # RMSE in meters
       'type': str,         # GCP type (e.g., 'road intersection')
       'description': str,  # Description
       'photo_identifiable': bool  # Whether clearly visible in imagery
   }
   ```

## Example API Call Structure

```python
# Example structure for EarthExplorer API
params = {
    "jsonRequest": json.dumps({
        "apiKey": "your_api_key",
        "datasetName": "GCP",
        "spatialFilter": {
            "filterType": "mbr",
            "lowerLeft": {"latitude": min_lat, "longitude": min_lon},
            "upperRight": {"latitude": max_lat, "longitude": max_lon}
        },
        "maxResults": max_results
    })
}
```

## Testing

Once you have M2M API access and an application token, test with:

```python
from research_gcp_support.usgs_gcp import USGSGCPClient

# M2M API (recommended): Requires both username and application token
client = USGSGCPClient(
    username="your_username",  # Required for M2M API
    application_token="your_application_token",  # Required for M2M API
    use_m2m=True  # Use M2M API (default)
)
bbox = (40.0, -75.0, 41.0, -74.0)  # Example bounding box
gcps = client.find_gcps_by_bbox(bbox, dataset_name="NAIP")
print(f"Found {len(gcps)} GCPs")

# Legacy EarthExplorer API (not recommended)
# client = USGSGCPClient(
#     application_token="your_application_token",
#     use_m2m=False  # Use legacy API
# )
```

Or use the test script:

```bash
# Set your username and application token as environment variables
export USGS_USERNAME="your_username"
export USGS_APPLICATION_TOKEN="your_token_here"
python test_usgs_access.py
```

The test script will:
1. Test M2M API authentication (recommended)
2. Fall back to legacy EarthExplorer API if M2M fails
3. Test dataset search (e.g., NAIP)
4. Test spatial search for scenes/GCPs

## GCP Data Availability

**Important**: Ground Control Points may not be available as a standalone dataset through the USGS API. Instead:

1. **GCPs may be embedded in imagery datasets**: GCPs are often part of NAIP or other high-resolution imagery datasets
2. **Scene metadata**: GCP information may be available in scene metadata rather than as a separate dataset
3. **Separate extraction required**: You may need to extract GCP information from scene search results

The current implementation searches for scenes (e.g., NAIP) and attempts to extract GCP information. If GCPs are not found in scene metadata, the code falls back to mock data for testing purposes.

## Notes

- M2M API is the recommended method for all new integrations
- Rate limiting may apply to USGS APIs
- Some datasets may require special licensing or agreements
- Consider caching results to avoid repeated API calls
- GCP extraction from scene metadata may require additional implementation based on USGS data structure

## Troubleshooting 403 Forbidden Errors

If you encounter 403 Forbidden errors when trying to authenticate:

1. **API Access May Require Separate Registration**: 
   - Even if you can log into the web interface, API access may need to be enabled separately
   - Contact USGS support to request API access: https://earthexplorer.usgs.gov/contact
   - Some accounts may need special permissions for API access

2. **Verify Account Status**:
   - Log into https://earthexplorer.usgs.gov/ manually to confirm your account works
   - Check if there are any account restrictions or pending activations

3. **Alternative Authentication**:
   - The API might require OAuth or token-based authentication
   - Check the latest API documentation for current authentication methods

4. **GCP Availability**:
   - **Important**: Ground Control Points may NOT be available through the standard EarthExplorer API
   - GCPs might be part of specific datasets (like aerial photography metadata) rather than a standalone dataset
   - GCPs might only be available through bulk downloads or special data requests
   - Check if GCPs appear in the EarthExplorer web interface dataset list

## Alternative Approaches

If USGS API access is not available or GCPs are not accessible through the API:

1. **Use NOAA GCP Databases** (already implemented as fallback)
2. **Contact USGS Directly**: Request GCP data for specific areas
3. **Use State/Local Sources**: Many states maintain their own GCP databases
4. **Commercial Sources**: Services like Maxar, Planet may provide GCP data
5. **Community Sources**: OpenAerialMap and similar community-driven sources



