import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Pose
from rclpy.qos import qos_profile_sensor_data
import math

class MockOakdNode(Node):
    def __init__(self):
        super().__init__('mock_oakd')
        self.publisher = self.create_publisher(Point, '/target_person_pose', 10)
        
        self.robot_pose = None
        self.person_pose = None
        
        # Subscribe directly to the dedicated model topics
        self.create_subscription(Pose, '/model/boombot/pose', self.robot_cb, qos_profile_sensor_data)
        self.create_subscription(Pose, '/model/person_cylinder/pose', self.person_cb, qos_profile_sensor_data)
            
        self.get_logger().info("Mock OAK-D Active. Listening to dedicated model poses...")

    def robot_cb(self, msg):
        self.robot_pose = msg
        self.compute_and_publish()

    def person_cb(self, msg):
        self.person_pose = msg
        self.compute_and_publish()

    def compute_and_publish(self):
        # Only calculate if we have seen both the robot and the cylinder
        if not self.robot_pose or not self.person_pose:
            return
            
        # 1. Get global differences
        dx = self.person_pose.position.x - self.robot_pose.position.x
        dy = self.person_pose.position.y - self.robot_pose.position.y
        
        # 2. Extract robot yaw from quaternion
        q = self.robot_pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        # 3. Apply 2D Rotation Matrix to convert to local camera frame
        local_z = dx * math.cos(yaw) + dy * math.sin(yaw)
        local_x = -dx * math.sin(yaw) + dy * math.cos(yaw)
        
        # Publish
        target_msg = Point()
        target_msg.x = local_x
        target_msg.y = 0.0
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