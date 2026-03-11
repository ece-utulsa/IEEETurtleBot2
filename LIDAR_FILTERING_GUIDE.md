# ROS2 LIDAR Laser Scan Filtering Guide - Angular Bounds Filtering

## Research Summary
This guide covers the best practices for filtering LIDAR laser scans in ROS2 to exclude specific angular ranges, with focus on excluding areas like 170-190 degrees (e.g., behind the robot where the back wall might obscure measurements).

---

## 1. The laser_filters Package

The **laser_filters** package (`ros-perception/laser_filters`) is the standard ROS2 library for filtering 2D planar laser scanner data (sensor_msgs/LaserScan type).

### Key Information:
- **GitHub**: https://github.com/ros-perception/laser_filters (ros2 branch)
- **Current Version**: 2.0.9 (as of July 2025)
- **Build Type**: AMENT_CMAKE
- **Maintained**: Yes (Active)
- **Available in**: ROS 2 Humble, Rolling, and other distributions

### Available Filters:
The package provides 15+ specialized filters including:
- `LaserScanAngularBoundsFilter` - **Removes points OUTSIDE angular range**
- `LaserScanAngularBoundsFilterInPlace` - **Removes points INSIDE angular range**
- `LaserScanRangeFilter` - Filters by distance
- `LaserScanIntensityFilter` - Filters by intensity
- `ScanShadowsFilter` - Removes shadow artifacts
- `LaserScanSpeckleFilter` - Removes noise points
- `LaserScanMedianSpatialFilter` - Smoothing filter
- `LaserScanBoxFilter` - Cartesian box filtering
- `LaserScanSectorFilter` - Sector-based filtering
- `LaserScanPolygonFilter` - Polygon-based filtering

---

## 2. Angular Filtering Options Compared

### Option A: LaserScanAngularBoundsFilter (KEEP range, discard outside)
**Use when**: You want to keep only a specific angular range (e.g., front-facing 0-90° range)
**Output**: Shrunk scan with only the desired angular range
**Parameters**:
- `lower_angle` (radians): Minimum angle to keep
- `upper_angle` (radians): Maximum angle to keep

**Example**: Keep only front 180°
```yaml
lower_angle: -1.57   # -90°
upper_angle: 1.57    # +90°
```

### Option B: LaserScanAngularBoundsFilterInPlace (DISCARD range, keep rest)
**Use when**: You want to discard a specific angular range but keep surrounding scans
**Output**: Full-sized scan with removed range replaced by NaN or range_max+1
**Parameters**:
- `lower_angle` (radians): Start of angular range to remove
- `upper_angle` (radians): End of angular range to remove
- `replace_with_nan` (bool): Use NaN instead of range_max+1 (default: false)

**Example**: Remove rear 40° (170-190° or π-angle to π+angle)
```yaml
lower_angle: 2.966   # 170° in radians
upper_angle: 3.316   # 190° in radians
replace_with_nan: true  # Better for SLAM algorithms
```

### Option C: LaserScanSectorFilter (Circle sector filtering)
**Use when**: You want cylindrical/circular region filtering (good for robot footprint)
**Output**: Points inside/outside specified circle sector removed
**Parameters**:
- `angle_min` (radians): Sector angle minimum
- `angle_max` (radians): Sector angle maximum
- `range_min` (meters): Minimum radius
- `range_max` (meters): Maximum radius
- `clear_inside` (bool): Remove points inside (true) or outside (false)
- `invert` (bool): Invert the logic

---

## 3. Exact Angle Conversion Reference

For your 170-190° exclusion use case:

```
Degrees to Radians Formula: radians = degrees × π / 180

170° = 170 × π / 180 = 2.9671 rad
190° = 190 × π / 180 = 3.3161 rad

For symmetrical rear exclusion (center at 180° ±α):
180° center = π (3.14159 rad)
±10° around 180° = 170-190°

Exact values:
170° = -2.9671 rad (from front facing 0)
190° = -3.3161 rad (from front facing 0)

OR using 0-360° convention:
170° = 2.9671 rad
180° = 3.1416 rad
190° = 3.3161 rad
```

**For your angles (170-190°)**:
```yaml
# Option 1: Using positive angles (most common)
lower_angle: 2.9671  # 170°
upper_angle: 3.3161  # 190°

# Option 2: For symmetric around 180°
lower_angle: 2.9496  # 169°
upper_angle: 3.3336  # 191°
```

