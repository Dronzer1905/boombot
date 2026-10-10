import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from tf2_msgs.msg import TFMessage
from rclpy.qos import qos_profile_sensor_data
import math

class MockOakdNode(Node):
    def __init__(self):
        super().__init__('mock_oakd')
        self.publisher = self.create_publisher(Point, '/target_person_pose', 10)
        
        # Listen to the bridged poses
        self.create_subscription(TFMessage, '/gazebo/model_poses', self.tf_cb, qos_profile_sensor_data)
        self.get_logger().info("Mock OAK-D Active. Using mathematical heuristics to bypass blank names...")

    def tf_cb(self, msg):
        # Safety check to ensure the array has loaded our wheels and cylinder
        if len(msg.transforms) < 8:
            return
            
        person_pos = None
        
        # 1. Find the Cylinder (It is the object floating at z=0.5)
        for t in msg.transforms:
            if t.transform.translation.z > 0.2:
                person_pos = t.transform.translation
                break
                
        if not person_pos:
            return

        # 2. Extract the 4 wheels based on your exact array layout
        # Indices 4 & 5 are back wheels, Indices 6 & 7 are front wheels
        w1 = msg.transforms[4].transform.translation
        w2 = msg.transforms[5].transform.translation
        w3 = msg.transforms[6].transform.translation
        w4 = msg.transforms[7].transform.translation
        
        # 3. Calculate exact robot center (average of all 4 wheels)
        robot_x = (w1.x + w2.x + w3.x + w4.x) / 4.0
        robot_y = (w1.y + w2.y + w3.y + w4.y) / 4.0
        
        # 4. Calculate exact robot Yaw (vector from back wheels to front wheels)
        front_x = (w3.x + w4.x) / 2.0
        front_y = (w3.y + w4.y) / 2.0
        back_x = (w1.x + w2.x) / 2.0
        back_y = (w1.y + w2.y) / 2.0
        
        robot_yaw = math.atan2(front_y - back_y, front_x - back_x)
        
        # 5. Apply 2D Rotation to shift the target into the robot's local perspective
        dx = person_pos.x - robot_x
        dy = person_pos.y - robot_y
        
        local_z = dx * math.cos(robot_yaw) + dy * math.sin(robot_yaw)
        local_x = -dx * math.sin(robot_yaw) + dy * math.cos(robot_yaw)
        
        # 6. Map to standard ROS frame expectations (X = Forward, Y = Lateral)
        target_msg = Point()
        target_msg.x = local_z  # Forward distance
        target_msg.y = local_x  # Lateral distance
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