# NOAA and Other GCP Sources Setup Guide

## Current Status

Currently, both USGS and NOAA clients are using **mock data** for testing. To use real data sources, you'll need to configure the appropriate APIs or data access methods.

## NOAA (National Geodetic Survey) Setup

### Overview

NOAA's National Geodetic Survey (NGS) maintains extensive geodetic control point databases. These are primarily survey markers and benchmarks rather than photo-identifiable GCPs, but they can be useful for georeferencing.

### Data Sources

1. **NGS Imagery Ground Control Point Archive** ⭐ **PROMISING**
   - URL: https://www.ngs.noaa.gov/AERO/PhotoControl/ImageControlArchive.htm
   - Contains: Ground control point coordinates, sketches, metadata, and ground-view photographs
   - Format: Google Earth KMZ files organized by state and project identifier
   - Access: Free download, organized by state
   - **This is specifically for aerial photogrammetry** - perfect for your use case!
   - **Note**: These are photo-identifiable GCPs used in aerial surveys

2. **NGS Datasheet Database**
   - URL: https://www.ngs.noaa.gov/cgi-bin/datasheet.prl
   - Contains: Survey markers, benchmarks, control points
   - Access: Web interface or direct database queries
   - **Note**: These are typically survey markers, not photo-identifiable GCPs

3. **NGS Data Explorer**
   - URL: https://www.ngs.noaa.gov/NGSDataExplorer/
   - Interactive map interface for finding control points
   - Can export data in various formats

4. **NGS API (if available)**
   - May require registration or special access
   - Check: https://www.ngs.noaa.gov/web_services/

### Configuration Options

#### Option 1: Direct Database Access (Recommended if available)

If NOAA provides API access:

```python
# Update noaa_gcp.py with actual API endpoint
BASE_URL = "https://api.ngs.noaa.gov/..."  # Actual endpoint
```

#### Option 2: Web Scraping (Not Recommended)

You could scrape the datasheet database, but this is:
- Against terms of service
- Unreliable
- Not scalable

#### Option 3: Bulk Downloads

NOAA may provide bulk data downloads:
- Check: https://www.ngs.noaa.gov/data/
- Download control point databases for your area
- Import into local database
- Query locally

### Current Implementation

The `NOAAGCPClient` in `noaa_gcp.py` currently:
- Uses mock data for testing
- Has placeholder endpoints
- Needs actual API configuration

### To Configure NOAA:

#### Option A: Use NGS Imagery Ground Control Point Archive (Recommended)

The NGS Imagery Ground Control Point Archive is the best option because:
- ✅ Specifically designed for aerial photogrammetry
- ✅ Includes photo-identifiable GCPs
- ✅ Free and publicly available
- ✅ Organized by state

**Implementation Steps**:

1. **Download KMZ files** for your target states from:
   https://www.ngs.noaa.gov/AERO/PhotoControl/ImageControlArchive.htm