---

## 4. Configuration Examples

### Example 1: Basic Angular In-Place Filter (Exclude 170-190°)

**File**: `turtlebot3_angular_filter.yaml`
```yaml
scan_to_scan_filter_chain:
  ros__parameters:
    filter1:
      name: rear_angle_filter
      type: laser_filters/LaserScanAngularBoundsFilterInPlace
      params:
        lower_angle: 2.9671  # 170 degrees
        upper_angle: 3.3161  # 190 degrees
        replace_with_nan: true  # Use NaN for better SLAM compatibility
```

### Example 2: Multiple Filters with Angular + Range Filtering

**File**: `turtlebot3_combined_filters.yaml`
```yaml
scan_to_scan_filter_chain:
  ros__parameters:
    # First filter: Remove rear angular range
    filter1:
      name: rear_angle_filter
      type: laser_filters/LaserScanAngularBoundsFilterInPlace
      params:
        lower_angle: 2.9671  # 170°
        upper_angle: 3.3161  # 190°
        replace_with_nan: true

    # Second filter: Remove close points (noise)
    filter2:
      name: range_filter
      type: laser_filters/LaserScanRangeFilter
      params:
        lower_threshold: 0.12   # 12 cm minimum range
        upper_threshold: 3.5    # 3.5 m maximum range
        
    # Third filter: Remove shadow artifacts
    filter3:
      name: shadow_filter
      type: laser_filters/ScanShadowsFilter
      params:
        min_angle: 10.
        max_angle: 170.
        neighbors: 20
        window: 0
```

### Example 3: Keep Only Front Hemisphere (0-90° + 270-360°)

**File**: `turtlebot3_front_only_filter.yaml`
```yaml
scan_to_scan_filter_chain:
  ros__parameters:
    filter1:
      name: front_hemisphere_filter
      type: laser_filters/LaserScanAngularBoundsFilter
      params:
        lower_angle: -1.5708  # -90°
        upper_angle: 1.5708   # +90°
```

### Example 4: Exclude Multiple Angular Regions (Cartesian Approach)

**File**: `turtlebot3_box_filter.yaml`
```yaml
# Alternative: Using box filter for cartesian bounds
# Useful for excluding behind robot based on geometry
scan_to_scan_filter_chain:
  ros__parameters:
    filter1:
      name: rear_zone_box_filter
      type: laser_filters/LaserScanBoxFilter
      params:
        box_frame: base_link
        min_x: -0.2   # Box bounds relative to robot
        max_x: 0.2
        min_y: -0.5
        max_y: 0.5
        min_z: -1.0
        max_z: 1.0
```

---

## 5. Integration with Cartographer SLAM - Step by Step

### Step 1: Create Filter Configuration YAML

Create `src/turtlebot3/turtlebot3_cartographer/config/scan_filter.yaml`:

```yaml
# Laser scan filter configuration for Cartographer
scan_to_scan_filter_chain:
  ros__parameters:
    filter1:
      name: angular_bounds_filter
      type: laser_filters/LaserScanAngularBoundsFilterInPlace
      params:
        lower_angle: 2.9671  # 170°
        upper_angle: 3.3161  # 190°
        replace_with_nan: true

    filter2:
      name: range_filter
      type: laser_filters/LaserScanRangeFilter
      params:
        lower_threshold: 0.12
        upper_threshold: 3.5
```

### Step 2: Create Filter Chain Launch File

Create `src/turtlebot3/turtlebot3_cartographer/launch/scan_filter.launch.py`:

```python
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    laser_filter_config = PathJoinSubstitution([
        get_package_share_directory('turtlebot3_cartographer'),
        'config',
        'scan_filter.yaml'
    ])

    filter_chain_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='scan_filter_chain',
        parameters=[laser_filter_config],
        remappings=[
            ('scan', '/scan'),                      # Input from lidar driver
            ('scan_filtered', '/scan_filtered')      # Output to cartographer
        ],
        output='screen'
    )

    return LaunchDescription([filter_chain_node])
```

### Step 3: Create Main Cartographer Launch File with Filter Integration

Create/modify `src/turtlebot3/turtlebot3_cartographer/launch/cartographer_with_filter.launch.py`:

