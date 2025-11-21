# USGS API Integration Notes

## Overview

The `usgs_gcp.py` module provides a framework for accessing USGS Ground Control Points, but requires configuration with the actual USGS API endpoints.

## USGS Data Sources

### Option 1: USGS EarthExplorer API

The USGS EarthExplorer provides an API for accessing various datasets including GCPs. To use this:

1. **Register for an account**: Create a free account at https://earthexplorer.usgs.gov/
2. **Request M2M API Access**: 
   - Log into your account
   - Visit: https://ers.cr.usgs.gov/profile/access
   - Request Machine-to-Machine (M2M) API access
   - Wait for approval (may take some time)
3. **Create Application Token**:
   - After M2M access is approved, go to your profile's "Applications" section
   - Generate a new application token
   - Save this token securely
4. **Use Token for Authentication**: Use the token with the `/login-token` endpoint

**API Documentation**: 
- https://earthexplorer.usgs.gov/inventory/documentation/json-docs
- M2M Application Token Documentation: https://www.usgs.gov/media/files/m2m-application-token-documentation
- The base URL is: `https://earthexplorer.usgs.gov/inventory/json/v/1.4.1`

**Important**: Username/password authentication is **DEPRECATED**. You must use application tokens.

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

Once the API is configured, test with:

```python
from research_gcp_support import USGSGCPClient

# NEW METHOD (recommended): Use application token
client = USGSGCPClient(application_token="your_application_token")
bbox = (40.0, -75.0, 41.0, -74.0)  # Example bounding box
gcps = client.find_gcps_by_bbox(bbox)
print(f"Found {len(gcps)} GCPs")

# DEPRECATED METHOD: Username/password (may not work)
# client = USGSGCPClient(username="your_username", password="your_password")
```

Or use the test script:

```bash
# Set your application token as an environment variable
export USGS_APPLICATION_TOKEN="your_token_here"
python test_usgs_access.py
```

## Notes

- The current implementation is a framework that needs API-specific details filled in
- Rate limiting may apply to USGS APIs
- Some GCP data may require special licensing or agreements
- Consider caching results to avoid repeated API calls

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



