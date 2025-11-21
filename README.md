# GCP Support

A Python library for automatically finding and downloading Ground Control Points (GCPs) from online sources for drone imagery processing. Supports H3 cell-based area selection and exports GCPs in formats compatible with MetaShape and ArcGIS Pro.

## Features

1. **H3 Cell to Bounding Box**: Convert H3 cell identifiers to latitude/longitude bounding boxes
2. **Multi-Source GCP Discovery**: Automatically find GCPs from USGS (primary) and NOAA (fallback) sources
3. **Automatic NOAA Fallback**: If USGS returns fewer GCPs than the threshold (default: 10), automatically searches NOAA databases
4. **GCP Filtering**: Filter GCPs for geometric accuracy, photo-identifiability, and area coverage
5. **Spatial Distribution Analysis**: Automatically evaluates and scores GCP spatial distribution to ensure good coverage for bundle adjustment
6. **Multi-Format Export**: Export GCPs in formats compatible with:
   - Agisoft MetaShape
   - ArcGIS Pro

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from research_gcp_support import GCPFinder

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

# Access spatial distribution metrics
if finder.last_spatial_metrics:
    print(f"Spread score: {finder.last_spatial_metrics['spread_score']:.3f}")
    print(f"Confidence score: {finder.last_spatial_metrics['confidence_score']:.3f}")
```

### Testing with Mock Data

For testing without API access, you can use mock GCPs:

```python
from research_gcp_support.mock_gcp import MockGCPGenerator
from research_gcp_support import GCPFinder

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
python -m research_gcp_support.cli --h3-cells 8a2a1072b4fffff 8a2a1072b5fffff --output-dir ./gcps

# From bounding box
python -m research_gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --output-dir ./gcps

# With custom NOAA fallback threshold
python -m research_gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --min-gcp-threshold 15 --output-dir ./gcps

# With NOAA API key
python -m research_gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --noaa-api-key YOUR_KEY --output-dir ./gcps

# With spatial distribution filtering (reject GCP sets with poor distribution)
python -m research_gcp_support.cli --bbox 40.0 -75.0 41.0 -74.0 --min-spread-score 0.5 --min-confidence-score 0.6 --output-dir ./gcps
```

### Spatial Distribution Analysis

The library automatically evaluates the spatial distribution of GCPs to ensure they provide good geometric control across the entire area. This is critical for accurate bundle adjustment in photogrammetry software like MetaShape.

```python
from research_gcp_support import GCPFinder
from research_gcp_support.gcp_filter import calculate_spatial_distribution_score

# Find GCPs (spatial metrics are automatically calculated)
finder = GCPFinder()
gcps = finder.find_gcps(h3_cells=h3_cells)

# Access spatial distribution metrics
if finder.last_spatial_metrics:
    metrics = finder.last_spatial_metrics
    print(f"Spread score: {metrics['spread_score']:.3f} (0-1, higher is better)")
    print(f"Confidence score: {metrics['confidence_score']:.3f} (0-1, higher is better)")
    print(f"Convex hull ratio: {metrics['convex_hull_ratio']:.3f}")
    print(f"Grid coverage: {metrics['grid_coverage']:.3f}")

# Filter out GCP sets with poor spatial distribution
finder = GCPFinder(
    min_spread_score=0.5,      # Reject if spread score < 0.5
    min_confidence_score=0.6    # Reject if confidence score < 0.6
)
gcps = finder.find_gcps(h3_cells=h3_cells)  # Returns empty list if distribution is poor

# Or manually check distribution
from research_gcp_support.gcp_filter import calculate_spatial_distribution_score
metrics = calculate_spatial_distribution_score(gcps, bbox)
if metrics['confidence_score'] < 0.5:
    print("Warning: GCPs may be clustered, which could affect bundle adjustment quality")
```

**Spatial Distribution Metrics:**
- **Spread Score** (0-1): Overall measure of how well GCPs are distributed across the area
  - Combines convex hull ratio, nearest neighbor distances, and grid coverage
  - Higher values indicate better distribution
- **Confidence Score** (0-1): Overall confidence in the GCP set quality
  - Combines spread score with the number of GCPs
  - Higher values indicate higher confidence for bundle adjustment
- **Convex Hull Ratio**: Ratio of convex hull area to bounding box area
  - Higher values indicate GCPs cover more of the area
- **Grid Coverage**: Fraction of grid cells (3x3) that contain at least one GCP
  - Higher values indicate better spatial coverage

## Requirements

- Python 3.8+
- h3-py: H3 geospatial indexing
- requests: HTTP requests for API calls
- geopandas: Geospatial data handling
- shapely: Geometric operations
- scipy: Spatial distance calculations

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
# Initialize with custom threshold and spatial distribution filtering
finder = GCPFinder(
    min_gcp_threshold=15,  # Search NOAA if USGS returns < 15 GCPs
    noaa_api_key='your_noaa_key',  # Optional NOAA API key
    min_spread_score=0.5,  # Optional: reject GCP sets with poor distribution
    min_confidence_score=0.6  # Optional: reject GCP sets with low confidence
)

# Or override threshold per search
gcps = finder.find_gcps(bbox=bbox, min_gcp_threshold=20)
```

See `USGS_API_NOTES.md` for more information on configuring data sources.

## License

MIT

