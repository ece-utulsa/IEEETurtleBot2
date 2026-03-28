#!/bin/bash

sleep 30

export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-02
export ROS_LOCALHOST_ONLY=0
export ROS_DISTRO=humble

source /opt/ros/humble/setup.bash
source /home/robotics/desktop_ws/IEEETurtleBot2/install/setup.bash

(
	cd /home/robotics/pi_ws
	ros2 launch turtlebot3_bringup robot.launch.py
) &

sleep 20

cd /home/robotics/desktop_ws/IEEETurtleBot2
ros2 run test_auto ballauto
