import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    pkg_share = get_package_share_directory('boombot_sim')
    urdf_file = os.path.join(pkg_share, 'urdf', 'boombot.urdf')

    return LaunchDescription([
        # 1. Start Gazebo
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', 'empty.sdf'], 
            output='screen'
        ),
        
        # 2. Spawn the Robot
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-name', 'boombot', '-file', urdf_file],
            output='screen'
        ),
        
        # 3. Spawn the Target Cylinder
        ExecuteProcess(
            cmd=['gz', 'service', '-s', '/world/empty/create', '--reqtype', 'gz.msgs.EntityFactory', 
                 '--reptype', 'gz.msgs.Boolean', '--timeout', '1000', '--req', 
                 'sdf: \'<sdf version="1.6"><model name="person_cylinder"><pose>2 0 0.5 0 0 0</pose><link name="link"><visual name="visual"><geometry><cylinder><radius>0.3</radius><length>1.0</length></cylinder></geometry></visual></link></model></sdf>\''],
            output='screen'
        ),
        
        # 4. Bridge Odometry (Robot) and TF Array (Cylinder)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/world/empty/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
            ],
            remappings=[
                ('/world/empty/pose/info', '/gazebo/model_poses')
            ],
            output='screen'
        ),
        
        # 5. Mock OAK-D Node
        Node(
            package='boombot_sim',
            executable='mock_oakd',
            output='screen'
        )
    ])