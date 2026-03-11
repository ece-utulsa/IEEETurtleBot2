"""
Cartographer SLAM with Integrated LIDAR Filtering
Purpose: Launch complete SLAM pipeline with preprocessed LIDAR scans

Data Pipeline:
    LIDAR Driver → Scan Filter Chain → Cartographer SLAM → Map Output
                        ↓
                  (Remove rear scans)
                        ↓
                    RViz Visualization

This launch file:
1. Starts the laser_filters scan_to_scan_filter_chain node first
2. Configures Cartographer to subscribe to /scan_filtered (not /scan)
3. Launches RViz for visualization and monitoring
"""

from launch import LaunchDescription, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Generate complete Cartographer SLAM with integrated filtering.
    
    Returns:
        LaunchDescription with filter chain, Cartographer, and visualization
    """
    
    # ===== PACKAGE PATHS =====
    turtlebot3_cartographer_dir = get_package_share_directory('turtlebot3_cartographer')
    
    cartographer_config_dir = PathJoinSubstitution([
        turtlebot3_cartographer_dir, 'config'
    ])
    
    # ===== CONFIGURATION FILES =====
    # Cartographer SLAM configuration (trajectory builder setup)
    cartographer_config_file = 'turtlebot3_lds_2d.lua'
    
    # RViz visualization configuration
    rviz_config_file = PathJoinSubstitution([
        cartographer_config_dir, 'cartographer.rviz'
    ])
    
    # ===== NODES =====
    
    # Node 1: LIDAR Scan Filter Chain
    # MUST run BEFORE Cartographer to ensure filtered scans are available
    # Remaps: Raw /scan → processed /scan_filtered
    scan_filter_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            turtlebot3_cartographer_dir, 'launch', 'scan_filter.launch.py'
        ])),
        launch_arguments={}.items()
    )

    # Node 2: Cartographer SLAM Node
    # Core SLAM engine - processes sensor data to create map and localization
    # Key remapping: subscribes to /scan_filtered (filtered data)
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,  # Set to True if using bag files with timestamps
        }],
        remappings=[
            # CRITICAL: Subscribe to FILTERED scans, not raw /scan
            # This is what excludes the rear wall reflections
            ('scan', '/scan_filtered'),
        ],
        arguments=[
            '-configuration_directory', cartographer_config_dir,
            '-configuration_basename', cartographer_config_file,
        ],
    )

    # Node 3: Cartographer State Publisher
    # Publishes the map↔odom transform and trajectory markers
    cartographer_occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='log',
        parameters=[{
            'use_sim_time': False,
        }],
    )

    # Node 4: RViz for Visualization
    # Displays:
    # - /map (occupancy grid)
    # - /cartographer_state (trajectory and submaps)
    # - /scan_filtered (for debugging)
    # - /tf frames
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
    )

    # ===== COMPOSE LAUNCH DESCRIPTION =====
    return LaunchDescription([
        # START FILTER CHAIN FIRST (essential!)
        scan_filter_launch,
        
        # Start Cartographer SLAM
        cartographer_node,
        cartographer_occupancy_grid_node,
        
        # Start visualization
        rviz_node,
    ])