```python
from launch import LaunchDescription, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Define package directory
    turtlebot3_cartographer_dir = get_package_share_directory('turtlebot3_cartographer')
    cartographer_config_dir = PathJoinSubstitution([
        turtlebot3_cartographer_dir, 'config'
    ])
    
    # Scan filter launch file
    scan_filter_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            turtlebot3_cartographer_dir, 'launch', 'scan_filter.launch.py'
        ]))
    )

    # Cartographer node - configured to subscribe to filtered scans
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,
        }],
        remappings=[
            ('scan', '/scan_filtered'),  # KEY: Subscribe to FILTERED scans
        ],
        arguments=[
            '-configuration_directory', cartographer_config_dir,
            '-configuration_basename', 'turtlebot3_lds_2d.lua',
        ],
    )

    # RViz for visualization
    rviz_config = PathJoinSubstitution([
        cartographer_config_dir, 'cartographer.rviz'
    ])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([
        scan_filter_launch,    # Start filter chain FIRST
        cartographer_node,     # Cartographer reads from filtered scans
        rviz_node,
    ])
```

### Step 4: Update Package Dependencies

Add to `src/turtlebot3/turtlebot3_cartographer/package.xml`:

```xml
<exec_depend>laser_filters</exec_depend>
```

### Step 5: Launch Command

```bash
ros2 launch turtlebot3_cartographer cartographer_with_filter.launch.py
```

---

## 6. Data Flow Diagram

```
LIDAR Driver
    ↓
  [/scan] topic (raw)
    ↓
┌─────────────────────────────────────┐
│  laser_filters Filter Chain Node    │ ← scan_to_scan_filter_chain
│  - Angular bounds removal           │
│  - Range filtering                  │
│  - Shadow removal                   │
└─────────────────────────────────────┘
    ↓
  [/scan_filtered] topic (processed)
    ↓
Cartographer SLAM
    ↓
  [/map] output
```

---

## 7. Alternative Methods

### Alternative 1: Built-in Cartographer SLAM Filtering

Cartographer has built-in range filtering:

**In `turtlebot3_lds_2d.lua`** (already shown in your workspace):
```lua
TRAJECTORY_BUILDER_2D.min_range = 0.12
TRAJECTORY_BUILDER_2D.max_range = 3.5
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.
```

**Limitations**: 
- Only range-based, not angular
- Limited filtering options
- Can't exclude specific directions

**Solution**: Combine Cartographer internal filtering with laser_filters pre-processing

### Alternative 2: Custom ROS2 Node

For advanced filtering logic, create a custom node using `rclpy`:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
import math


class LidarFilterNode(Node):
    def __init__(self):
        super().__init__('lidar_filter_node')
        
        # Exclusion angles in degrees
        self.exclude_start = 170.0  # degrees
        self.exclude_end = 190.0    # degrees
        
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.publisher = self.create_publisher(
            LaserScan, '/scan_filtered', 10)

    def scan_callback(self, msg: LaserScan):
        filtered_msg = LaserScan()
        filtered_msg = msg  # Copy all fields
        
        # Convert exclude angles to radians
        exclude_start_rad = math.radians(self.exclude_start)
        exclude_end_rad = math.radians(self.exclude_end)
        
        # Filter ranges
        current_angle = msg.angle_min
        for i, range_val in enumerate(msg.ranges):
            if exclude_start_rad < current_angle < exclude_end_rad:
                filtered_msg.ranges[i] = float('nan')
            current_angle += msg.angle_increment
        
        self.publisher.publish(filtered_msg)


def main():
    rclpy.init()
    node = LidarFilterNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**Advantages**: 
- Full control over filtering logic
- Can implement complex algorithms
- Easy to debug

**Disadvantages**: 
- More code to maintain
- Slower than compiled C++ filters
- Dependency management

### Alternative 3: Use Sector Filter for Geometry-Based Exclusion

For excluding areas based on robot geometry (like back wall):

```yaml
scan_to_scan_filter_chain:
  ros__parameters:
    filter1:
      name: rear_sector_filter
      type: laser_filters/LaserScanSectorFilter
      params:
        angle_min: 2.5  # ~143°
        angle_max: 3.67 # ~210°
        range_min: 0.0
        range_max: 0.5  # Only near the robot
        clear_inside: false  # Keep points outside sector
        invert: false
```

---

## 8. Recommended Configuration for Your IEEE Robot

For a TurtleBot3-based IEEE robot with a back wall:

