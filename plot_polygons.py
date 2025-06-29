import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon
from collections import defaultdict
import os

def load_annotations(file_path):
    """Load annotations from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_polygon_bounds(annotations):
    """Get the bounding box of all polygons."""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for annotation in annotations:
        points = annotation.get('points', [])
        for point in points:
            x, y = point['x'], point['y']
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
    
    return min_x, min_y, max_x, max_y

def create_grid_from_polygons(annotations, grid_resolution=1.0):
    """
    Create a 2D grid with polygon labels.
    
    Args:
        annotations: List of annotation objects
        grid_resolution: Resolution of the grid (lower = more detailed)
    
    Returns:
        grid: 2D numpy array with labels
        grid_info: Dictionary with grid metadata
    """
    # Get bounds
    min_x, min_y, max_x, max_y = get_polygon_bounds(annotations)
    
    # Add padding
    padding = 10
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding
    
    # Calculate grid dimensions
    width = int((max_x - min_x) / grid_resolution) + 1
    height = int((max_y - min_y) / grid_resolution) + 1
    
    # Initialize grid with background label
    grid = np.full((height, width), 'background', dtype=object)
    
    # Create label to color mapping
    label_colors = {}
    color_index = 0
    
    # Process each annotation
    for annotation in annotations:
        points = annotation.get('points', [])
        label = annotation.get('label', 'unlabeled')
        annotation_type = annotation.get('type', 'unknown')
        
        if not points:
            continue
        
        # Convert points to grid coordinates
        polygon_points = []
        for point in points:
            grid_x = int((point['x'] - min_x) / grid_resolution)
            grid_y = int((point['y'] - min_y) / grid_resolution)
            polygon_points.append([grid_x, grid_y])
        
        if len(polygon_points) < 3:
            continue
        
        # Fill polygon in grid using rasterization
        polygon_points = np.array(polygon_points)
        
        # Simple polygon filling using matplotlib's path
        from matplotlib.path import Path
        path = Path(polygon_points)
        
        # Create mesh grid for testing points
        x_coords = np.arange(width)
        y_coords = np.arange(height)
        x_mesh, y_mesh = np.meshgrid(x_coords, y_coords)
        points_to_test = np.column_stack((x_mesh.ravel(), y_mesh.ravel()))
        
        # Test which points are inside the polygon
        inside_mask = path.contains_points(points_to_test)
        inside_mask = inside_mask.reshape(height, width)
        
        # Update grid with label
        grid[inside_mask] = f"{annotation_type}:{label}"
        
        # Store color mapping
        if label not in label_colors:
            label_colors[label] = plt.cm.tab20(color_index % 20)
            color_index += 1
    
    grid_info = {
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
        'width': width,
        'height': height,
        'resolution': grid_resolution,
        'label_colors': label_colors
    }
    
    return grid, grid_info

def sample_grid_visible_shops(grid, grid_info, cx, cy, dir, fov, radius=50):
    """
    Sample visible shops from the grid based on a center point and direction.
    
    Args:
        grid: 2D numpy array with labels
        grid_info: Dictionary with grid metadata
        cx: Center x coordinate in real space
        cy: Center y coordinate in real space
        dir: Direction in degrees (0 = right, 90 = up, etc.)
        radius: Radius to sample around the center point
    
    Returns:
        List of visible shop labels
    """
    # Convert center coordinates to grid coordinates
    grid_x = int((cx - grid_info['min_x']) / grid_info['resolution'])
    grid_y = int((cy - grid_info['min_y']) / grid_info['resolution'])
    
    visible_shops = set()
    
    # Sample points in a circle around the center
    for angle in np.linspace(0, fov, num=360):
        for r in range(radius):
            x_offset = int(r * np.cos(angle + np.radians(dir)))
            y_offset = int(r * np.sin(angle + np.radians(dir)))
            
            sample_x = grid_x + x_offset
            sample_y = grid_y + y_offset
            
            if 0 <= sample_x < grid.shape[1] and 0 <= sample_y < grid.shape[0]:
                label = grid[sample_y, sample_x]
                if label.startswith('shop:'):
                    visible_shops.add(label)
    
    return list(visible_shops)

def plot_polygons_matplotlib(annotations, grid=None, grid_info=None, save_path=None):
    """
    Plot polygons using matplotlib with better visualization.
    
    Args:
        annotations: List of annotation objects
        grid: Optional grid array for background
        grid_info: Optional grid metadata
        save_path: Optional path to save the plot
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))
    
    # Get bounds for plotting
    min_x, min_y, max_x, max_y = get_polygon_bounds(annotations)
    
    # Create color map for different types and labels
    type_colors = {
        'polygon': 'blue',
        'corridor': 'red',
        'unknown': 'gray'
    }
    
    label_colors = {}
    color_index = 0
    
    # Plot each annotation
    for annotation in annotations:
        points = annotation.get('points', [])
        label = annotation.get('label', 'unlabeled')
        annotation_type = annotation.get('type', 'unknown')
        
        if not points or len(points) < 3:
            continue
        
        # Convert points to coordinate arrays
        x_coords = [point['x'] for point in points]
        y_coords = [point['y'] for point in points]
        
        # Get color for this label
        if label not in label_colors:
            if annotation_type in type_colors:
                base_color = type_colors[annotation_type]
            else:
                base_color = plt.cm.tab20(color_index % 20)
                color_index += 1
            label_colors[label] = base_color
        
        color = label_colors[label]
        
        # Create polygon patch
        polygon_coords = list(zip(x_coords, y_coords))
        polygon_patch = Polygon(polygon_coords, 
                              facecolor=color, 
                              edgecolor='black', 
                              alpha=0.6, 
                              linewidth=1)
        ax.add_patch(polygon_patch)
        
        # Add label text at centroid
        centroid_x = sum(x_coords) / len(x_coords)
        centroid_y = sum(y_coords) / len(y_coords)
        
        # Adjust text size based on polygon size
        text_size = min(12, max(6, len(label)))
        ax.text(centroid_x, centroid_y, label, 
               ha='center', va='center', 
               fontsize=8, 
               bbox=dict(boxstyle='round,pad=0.2', 
                        facecolor='white', 
                        alpha=0.8))
    
    # Set plot properties
    ax.set_xlim(min_x - 20, max_x + 20)
    ax.set_ylim(min_y - 20, max_y + 20)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Polygon Annotations Visualization')
    
    # Invert y-axis to match image coordinates
    ax.invert_yaxis()
    
    # Create legend
    legend_elements = []
    for label, color in label_colors.items():
        legend_elements.append(patches.Patch(color=color, label=label))
    
    # Split legend into multiple columns if too many items
    ncol = min(3, max(1, len(legend_elements) // 10))
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), ncol=ncol)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()
    
    return fig, ax

