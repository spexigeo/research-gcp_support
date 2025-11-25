"""Basemap downloader and visualization utilities."""

import math
import time
import requests
from typing import Tuple, Optional, List, Dict
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import io
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """Convert lat/lon to tile coordinates."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile: int, ytile: int, zoom: int) -> Tuple[float, float]:
    """Convert tile coordinates to lat/lon of top-left corner."""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


def get_tile_url(xtile: int, ytile: int, zoom: int, source: str = "openstreetmap") -> str:
    """Get URL for a tile."""
    if source == "openstreetmap":
        return f"https://tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png"
    elif source == "esri_world_imagery" or source == "esri":
        return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ytile}/{xtile}"
    else:
        raise ValueError(f"Unknown tile source: {source}")


def download_tile(xtile: int, ytile: int, zoom: int, source: str = "openstreetmap", 
                  verbose: bool = False, retries: int = 2) -> Optional[Image.Image]:
    """Download a single tile with retry logic."""
    url = get_tile_url(xtile, ytile, zoom, source)
    
    headers = {
        'User-Agent': 'research-gcp-support/0.1.0'
    }
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img
        except requests.exceptions.HTTPError as e:
            if attempt < retries:
                time.sleep(0.1 * (attempt + 1))
                continue
            if verbose:
                status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 'unknown'
                print(f"Warning: HTTP error downloading tile {zoom}/{xtile}/{ytile}: {e} (Status: {status_code})")
            return None
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                time.sleep(0.1 * (attempt + 1))
                continue
            if verbose:
                print(f"Warning: Request error downloading tile {zoom}/{xtile}/{ytile}: {e}")
            return None
        except Exception as e:
            if attempt < retries:
                time.sleep(0.1 * (attempt + 1))
                continue
            if verbose:
                print(f"Warning: Failed to download tile {zoom}/{xtile}/{ytile}: {e}")
            return None
    
    return None


def calculate_zoom_level(bbox: Tuple[float, float, float, float], 
                         max_tiles: int = 64, 
                         target_resolution: Optional[float] = None) -> int:
    """
    Calculate appropriate zoom level based on bounding box size or target resolution.
    
    Args:
        bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
        max_tiles: Maximum number of tiles to download (default 64)
        target_resolution: Target resolution in meters per pixel (optional)
        
    Returns:
        Zoom level
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    
    if target_resolution:
        # Calculate zoom based on target resolution
        center_lat = (min_lat + max_lat) / 2
        meters_per_pixel_at_equator = 156543.03392
        meters_per_pixel = meters_per_pixel_at_equator * math.cos(math.radians(center_lat))
        
        for zoom in range(1, 20):
            tile_size_meters = meters_per_pixel * 256 / (2 ** zoom)
            if tile_size_meters <= target_resolution:
                return zoom
        return 18
    
    # Calculate based on bounding box size
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    area_deg2 = lat_range * lon_range
    
    if area_deg2 < 0.0001:
        base_zoom = 16
    elif area_deg2 < 0.001:
        base_zoom = 15
    elif area_deg2 < 0.01:
        base_zoom = 13
    elif area_deg2 < 0.1:
        base_zoom = 11
    else:
        base_zoom = 9
    
    # Check tile count and adjust if needed
    for zoom in range(base_zoom, base_zoom - 5, -1):
        if zoom < 1:
            break
        xtile_min, ytile_min = deg2num(min_lat, min_lon, zoom)
        xtile_max, ytile_max = deg2num(max_lat, max_lon, zoom)
        
        num_tiles = (xtile_max - xtile_min + 1) * (ytile_max - ytile_min + 1)
        if num_tiles <= max_tiles:
            return zoom
    
    return max(1, base_zoom)