**`scan_filter.yaml`:**
```yaml
scan_to_scan_filter_chain:
  ros__parameters:
    # Angular filter: Exclude rear 180° ± 10°
    filter1:
      name: rear_angle_filter
      type: laser_filters/LaserScanAngularBoundsFilterInPlace
      params:
        lower_angle: 2.9671    # 170°
        upper_angle: 3.3161    # 190°
        replace_with_nan: true

    # Range filter: Minimum range to avoid close noise
    filter2:
      name: min_range_filter
      type: laser_filters/LaserScanRangeFilter
      params:
        lower_threshold: 0.10
        upper_threshold: 4.0

    # Median filter: Smooth out noise
    filter3:
      name: median_filter
      type: laser_filters/LaserScanSpeckleFilter
      params:
        filter_type: median
        max_distance: 0.05
        window_size: 5
```

**Rationale**:
- Replace-with-NaN prevents "ghost" walls in SLAM
- Multiple filters handle different noise sources
- Angles: 170-190° excludes rear, matches LaserScan convention
- TurtleBot3 specific: 0.10m minimum (low height, close readings problematic)

---

## 9. Testing and Debugging

### Visualize Filtered vs. Raw Scans

```bash
# Terminal 1: Start filter chain
ros2 launch turtlebot3_cartographer scan_filter.launch.py

# Terminal 2: View both scans in RViz
rviz2

# In RViz:
# Add LaserScan display for '/scan' (raw)
# Add LaserScan display for '/scan_filtered' (filtered)
# Color them differently to compare
```

### Check Filter Parameters at Runtime

```bash
# List all filter parameters
ros2 param list /scan_filter_chain

# Get specific parameter
ros2 param get /scan_filter_chain filter1.lower_angle

# Dynamically modify parameter (if reconfigurable)
ros2 param set /scan_filter_chain filter1.lower_angle 2.9671
```

### Monitor Filter Performance

```bash
# Check node status
ros2 node list | grep filter

# Check topic statistics
ros2 topic hz /scan_filtered
ros2 topic hz /scan
```

---

## 10. Common Issues and Solutions

### Issue 1: Filter removes too many points
**Solution**: Check angle calculations. Verify 180° = π radians (3.14159)

### Issue 2: Cartographer not receiving filtered scans
**Solution**: Check remappings in launch file. Ensure `/scan` → `/scan_filtered` mapping is correct

### Issue 3: NaN values causing issues in SLAM
**Solution**: Set `replace_with_nan: false` to use `range_max + 1` instead (older compatibility)

### Issue 4: Filter chain node crashes
**Solution**: Verify `lower_angle < upper_angle`, both in radians, within range [-π, π]

### Issue 5: Performance degradation
**Solution**: Use compiled filters (laser_filters) not Python nodes. Reduce filter chain complexity.

---

## 11. References and Documentation

- **laser_filters GitHub**: https://github.com/ros-perception/laser_filters/tree/ros2
- **ROS2 laser_filters API**: https://docs.ros.org/en/rolling/p/laser_filters/
- **Cartographer ROS**: https://github.com/ros2/cartographer_ros
- **sensor_msgs/LaserScan**: http://docs.ros.org/en/api/sensor_msgs/html/msg/LaserScan.html
- **Filter Chain Plugins**: https://github.com/ros-perception/filters

---

## 12. Quick Reference: Angle Conversion Table

| Degrees | Radians | Use Case |
|---------|---------|----------|
| 0° | 0.0 | Front (straight ahead) |
| ±45° | ±0.7854 | Front corners |
| ±90° | ±1.5708 | Left/right |
| 170° | 2.9671 | Rear-left edge |
| 180° | 3.1416 | Directly behind |
| 190° | 3.3161 | Rear-right edge |
| ±170° to ±190° | 2.9671-3.3161 | Rear exclusion zone |

---

## Summary

For your IEEE robot excluding 170-190° (the rear wall):

**Best Practice**: Use `LaserScanAngularBoundsFilterInPlace` with:
```yaml
lower_angle: 2.9671
upper_angle: 3.3161
replace_with_nan: true
```

**Why this approach**:
1. ✅ Well-tested, mature solution (laser_filters package)
2. ✅ Compiled C++ for performance
3. ✅ Easy integration with Cartographer
4. ✅ Handles both angular and range filtering
5. ✅ NaN values prevent SLAM artifacts
6. ✅ Industry standard method for ROS2 robots

**Integration complexity**: Low (3 files: YAML config, filter launch, main launch)

This is the exact same approach used by TurtleBot3, Clearpath robots, and most ROS2 SLAM projects.
