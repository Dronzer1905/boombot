import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from tf2_msgs.msg import TFMessage
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
import math

class MockOakdNode(Node):
    def __init__(self):
        super().__init__('mock_oakd')
        self.publisher = self.create_publisher(Point, '/target_person_pose', 10)
        
        self.robot_x = None
        self.robot_y = None
        self.robot_yaw = None
        self.person_pos = None
        
        # Subscribe to Odometry for the Robot's exact pose
        self.create_subscription(Odometry, '/odom', self.odom_cb, qos_profile_sensor_data)
        # Subscribe to TFMessage to spot the Cylinder
        self.create_subscription(TFMessage, '/gazebo/model_poses', self.tf_cb, qos_profile_sensor_data)
        
        self.get_logger().info("Mock OAK-D Active. Using Odometry for robot, TF for cylinder...")

    def odom_cb(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        
        # Extract Yaw
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.compute_and_publish()

    def tf_cb(self, msg):
        # Scan array for the floating cylinder
        for t in msg.transforms:
            if t.transform.translation.z > 0.2:
                self.person_pos = t.transform.translation
                break
        self.compute_and_publish()

    def compute_and_publish(self):
        if self.robot_x is None or self.person_pos is None:
            return
            
        dx = self.person_pos.x - self.robot_x
        dy = self.person_pos.y - self.robot_y
        
        local_z = dx * math.cos(self.robot_yaw) + dy * math.sin(self.robot_yaw)
        local_x = -dx * math.sin(self.robot_yaw) + dy * math.cos(self.robot_yaw)
        
        target_msg = Point()
        target_msg.x = local_z  # Forward error
        target_msg.y = local_x  # Lateral error
        target_msg.z = 0.0 
        
        self.publisher.publish(target_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MockOakdNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()