2. **Parse KMZ files** (they're just ZIP files with KML inside):
   ```python
   import zipfile
   from xml.etree import ElementTree as ET
   
   # Extract KMZ and parse KML
   # Extract coordinates and metadata
   ```

3. **Update `noaa_gcp.py`** to:
   - Load KMZ files for relevant states
   - Parse KML to extract GCP coordinates
   - Filter by bounding box
   - Map to GCP dictionary format

4. **Alternative**: Convert KMZ to local database (PostGIS, SQLite) for faster queries

#### Option B: Use NGS API (if available)

1. **Check if API exists**: Visit https://www.ngs.noaa.gov/web_services/
2. **Request API access**: Contact NOAA/NGS if API access is needed
3. **Update `noaa_gcp.py`**: 
   - Set correct `BASE_URL`
   - Implement actual API calls
   - Parse response format
   - Map to GCP dictionary format

### Important Note

**NGS Imagery Ground Control Point Archive** contains photo-identifiable GCPs specifically for aerial photogrammetry - this is perfect for your use case!

The regular NGS datasheet database contains survey markers which may not be photo-identifiable.

## Other Potential Sources

### 1. CompassData GCP Archive ⭐ **COMMERCIAL BUT COMPREHENSIVE**

- **Website**: https://compassdatainc.com/ground-control-point-sample/
- **Description**: Global archive of over 80,000 survey-grade GCPs
- **Access**: 
  - Free sample dataset available
  - Full archive requires commercial license
- **Includes**: Certified GCPs, coordinate metadata, sample imagery footprints, accuracy documentation
- **Good for**: High-quality, verified GCPs with documentation

### 2. USGS Ground Control Points (Direct Download)

- **Website**: https://www.usgs.gov/landsat-missions/ground-control-points
- **Description**: GCPs used to geo-reference Landsat Level-1 data
- **Access**: Periodic updates, downloadable datasets
- **Note**: These are the same GCPs that would be available through the API
- **Good for**: If you can't get API access, you might be able to download bulk data

### 3. State and Local Government Sources

Many states maintain their own GCP databases:

- **State DOTs (Departments of Transportation)**: Often have survey control points
- **State GIS Offices**: May maintain geodetic control databases
- **County/Local Surveyors**: Local control point databases

**How to use**:
- Contact state/local GIS offices
- Request access to control point databases
- May require data sharing agreements
- Often available as shapefiles or databases

### 2. Commercial Sources

#### Maxar (formerly DigitalGlobe)
- **Website**: https://www.maxar.com/
- **GCP Service**: May provide GCP data as part of imagery services
- **Access**: Commercial license required
- **Contact**: Sales team for API access

#### Planet Labs
- **Website**: https://www.planet.com/
- **GCP Service**: May have GCP data for their imagery
- **Access**: Commercial license required

#### Google Earth Engine
- **Website**: https://earthengine.google.com/
- **GCP Data**: May have some GCP datasets
- **Access**: Requires Google account and approval

### 3. Academic/Research Sources

#### OpenTopography
- **Website**: https://opentopography.org/
- **GCP Data**: May have some control point data
- **Access**: Free for research/education

#### UNAVCO
- **Website**: https://www.unavco.org/
- **GCP Data**: Geodetic control points
- **Access**: Free for research

### 4. Community Sources

#### OpenStreetMap (OSM)
- **Website**: https://www.openstreetmap.org/
- **GCP Data**: Not directly, but can extract landmarks/features
- **Access**: Free, via Overpass API
- **Note**: Would need to identify photo-identifiable features

#### Mapillary
- **Website**: https://www.mapillary.com/
- **GCP Data**: Street-level imagery with geotags
- **Access**: API available, may have usage limits

## Recommended Approach While Waiting for USGS Access

### Option 1: Use NOAA NGS Imagery Ground Control Point Archive ⭐ **BEST OPTION**

This is the most practical solution right now:

1. **Download KMZ files** for your target states/regions
2. **Parse and import** into a local database or directly into your system
3. **Query by bounding box** from your local database
4. **Use immediately** - no API access needed!

**Advantages**:
- ✅ Free and publicly available
- ✅ Photo-identifiable GCPs
- ✅ Designed for aerial photogrammetry
- ✅ No API access required
- ✅ Can be cached locally for fast queries

**Implementation**: I can help you create a KMZ parser and local database loader if you want.

### Option 2: Use Mock Data for Development

Continue using mock data to:
- Test your workflow
- Validate filtering and export functionality
- Develop spatial distribution analysis
- Test with different scenarios

### Option 2: Set Up Local GCP Database

1. **Collect GCPs manually**:
   - Use GPS to collect control points in your target areas
   - Store in a local database (PostgreSQL/PostGIS, SQLite, etc.)
   - Create a custom client to query your database

2. **Import existing datasets**:
   - Download NGS control points for your area
   - Import into local database
   - Create custom client

### Option 3: Create Custom GCP Source Client

You can extend the `AlternativeGCPClient` or create a new client:

```python
# Example: Custom local database client
class LocalGCPClient:
    def __init__(self, database_path: str):
        self.db_path = database_path
    
    def find_gcps_by_bbox(self, bbox, max_results=100):
        # Query local database
        # Return GCPs in standard format
        pass
```

## Configuration Summary

### Currently Working (Mock Data)
- ✅ USGS client (mock data)
- ✅ NOAA client (mock data)
- ✅ All filtering and export functionality
- ✅ Spatial distribution analysis

### Needs Configuration
- ⚠️ USGS API (waiting for M2M access approval)
- ⚠️ NOAA API (needs endpoint configuration)
- ⚠️ Other sources (need implementation)

### Quick Start: Use Mock Data

For now, you can use the system with mock data:

```python
from research_gcp_support import GCPFinder

# Mock data will be used automatically
finder = GCPFinder()
gcps = finder.find_gcps(h3_cells=your_h3_cells)

# All functionality works with mock data:
# - Filtering
# - Spatial distribution analysis
# - Export to MetaShape/ArcGIS formats
```

## Next Steps

1. **Wait for USGS M2M approval** - This is your best bet for real GCP data
2. **Research NOAA NGS API** - Check if they have an API you can use
3. **Consider local sources** - Contact state/local GIS offices
4. **Continue development** - Use mock data to perfect your workflow

## Questions to Ask NOAA/NGS

If you contact NOAA/NGS about API access:

1. Do you have an API for accessing control point databases?
2. What format is the data in?
3. Are the control points photo-identifiable?
4. What are the access requirements/restrictions?
5. Is there bulk download available?
6. Are there rate limits?

## Questions to Ask State/Local Sources

1. Do you maintain a geodetic control point database?
2. Is the data publicly available?
3. What format is it in?
4. Are the points photo-identifiable?
5. Can we access via API or bulk download?

