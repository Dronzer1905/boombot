from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Perception: Boot the OAK-D camera and publish /target_person_pose
        Node(
            package='perception',
            executable='oakd_tracker_node',
            name='tracker_node',
            output='screen'
        ),
        
        # 2. Control: Read the pose and calculate /cmd_vel kinematics
        Node(
            package='boombot_sim',
            executable='lqr_node',
            name='lqr_node',
            output='screen'
        ),
        
        # 3. Actuation: Bridge /cmd_vel down to the physical motor controllers
        Node(
            package='boombot_teleop',
            executable='serial_send',
            name='serial_transmitter',
            output='screen'
        )
    ])