"""
Laser Scan Filter Chain Launch File
Purpose: Initialize the laser_filters scan_to_scan_filter_chain node
         to preprocess LIDAR scans before sending to Cartographer SLAM

This node:
1. Subscribes to raw /scan topic from LIDAR driver
2. Applies configured filters (angular bounds, range, speckle)
3. Publishes filtered scans to /scan_filtered topic

Topic Mapping:
  Input:  /scan (raw LIDAR data)
  Output: /scan_filtered (processed data for Cartographer)
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Generate launch description for laser filter chain node.
    
    Returns:
        LaunchDescription with configured filter chain node
    """
    
    # Get the path to the turtlebot3_cartographer package
    turtlebot3_cartographer_dir = get_package_share_directory('turtlebot3_cartographer')
    
    # Construct path to scan_filter.yaml configuration file
    scan_filter_config = PathJoinSubstitution([
        turtlebot3_cartographer_dir,
        'config',
        'scan_filter.yaml'
    ])

    # Create the filter chain node
    # executable: scan_to_scan_filter_chain - standard filterchain processor
    # It reads YAML config and dynamically loads specified filter plugins
    scan_filter_chain = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='scan_filter_chain',
        namespace='',
        output='screen',
        parameters=[scan_filter_config],
        remappings=[
            # Input: Raw scans from LIDAR driver
            ('scan', '/scan'),
            # Output: Filtered scans for Cartographer SLAM
            ('scan_filtered', '/scan_filtered')
        ]
    )

    return LaunchDescription([
        scan_filter_chain
    ])