def print_grid_statistics(grid, grid_info):
    """Print statistics about the grid."""
    unique_labels = np.unique(grid)
    label_counts = {label: np.sum(grid == label) for label in unique_labels}
    
    print("\n=== Grid Statistics ===")
    print(f"Grid dimensions: {grid_info['width']} x {grid_info['height']}")
    print(f"Grid resolution: {grid_info['resolution']}")
    print(f"Coordinate bounds: ({grid_info['min_x']:.1f}, {grid_info['min_y']:.1f}) to ({grid_info['max_x']:.1f}, {grid_info['max_y']:.1f})")
    print(f"Total unique labels: {len(unique_labels)}")
    
    print("\nLabel distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / grid.size) * 100
        print(f"  {label}: {count} pixels ({percentage:.2f}%)")

def main():
    """Main function to process annotations and create visualizations."""
    
    # File paths
    corridor_file = "example/annotations.corridor.json"
    shop_file = "example/annotations.shop.json"
    
    # Check if files exist
    files_to_process = []
    if os.path.exists(corridor_file):
        files_to_process.append(("corridor", corridor_file))
    if os.path.exists(shop_file):
        files_to_process.append(("shop", shop_file))
    
    if not files_to_process:
        print("No annotation files found!")
        return
    
    # Process each file
    all_annotations = []
    for file_type, file_path in files_to_process:
        print(f"Loading {file_type} annotations from: {file_path}")
        annotations = load_annotations(file_path)
        
        # Add file type to annotations if not present
        for annotation in annotations:
            if 'type' not in annotation:
                annotation['type'] = file_type
        # Remove all annotations of type 'corridor'
        annotations = [a for a in annotations if a.get('type') != 'corridor']
        all_annotations.extend(annotations)
        print(f"Loaded {len(annotations)} {file_type} annotations")
    
    print(f"\nTotal annotations loaded: {len(all_annotations)}")
    
    # Create grid representation
    print("\nCreating 2D grid representation...")
    grid, grid_info = create_grid_from_polygons(all_annotations, grid_resolution=2.0)
    
    # Print grid statistics
    print_grid_statistics(grid, grid_info)
    
    # Create matplotlib visualization
    print("\nCreating matplotlib visualization...")
    fig, ax = plot_polygons_matplotlib(all_annotations, grid, grid_info, 
                                     save_path="polygon_visualization.png")
    
    # Store grid in memory for later use
    print(f"\nGrid with labels stored in memory:")
    print(f"Grid shape: {grid.shape}")
    print(f"Grid dtype: {grid.dtype}")
    print(f"Access grid with: grid[y, x] where y,x are grid coordinates")
    
    # Example of accessing grid data
    print(f"\nExample grid values:")
    sample_points = [(grid.shape[0]//4, grid.shape[1]//4), 
                     (grid.shape[0]//2, grid.shape[1]//2),
                     (3*grid.shape[0]//4, 3*grid.shape[1]//4)]
    
    for y, x in sample_points:
        if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
            real_x = grid_info['min_x'] + x * grid_info['resolution']
            real_y = grid_info['min_y'] + y * grid_info['resolution']
            print(f"  Grid[{y}, {x}] = '{grid[y, x]}' (real coords: {real_x:.1f}, {real_y:.1f})")
    
    return grid, grid_info, all_annotations

if __name__ == "__main__":
    # Run the main function and keep results in memory
    grid, grid_info, annotations = main()
    
    print(f"\nScript completed! Grid and annotations are available in memory.")
    print(f"Variables available:")
    print(f"  - grid: 2D numpy array with labels")
    print(f"  - grid_info: Dictionary with grid metadata")
    print(f"  - annotations: List of all annotation objects")
