"""
Export GCPs to various formats for different software.
"""

from typing import List, Dict
import csv
import os


class MetaShapeExporter:
    """Export GCPs to Agisoft MetaShape format."""
    
    @staticmethod
    def export(gcps: List[Dict], output_path: str):
        """
        Export GCPs to MetaShape format.
        
        MetaShape typically uses a text file format with columns:
        Label, X, Y, Z, Accuracy, Enabled
        
        Or a CSV format with similar columns.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output file
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # Write header (MetaShape format)
            writer.writerow(['Label', 'X', 'Y', 'Z', 'Accuracy', 'Enabled'])
            
            for i, gcp in enumerate(gcps):
                label = gcp.get('id', gcp.get('label', f'GCP_{i+1}'))
                lon = gcp.get('lon', gcp.get('longitude', 0.0))
                lat = gcp.get('lat', gcp.get('latitude', 0.0))
                z = gcp.get('z', gcp.get('elevation', gcp.get('altitude', 0.0)))
                accuracy = gcp.get('accuracy', gcp.get('rmse', 1.0))
                enabled = '1'  # Default to enabled
                
                writer.writerow([label, lon, lat, z, accuracy, enabled])
    
    @staticmethod
    def export_marker_file(gcps: List[Dict], output_path: str):
        """
        Export GCPs as MetaShape marker file (XML format).
        
        This is an alternative format that MetaShape can import.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output XML file
        """
        import xml.etree.ElementTree as ET
        
        root = ET.Element('document')
        chunks = ET.SubElement(root, 'chunks')
        chunk = ET.SubElement(chunks, 'chunk')
        markers = ET.SubElement(chunk, 'markers')
        
        for i, gcp in enumerate(gcps):
            marker = ET.SubElement(markers, 'marker')
            marker.set('label', gcp.get('id', gcp.get('label', f'GCP_{i+1}')))
            marker.set('reference', 'true')
            
            # Position
            position = ET.SubElement(marker, 'position')
            lon = gcp.get('lon', gcp.get('longitude', 0.0))
            lat = gcp.get('lat', gcp.get('latitude', 0.0))
            z = gcp.get('z', gcp.get('elevation', gcp.get('altitude', 0.0)))
            position.set('x', str(lon))
            position.set('y', str(lat))
            position.set('z', str(z))
            
            # Accuracy
            accuracy = gcp.get('accuracy', gcp.get('rmse', 1.0))
            accuracy_elem = ET.SubElement(marker, 'accuracy')
            accuracy_elem.set('x', str(accuracy))
            accuracy_elem.set('y', str(accuracy))
            accuracy_elem.set('z', str(accuracy))
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)


class ArcGISExporter:
    """Export GCPs to ArcGIS Pro format."""
    
    @staticmethod
    def export_csv(gcps: List[Dict], output_path: str):
        """
        Export GCPs to CSV format for ArcGIS Pro.
        
        ArcGIS Pro can import CSV files with X, Y, Z columns.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output CSV file
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['ID', 'X', 'Y', 'Z', 'Accuracy', 'Description'])
            
            for i, gcp in enumerate(gcps):
                gcp_id = gcp.get('id', gcp.get('label', f'GCP_{i+1}'))
                lon = gcp.get('lon', gcp.get('longitude', 0.0))
                lat = gcp.get('lat', gcp.get('latitude', 0.0))
                z = gcp.get('z', gcp.get('elevation', gcp.get('altitude', 0.0)))
                accuracy = gcp.get('accuracy', gcp.get('rmse', 1.0))
                description = gcp.get('description', gcp.get('type', ''))
                
                writer.writerow([gcp_id, lon, lat, z, accuracy, description])
    
    @staticmethod
    def export_shapefile(gcps: List[Dict], output_path: str):
        """
        Export GCPs to Shapefile format for ArcGIS Pro.
        
        Requires geopandas and fiona.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output shapefile (without .shp extension)
        """
        try:
            import geopandas as gpd
            from shapely.geometry import Point
        except ImportError:
            raise ImportError("geopandas is required for shapefile export. Install with: pip install geopandas")
        
        # Create GeoDataFrame
        geometries = []
        attributes = []
        
        for i, gcp in enumerate(gcps):
            lon = gcp.get('lon', gcp.get('longitude', 0.0))
            lat = gcp.get('lat', gcp.get('latitude', 0.0))
            z = gcp.get('z', gcp.get('elevation', gcp.get('altitude', 0.0)))
            
            point = Point(lon, lat)
            geometries.append(point)
            
            attributes.append({
                'ID': gcp.get('id', gcp.get('label', f'GCP_{i+1}')),
                'Z': z,
                'Accuracy': gcp.get('accuracy', gcp.get('rmse', 1.0)),
                'Description': gcp.get('description', gcp.get('type', ''))
            })
        
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs='EPSG:4326')
        
        # Save to shapefile
        gdf.to_file(output_path, driver='ESRI Shapefile')
    
    @staticmethod
    def export_geojson(gcps: List[Dict], output_path: str):
        """
        Export GCPs to GeoJSON format for ArcGIS Pro.
        
        Args:
            gcps: List of GCP dictionaries
            output_path: Path to output GeoJSON file
        """
        try:
            import geopandas as gpd
            from shapely.geometry import Point
        except ImportError:
            raise ImportError("geopandas is required for GeoJSON export. Install with: pip install geopandas")
        
        # Create GeoDataFrame
        geometries = []
        attributes = []
        
        for i, gcp in enumerate(gcps):
            lon = gcp.get('lon', gcp.get('longitude', 0.0))
            lat = gcp.get('lat', gcp.get('latitude', 0.0))
            z = gcp.get('z', gcp.get('elevation', gcp.get('altitude', 0.0)))
            
            point = Point(lon, lat)
            geometries.append(point)
            
            attributes.append({
                'ID': gcp.get('id', gcp.get('label', f'GCP_{i+1}')),
                'Z': z,
                'Accuracy': gcp.get('accuracy', gcp.get('rmse', 1.0)),
                'Description': gcp.get('description', gcp.get('type', ''))
            })
        
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs='EPSG:4326')
        
        # Save to GeoJSON
        gdf.to_file(output_path, driver='GeoJSON')