def download_basemap(
    bbox: Tuple[float, float, float, float],
    output_path: str,
    source: str = "openstreetmap",
    zoom: Optional[int] = None,
    target_resolution: Optional[float] = None
) -> str:
    """
    Download basemap tiles and create a GeoTIFF.
    
    Args:
        bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
        output_path: Path to save GeoTIFF
        source: Tile source ('openstreetmap' or 'esri_world_imagery')
        zoom: Zoom level (auto-calculated if None)
        target_resolution: Target resolution in meters per pixel
        
    Returns:
        Path to saved GeoTIFF
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    
    # Validate bounding box
    if min_lat >= max_lat:
        raise ValueError(f"Invalid bounding box: min_lat ({min_lat}) must be less than max_lat ({max_lat})")
    if min_lon >= max_lon:
        raise ValueError(f"Invalid bounding box: min_lon ({min_lon}) must be less than max_lon ({max_lon})")
    
    if zoom is None:
        zoom = calculate_zoom_level(bbox, target_resolution=target_resolution)
    
    print(f"Downloading {source} basemap at zoom level {zoom}...")
    
    # Calculate tile range
    xtile_min, ytile_max = deg2num(min_lat, min_lon, zoom)
    xtile_max, ytile_min = deg2num(max_lat, max_lon, zoom)
    
    # Ensure correct ordering
    if xtile_min > xtile_max:
        xtile_min, xtile_max = xtile_max, xtile_min
    if ytile_min > ytile_max:
        ytile_min, ytile_max = ytile_max, ytile_min
    
    print(f"  Tile range: X [{xtile_min}, {xtile_max}], Y [{ytile_min}, {ytile_max}]")
    
    # Download tiles
    tiles = []
    total_tiles = (xtile_max - xtile_min + 1) * (ytile_max - ytile_min + 1)
    downloaded = 0
    
    for y in range(ytile_min, ytile_max + 1):
        row = []
        for x in range(xtile_min, xtile_max + 1):
            tile = download_tile(x, y, zoom, source, verbose=False)
            if tile:
                row.append(tile)
                downloaded += 1
            else:
                # Create blank tile if download failed
                row.append(Image.new('RGB', (256, 256), color='gray'))
            if (downloaded % 10 == 0) or (downloaded == total_tiles):
                print(f"  Downloaded {downloaded}/{total_tiles} tiles...", end='\r')
        if row:
            tiles.append(row)
    
    print(f"\n  Downloaded {downloaded}/{total_tiles} tiles")
    
    if not tiles or not tiles[0]:
        raise ValueError("Failed to download any tiles")
    
    # Stitch tiles together
    tile_height = tiles[0][0].height
    tile_width = tiles[0][0].width
    
    stitched = Image.new('RGB', (len(tiles[0]) * tile_width, len(tiles) * tile_height))
    
    for y_idx, row in enumerate(tiles):
        for x_idx, tile in enumerate(row):
            stitched.paste(tile, (x_idx * tile_width, y_idx * tile_height))
    
    # Calculate bounds for GeoTIFF
    top_left_lat, top_left_lon = num2deg(xtile_min, ytile_min, zoom)
    bottom_right_lat, bottom_right_lon = num2deg(xtile_max + 1, ytile_max + 1, zoom)
    
    # Create transform
    transform = from_bounds(
        top_left_lon, bottom_right_lat,
        bottom_right_lon, top_left_lat,
        stitched.width, stitched.height
    )
    
    # Save as GeoTIFF
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path.with_suffix('.tif')
    
    # Convert PIL image to numpy array
    img_array = np.array(stitched)
    
    with rasterio.open(
        str(output_path),
        'w',
        driver='GTiff',
        height=stitched.height,
        width=stitched.width,
        count=3,
        dtype=rasterio.uint8,
        crs=CRS.from_epsg(4326),
        transform=transform
    ) as dst:
        # Write RGB bands
        for i in range(3):
            dst.write(img_array[:, :, i], i + 1)
    
    print(f"✓ Saved basemap to {output_path}")
    return str(output_path)


def visualize_gcps_on_basemap(
    gcps: List[Dict],
    bbox: Tuple[float, float, float, float],
    basemap_path: Optional[str] = None,
    basemap_source: str = "openstreetmap",
    output_path: Optional[str] = None,
    title: str = "GCPs on Basemap",
    figsize: Tuple[int, int] = (12, 10),
    original_gcps: Optional[List[Dict]] = None,
    original_color: str = 'orange',
    filtered_color: str = 'red',
    original_label: str = 'Original GCPs',
    filtered_label: str = 'Filtered GCPs'
) -> str:
    """
    Visualize GCPs overlaid on a basemap.
    
    Args:
        gcps: List of filtered GCP dictionaries with 'lat' and 'lon' keys
        bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
        basemap_path: Path to existing basemap GeoTIFF (if None, will download)
        basemap_source: Source for basemap if downloading ('openstreetmap', 'esri', or 'esri_world_imagery')
        output_path: Path to save visualization (if None, displays only)
        title: Title for the plot
        figsize: Figure size (width, height)
        original_gcps: Optional list of original GCPs (before filtering) to display
        original_color: Color for original GCPs (default: 'orange')
        filtered_color: Color for filtered GCPs (default: 'red')
        original_label: Label for original GCPs in legend
        filtered_label: Label for filtered GCPs in legend
        
    Returns:
        Path to saved visualization or empty string if just displayed
    """
    import geopandas as gpd
    from shapely.geometry import Point
    
    min_lat, min_lon, max_lat, max_lon = bbox
    
    # Download basemap if not provided
    if basemap_path is None or not Path(basemap_path).exists():
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        basemap_path = str(temp_dir / f"basemap_{basemap_source}_{int(time.time())}.tif")
        download_basemap(bbox, basemap_path, source=basemap_source)
    
    # Check if we need to download a basemap for GCP area
    # Collect GCP coordinates first to check if they're outside the provided basemap
    gcp_lons_temp = []
    gcp_lats_temp = []
    if original_gcps:
        for gcp in original_gcps:
            if 'lat' in gcp and 'lon' in gcp:
                gcp_lons_temp.append(gcp['lon'])
                gcp_lats_temp.append(gcp['lat'])
    if not gcp_lons_temp and gcps:
        for gcp in gcps:
            if 'lat' in gcp and 'lon' in gcp:
                gcp_lons_temp.append(gcp['lon'])
                gcp_lats_temp.append(gcp['lat'])
    
    # If GCPs are found and outside the basemap bounds, download a new basemap for GCP area
    if gcp_lons_temp and gcp_lats_temp:
        # Load existing basemap to check bounds
        with rasterio.open(basemap_path) as src:
            existing_bounds = src.bounds
        
        gcp_min_lon = min(gcp_lons_temp)
        gcp_max_lon = max(gcp_lons_temp)
        gcp_min_lat = min(gcp_lats_temp)
        gcp_max_lat = max(gcp_lats_temp)
        
        # Check if GCPs are outside existing basemap
        if (gcp_min_lon < existing_bounds.left - 0.1 or gcp_max_lon > existing_bounds.right + 0.1 or
            gcp_min_lat < existing_bounds.bottom - 0.1 or gcp_max_lat > existing_bounds.top + 0.1):
            print(f"  [DEBUG] GCPs are outside existing basemap, downloading new basemap for GCP area...")
            # Create GCP bbox with padding
            padding_lon = (gcp_max_lon - gcp_min_lon) * 0.1
            padding_lat = (gcp_max_lat - gcp_min_lat) * 0.1
            gcp_bbox = (
                max(gcp_min_lat - padding_lat, -90),
                max(gcp_min_lon - padding_lon, -180),
                min(gcp_max_lat + padding_lat, 90),
                min(gcp_max_lon + padding_lon, 180)
            )
            # Download new basemap for GCP area
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            basemap_path = str(temp_dir / f"basemap_{basemap_source}_gcp_{int(time.time())}.tif")
            try:
                download_basemap(gcp_bbox, basemap_path, source=basemap_source)
                print(f"  [DEBUG] ✓ Downloaded basemap for GCP area")
            except Exception as e:
                print(f"  [DEBUG] ⚠️  Could not download basemap for GCP area: {e}")
                print(f"  [DEBUG]   Using original basemap (may show gray area where GCPs are)")
    
    # Load basemap
    with rasterio.open(basemap_path) as src:
        basemap_img = src.read([1, 2, 3])  # RGB bands
        basemap_img = np.transpose(basemap_img, (1, 2, 0))  # Change to (H, W, C)
        basemap_bounds = src.bounds
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Collect GCP coordinates for bounding box calculation (do this FIRST)
        gcp_lons = []
        gcp_lats = []
        
        # Collect original GCPs first (if provided)
        if original_gcps:
            for gcp in original_gcps:
                if 'lat' in gcp and 'lon' in gcp:
                    gcp_lons.append(gcp['lon'])
                    gcp_lats.append(gcp['lat'])
        
        # If no original GCPs, use filtered GCPs
        if not gcp_lons and gcps:
            for gcp in gcps:
                if 'lat' in gcp and 'lon' in gcp:
                    gcp_lons.append(gcp['lon'])
                    gcp_lats.append(gcp['lat'])
        
        # Display basemap
        # Note: basemap may not cover GCP area if GCPs are outside search bbox
        # Always show the basemap, even if it doesn't cover the full plot area
        # Use interpolation to make it look better when zoomed
        im = ax.imshow(
            basemap_img,
            extent=[basemap_bounds.left, basemap_bounds.right, 
                   basemap_bounds.bottom, basemap_bounds.top],
            origin='upper',
            zorder=1,  # Basemap should be in the background
            aspect='auto',  # Allow aspect ratio to adjust
            interpolation='bilinear'  # Smooth interpolation
        )
        
        # Set background color to light gray (will show if basemap doesn't cover area)
        # This ensures we see something even if basemap is outside plot limits
        ax.set_facecolor('#E0E0E0')  # Light gray background
        
        # If GCPs are outside basemap bounds, add a note
        if gcp_lons and gcp_lats:
            gcp_min_lon = min(gcp_lons)
            gcp_max_lon = max(gcp_lons)
            gcp_min_lat = min(gcp_lats)
            gcp_max_lat = max(gcp_lats)
            
            if (gcp_min_lon < basemap_bounds.left or gcp_max_lon > basemap_bounds.right or
                gcp_min_lat < basemap_bounds.bottom or gcp_max_lat > basemap_bounds.top):
                print(f"  [DEBUG] WARNING: GCPs are outside basemap bounds!")
                print(f"    Basemap covers: lon [{basemap_bounds.left:.6f}, {basemap_bounds.right:.6f}], lat [{basemap_bounds.bottom:.6f}, {basemap_bounds.top:.6f}]")
                print(f"    GCPs are at: lon [{gcp_min_lon:.6f}, {gcp_max_lon:.6f}], lat [{gcp_min_lat:.6f}, {gcp_max_lat:.6f}]")
                print(f"    The basemap may show empty/gray area where GCPs are located")
        
        # Debug output
        print(f"\n[DEBUG] Visualization debug info:")
        print(f"  Original GCPs: {len(original_gcps) if original_gcps else 0}")
        print(f"  Filtered GCPs: {len(gcps)}")
        print(f"  GCP coordinates collected: {len(gcp_lons)} lons, {len(gcp_lats)} lats")
        if gcp_lons and gcp_lats:
            print(f"  GCP lon range: {min(gcp_lons):.6f} to {max(gcp_lons):.6f}")
            print(f"  GCP lat range: {min(gcp_lats):.6f} to {max(gcp_lats):.6f}")
            print(f"  Basemap bounds: lon [{basemap_bounds.left:.6f}, {basemap_bounds.right:.6f}], lat [{basemap_bounds.bottom:.6f}, {basemap_bounds.top:.6f}]")
            print(f"  Plot limits: lon [{min_lon:.6f}, {max_lon:.6f}], lat [{min_lat:.6f}, {max_lat:.6f}]")
        
        # Draw yellow bounding box around all GCPs (minimum bounding box)
        if gcp_lons and gcp_lats:
            gcp_min_lon = min(gcp_lons)
            gcp_max_lon = max(gcp_lons)
            gcp_min_lat = min(gcp_lats)
            gcp_max_lat = max(gcp_lats)
            
            print(f"  GCP bounding box: lon [{gcp_min_lon:.6f}, {gcp_max_lon:.6f}], lat [{gcp_min_lat:.6f}, {gcp_max_lat:.6f}]")
            
            # Add some padding (5% of the range)
            lon_range = gcp_max_lon - gcp_min_lon
            lat_range = gcp_max_lat - gcp_min_lat
            padding_lon = max(lon_range * 0.05, 0.001)  # At least 0.001 degrees
            padding_lat = max(lat_range * 0.05, 0.001)
            
            bbox_rect = mpatches.Rectangle(
                (gcp_min_lon - padding_lon, gcp_min_lat - padding_lat),
                (gcp_max_lon - gcp_min_lon) + 2 * padding_lon,
                (gcp_max_lat - gcp_min_lat) + 2 * padding_lat,
                linewidth=4,
                edgecolor='yellow',
                facecolor='none',
                linestyle='--',
                zorder=7,
                alpha=0.9,
                label='GCP Bounding Box'
            )
            ax.add_patch(bbox_rect)
            print(f"  ✓ Yellow bounding box drawn")
        else:
            print(f"  ⚠️  No GCP coordinates to draw bounding box")
        
        # Create a set of filtered GCP IDs for comparison
        filtered_gcp_ids = set()
        if gcps:
            for gcp in gcps:
                gcp_id = gcp.get('id', gcp.get('label'))
                if gcp_id:
                    filtered_gcp_ids.add(gcp_id)
                else:
                    # Use location as fallback
                    lat = gcp.get('lat', gcp.get('latitude'))
                    lon = gcp.get('lon', gcp.get('longitude'))
                    if lat is not None and lon is not None:
                        filtered_gcp_ids.add((round(lat, 6), round(lon, 6)))
        
        # Plot original GCPs first (if provided)
        if original_gcps:
            original_lons = []
            original_lats = []
            for gcp in original_gcps:
                if 'lat' in gcp and 'lon' in gcp:
                    original_lons.append(gcp['lon'])
                    original_lats.append(gcp['lat'])
            
            if original_lons and original_lats:
                print(f"  [DEBUG] Plotting {len(original_lons)} original GCPs")
                print(f"    Sample coordinates: ({original_lons[0]:.6f}, {original_lats[0]:.6f})")
                # Plot original GCPs as very large filled circles with outline
                # Use even larger markers and ensure they're on top
                # White background circle for visibility (largest, behind)
                ax.scatter(original_lons, original_lats,
                          s=3000,  # Very large marker size
                          c='white',
                          marker='o',
                          edgecolors='none',
                          zorder=15,
                          alpha=1.0)
                # Orange outline circle (thick border)
                ax.scatter(original_lons, original_lats, 
                          s=3000,
                          c='none',
                          edgecolors=original_color,
                          linewidths=6,
                          marker='o',
                          label=original_label,
                          zorder=16,
                          alpha=1.0)
                # Inner filled circle
                ax.scatter(original_lons, original_lats,
                          s=2000,
                          c=original_color,
                          marker='o',
                          edgecolors='white',
                          linewidths=3,
                          zorder=17,
                          alpha=0.8)
                print(f"    ✓ Original GCPs plotted with size 3000")
            else:
                print(f"  [DEBUG] No valid original GCP coordinates found")
        
        # Plot filtered GCPs
        if gcps:
            filtered_lons = []
            filtered_lats = []
            filtered_ids = []
            for gcp in gcps:
                if 'lat' in gcp and 'lon' in gcp:
                    filtered_lons.append(gcp['lon'])
                    filtered_lats.append(gcp['lat'])
                    filtered_ids.append(gcp.get('id', gcp.get('label', '')))
            
            if filtered_lons and filtered_lats:
                print(f"  [DEBUG] Plotting {len(filtered_lons)} filtered GCPs")
                print(f"    Sample coordinates: ({filtered_lons[0]:.6f}, {filtered_lats[0]:.6f})")
                # Plot filtered GCPs as smaller but visible X markers with filled circle background
                # White background circle for visibility (behind)
                ax.scatter(filtered_lons, filtered_lats,
                          s=400,  # Smaller but visible marker size
                          c='white',
                          marker='o',
                          edgecolors='black',
                          linewidths=1.5,
                          zorder=18,
                          alpha=0.9)
                # Red X marker (on top)
                ax.scatter(filtered_lons, filtered_lats,
                          s=400,
                          c=filtered_color,
                          marker='x',
                          linewidths=3,
                          label=filtered_label,
                          zorder=20,
                          alpha=1.0)
                # White X outline for contrast (behind red X)
                ax.scatter(filtered_lons, filtered_lats,
                          s=400,
                          c='white',
                          marker='x',
                          linewidths=4,
                          zorder=19,
                          alpha=0.9)
                
                # Add labels with GCP IDs if available (only for filtered GCPs)
                for idx, (lon, lat, gcp_id) in enumerate(zip(filtered_lons, filtered_lats, filtered_ids)):
                    if gcp_id:
                        ax.annotate(
                            gcp_id,
                            (lon, lat),
                            xytext=(8, 8),
                            textcoords='offset points',
                            fontsize=10,
                            color='yellow',
                            weight='bold',
                            bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8, edgecolor='white', linewidth=1.5)
                        )
                print(f"    ✓ Filtered GCPs plotted")
            else:
                print(f"  [DEBUG] No valid filtered GCP coordinates found")
        
        # Set plot limits based on GCP bounding box (if available), otherwise use search bbox
        # But ensure basemap area is also visible if it overlaps
        if gcp_lons and gcp_lats:
            # Use GCP bounding box with padding
            gcp_min_lon = min(gcp_lons)
            gcp_max_lon = max(gcp_lons)
            gcp_min_lat = min(gcp_lats)
            gcp_max_lat = max(gcp_lats)
            
            # Add padding (10% of range, minimum 0.01 degrees)
            lon_range = gcp_max_lon - gcp_min_lon
            lat_range = gcp_max_lat - gcp_min_lat
            padding_lon = max(lon_range * 0.1, 0.01)
            padding_lat = max(lat_range * 0.1, 0.01)
            
            plot_min_lon = gcp_min_lon - padding_lon
            plot_max_lon = gcp_max_lon + padding_lon
            plot_min_lat = gcp_min_lat - padding_lat
            plot_max_lat = gcp_max_lat + padding_lat
            
            # If basemap overlaps with GCP area, include basemap bounds in plot limits
            # This ensures the basemap is visible
            basemap_overlaps = not (basemap_bounds.right < plot_min_lon or basemap_bounds.left > plot_max_lon or
                                   basemap_bounds.top < plot_min_lat or basemap_bounds.bottom > plot_max_lat)
            
            if basemap_overlaps:
                # Expand plot limits to include basemap area
                plot_min_lon = min(plot_min_lon, basemap_bounds.left)
                plot_max_lon = max(plot_max_lon, basemap_bounds.right)
                plot_min_lat = min(plot_min_lat, basemap_bounds.bottom)
                plot_max_lat = max(plot_max_lat, basemap_bounds.top)
                print(f"  [DEBUG] Basemap overlaps with GCP area, including basemap in plot limits")
            
            print(f"  [DEBUG] Setting plot limits to: lon [{plot_min_lon:.6f}, {plot_max_lon:.6f}], lat [{plot_min_lat:.6f}, {plot_max_lat:.6f}]")
        else:
            # Fall back to search bbox
            plot_min_lon = min_lon
            plot_max_lon = max_lon
            plot_min_lat = min_lat
            plot_max_lat = max_lat
            print(f"  [DEBUG] No GCPs found, using search bbox for plot limits")
        
        ax.set_xlim(plot_min_lon, plot_max_lon)
        ax.set_ylim(plot_min_lat, plot_max_lat)
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(title)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save or display
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✓ Saved visualization to {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return ""


def download_naip_basemap(
    bbox: Tuple[float, float, float, float],
    output_path: str,
    usgs_client=None
) -> Optional[str]:
    """
    Attempt to download NAIP basemap using USGS M2M API.
    
    Note: This requires USGS API access and NAIP dataset permissions.
    
    Args:
        bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
        output_path: Path to save GeoTIFF
        usgs_client: USGSGCPClient instance with authentication
        
    Returns:
        Path to saved GeoTIFF if successful, None otherwise
    """
    if usgs_client is None or not usgs_client.api_key:
        print("⚠️  NAIP download requires authenticated USGS client")
        return None
    
    print("⚠️  NAIP basemap download via USGS API not yet fully implemented")
    print("   This would require:")
    print("   1. Searching for NAIP scenes in the bounding box")
    print("   2. Downloading scene data")
    print("   3. Mosaicking scenes into a basemap")
    print("   For now, using ESRI World Imagery as a high-resolution alternative")
    
    # Fall back to ESRI World Imagery
    return download_basemap(bbox, output_path, source="esri_world_imagery")

