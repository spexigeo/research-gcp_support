# USGS API Integration Notes

## Overview

The `usgs_gcp.py` module provides a framework for accessing USGS Ground Control Points, but requires configuration with the actual USGS API endpoints.

## USGS Data Sources

### Option 1: USGS EarthExplorer API

The USGS EarthExplorer provides an API for accessing various datasets including GCPs. To use this:

1. **Register for an account**: Create a free account at https://earthexplorer.usgs.gov/
2. **Get API credentials**: The EarthExplorer API may require authentication
3. **Configure the endpoint**: Update `USGSGCPClient` in `usgs_gcp.py` with the correct API endpoint

**API Documentation**: 
- https://earthexplorer.usgs.gov/inventory/documentation/json-docs
- The base URL is typically: `https://earthexplorer.usgs.gov/inventory/json/v/1.4.1`

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
from gcp_support import USGSGCPClient

client = USGSGCPClient(username="your_username", password="your_password")
bbox = (40.0, -75.0, 41.0, -74.0)  # Example bounding box
gcps = client.find_gcps_by_bbox(bbox)
print(f"Found {len(gcps)} GCPs")
```

## Notes

- The current implementation is a framework that needs API-specific details filled in
- Rate limiting may apply to USGS APIs
- Some GCP data may require special licensing or agreements
- Consider caching results to avoid repeated API calls



