# Quick Start: Using Other GCP Sources

## Summary

While waiting for USGS M2M API access, here's what you need to know:

## Current Status

- ✅ **USGS**: Waiting for M2M access approval (then use application token)
- ⚠️ **NOAA**: Currently using mock data, but **NGS Imagery Ground Control Point Archive** is available
- ✅ **All other functionality**: Working (filtering, spatial distribution, export)

## Best Option Right Now: NOAA NGS Imagery Ground Control Point Archive

### Why This is Good

- ✅ **Free and publicly available** - No API access needed
- ✅ **Photo-identifiable GCPs** - Specifically for aerial photogrammetry
- ✅ **Organized by state** - Easy to download relevant data
- ✅ **KMZ format** - Can be parsed and loaded into your system

### How to Use

1. **Download KMZ files** for your target states:
   - Visit: https://www.ngs.noaa.gov/AERO/PhotoControl/ImageControlArchive.htm
   - Download KMZ files for states where you have drone imagery

2. **For now, the system uses mock data** - which works fine for testing

3. **When ready to implement real NOAA data**:
   - I can help you create a KMZ parser
   - Load GCPs into a local database (SQLite/PostGIS)
   - Update `noaa_gcp.py` to query the local database

## What Needs to Be Set

### For USGS (when M2M access is approved):

```python
# Option 1: Environment variable
export USGS_APPLICATION_TOKEN="your_token_here"

# Option 2: In code
finder = GCPFinder(usgs_application_token="your_token_here")

# Option 3: CLI
python -m gcp_support.cli --usgs-application-token "your_token" --h3-cells ...
```

### For NOAA (currently):

**Nothing needs to be set** - it uses mock data automatically.

**For real NOAA data** (when implemented):
- Download KMZ files from NGS archive
- No API key needed (it's free public data)
- Will need KMZ parser implementation

### For Other Sources:

- **CompassData**: Would need commercial license
- **State/Local**: Would need to contact individual sources
- **Custom Database**: Would need to implement custom client

## Recommended Workflow

### Right Now (While Waiting):

1. **Continue using mock data** - Everything works, just with simulated GCPs
2. **Test your workflow** - Validate filtering, spatial distribution, exports
3. **Download NOAA KMZ files** - Start collecting data for your target areas
4. **Wait for USGS M2M approval** - Then you'll have real USGS data

### When USGS Access is Ready:

1. **Get application token** from your USGS profile
2. **Set token** in environment variable or code
3. **Test with real USGS data**
4. **NOAA will still work as fallback** (using mock data until we implement KMZ parser)

### When Ready for Real NOAA Data:

1. **I can help implement KMZ parser** - Parse NGS archive files
2. **Load into local database** - For fast spatial queries
3. **Update `noaa_gcp.py`** - Query local database instead of mock data

## Quick Test

To test the current system (with mock data):

```python
from gcp_support import GCPFinder

# Works with mock data - no credentials needed
finder = GCPFinder()
gcps = finder.find_gcps(h3_cells=your_h3_cells)

# All features work:
# - Filtering by accuracy
# - Spatial distribution analysis  
# - Export to MetaShape/ArcGIS
```

## Next Steps

1. ✅ **System is ready** - Works with mock data
2. ⏳ **Wait for USGS M2M approval** - Then add application token
3. 📥 **Download NOAA KMZ files** - For your target states/regions
4. 🔧 **Implement KMZ parser** (when ready) - To use real NOAA data

## Questions?

- See `NOAA_AND_OTHER_SOURCES.md` for detailed information
- See `USGS_API_NOTES.md` for USGS setup
- Current implementation uses mock data - perfect for development and testing

