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
    figsize: Tuple[int, int] = (12, 10)
) -> str:
    """
    Visualize GCPs overlaid on a basemap.
    
    Args:
        gcps: List of GCP dictionaries with 'lat' and 'lon' keys
        bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
        basemap_path: Path to existing basemap GeoTIFF (if None, will download)
        basemap_source: Source for basemap if downloading ('openstreetmap', 'esri', or 'esri_world_imagery')
        output_path: Path to save visualization (if None, displays only)
        title: Title for the plot
        figsize: Figure size (width, height)
        
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
    
    # Load basemap
    with rasterio.open(basemap_path) as src:
        basemap_img = src.read([1, 2, 3])  # RGB bands
        basemap_img = np.transpose(basemap_img, (1, 2, 0))  # Change to (H, W, C)
        basemap_bounds = src.bounds
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Display basemap
        ax.imshow(
            basemap_img,
            extent=[basemap_bounds.left, basemap_bounds.right, 
                   basemap_bounds.bottom, basemap_bounds.top],
            origin='upper'
        )
        
        # Create GCP points
        if gcps:
            gcp_points = []
            for gcp in gcps:
                if 'lat' in gcp and 'lon' in gcp:
                    gcp_points.append(Point(gcp['lon'], gcp['lat']))
            
            if gcp_points:
                gcp_gdf = gpd.GeoDataFrame(
                    {'geometry': gcp_points},
                    crs='EPSG:4326'
                )
                
                # Plot GCPs
                gcp_gdf.plot(ax=ax, color='red', markersize=50, marker='x', 
                            linewidth=2, label='GCPs', zorder=10)
                
                # Add labels with GCP IDs if available
                for idx, gcp in enumerate(gcps):
                    if 'lat' in gcp and 'lon' in gcp and 'id' in gcp:
                        ax.annotate(
                            gcp['id'],
                            (gcp['lon'], gcp['lat']),
                            xytext=(5, 5),
                            textcoords='offset points',
                            fontsize=8,
                            color='yellow',
                            weight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
                        )
        
        # Set limits to bounding box
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(title)
        ax.legend()
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

