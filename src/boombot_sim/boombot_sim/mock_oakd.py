import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseArray
import math

class MockOakdNode(Node):
    def __init__(self):
        super().__init__('mock_oakd')
        self.publisher = self.create_publisher(Point, '/target_person_pose', 10)
        
        # Subscribe to the ground truth poses bridged from Gazebo Harmonic
        self.subscription = self.create_subscription(
            PoseArray,
            '/gazebo/model_poses',
            self.pose_callback,
            10)
            
        self.get_logger().info("Mock OAK-D Active. Translating global poses to local camera frame...")

    def pose_callback(self, msg):
        robot_pose = None
        person_pose = None

        # Find our specific models in the Gazebo array
        for i, name in enumerate(msg.header.frame_id.split(',')): # Gazebo packs names in frame_id or we match by index
            # Note: In production ros_gz_bridge, parse the names appropriately based on your world
            if "boombot" in name:
                robot_pose = msg.poses[i]
            elif "person_cylinder" in name:
                person_pose = msg.poses[i]

        if robot_pose and person_pose:
            # 1. Get global differences
            dx = person_pose.position.x - robot_pose.position.x
            dy = person_pose.position.y - robot_pose.position.y
            
            # 2. Extract robot yaw from quaternion
            q = robot_pose.orientation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            
            # 3. Apply 2D Rotation Matrix to convert to local camera frame
            # Camera Z (depth) maps to Robot X (forward)
            # Camera X (lateral) maps to Robot Y (left/right)
            local_z = dx * math.cos(yaw) + dy * math.sin(yaw)
            local_x = -dx * math.sin(yaw) + dy * math.cos(yaw)
            
            # Publish
            target_msg = Point()
            target_msg.x = local_x
            target_msg.y = 0.0 # Height ignored for 2D ground control
            target_msg.z = local_z 
            
            self.publisher.publish(target_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MockOakdNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()