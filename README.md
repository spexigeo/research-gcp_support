# GCP Support

A Python library for automatically finding and downloading Ground Control Points (GCPs) from online sources for drone imagery processing. Supports H3 cell-based area selection and exports GCPs in formats compatible with MetaShape and ArcGIS Pro.

## Features

1. **H3 Cell to Bounding Box**: Convert H3 cell identifiers to latitude/longitude bounding boxes
2. **Multi-Source GCP Discovery**: Automatically find GCPs from USGS (primary) and NOAA (fallback) sources
3. **Automatic NOAA Fallback**: If USGS returns fewer GCPs than the threshold (default: 10), automatically searches NOAA databases
4. **GCP Filtering**: Filter GCPs for geometric accuracy, photo-identifiability, and area coverage
5. **Multi-Format Export**: Export GCPs in formats compatible with:
   - Agisoft MetaShape
   - ArcGIS Pro

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from gcp_support import GCPFinder

# Initialize finder
finder = GCPFinder()

# Get bounding box from H3 cells
h3_cells = ['8a2a1072b4fffff', '8a2a1072b5fffff']
bbox = finder.h3_cells_to_bbox(h3_cells)

# Find and download GCPs
# Searches USGS first, then NOAA if fewer than 10 GCPs found (configurable)
gcps = finder.find_gcps(h3_cells=h3_cells)

# Customize the threshold for NOAA fallback
gcps = finder.find_gcps(h3_cells=h3_cells, min_gcp_threshold=15)

# Export for MetaShape
finder.export_metashape(gcps, 'gcps_metashape.txt')

# Export for ArcGIS Pro
finder.export_arcgis(gcps, 'gcps_arcgis.csv')

# Export all formats at once
finder.export_all(gcps, './output', 'my_gcps')
```

### Testing with Mock Data

For testing without API access, you can use mock GCPs:

```python
from gcp_support.mock_gcp import MockGCPGenerator
from gcp_support import GCPFinder

# Generate mock GCPs
bbox = (40.0, -75.0, 41.0, -74.0)
mock_gcps = MockGCPGenerator.generate_gcps_in_bbox(bbox, count=20)

# Use with finder for export
finder = GCPFinder()
finder.export_all(mock_gcps, './output', 'test_gcps')
```

### Command Line Interface

```bash
# From H3 cells
python -m gcp_support.cli --h3-cells 8a2a1072b4fffff 8a2a1072b5fffff --output-dir ./gcps

# From bounding box
python -m gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --output-dir ./gcps

# With custom NOAA fallback threshold
python -m gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --min-gcp-threshold 15 --output-dir ./gcps

# With NOAA API key
python -m gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --noaa-api-key YOUR_KEY --output-dir ./gcps
```

## Requirements

- Python 3.8+
- h3-py: H3 geospatial indexing
- requests: HTTP requests for API calls
- geopandas: Geospatial data handling
- shapely: Geometric operations

## Data Sources

### Primary Source: USGS
- USGS Ground Control Points (via API) - **Requires API configuration** (see USGS_API_NOTES.md)
- Searched first by default

### Fallback Source: NOAA
- NOAA Ground Control Points (via API) - **Requires API configuration**
- Automatically searched if USGS returns fewer GCPs than the threshold (default: 10)
- Threshold is configurable via `min_gcp_threshold` parameter

### Testing
- Mock GCP generator for testing (see `mock_gcp.py`)
- Both USGS and NOAA clients can use mock data for development

### Configuration

```python
# Initialize with custom threshold
finder = GCPFinder(
    min_gcp_threshold=15,  # Search NOAA if USGS returns < 15 GCPs
    noaa_api_key='your_noaa_key'  # Optional NOAA API key
)

# Or override threshold per search
gcps = finder.find_gcps(bbox=bbox, min_gcp_threshold=20)
```

See `USGS_API_NOTES.md` for more information on configuring data sources.

## License

MIT

