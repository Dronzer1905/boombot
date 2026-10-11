import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt
import math
import time
import os

class ResultsPlotter(Node):
    def __init__(self):
        super().__init__('results_plotter')
        
        # Data storage arrays
        self.start_time = time.time()
        
        self.vel_times = []
        self.vx = []
        self.vy = []
        self.wz = []
        
        self.pose_times = []
        self.px = []
        self.py = []
        self.ptheta = []

        # Subscriptions
        self.create_subscription(Twist, '/cmd_vel', self.vel_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        
        self.get_logger().info("Recording data... Let the robot drive, then press Ctrl+C to generate graphs!")

    def vel_cb(self, msg):
        self.vel_times.append(time.time() - self.start_time)
        self.vx.append(msg.linear.x)
        self.vy.append(msg.linear.y)
        self.wz.append(msg.angular.z)

    def odom_cb(self, msg):
        self.pose_times.append(time.time() - self.start_time)
        self.px.append(msg.pose.pose.position.x)
        self.py.append(msg.pose.pose.position.y)
        
        # Convert Quaternion to Yaw Angle
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        self.ptheta.append(yaw)

    def plot_graphs(self):
        self.get_logger().info("Generating and saving graphs...")
        
        plt.figure(figsize=(14, 10))
        
        # 1. Velocities vs Time
        plt.subplot(2, 2, 1)
        plt.plot(self.vel_times, self.vx, label='Forward Vel (vx)', linewidth=2)
        plt.plot(self.vel_times, self.vy, label='Lateral Vel (vy)', linewidth=2)
        plt.plot(self.vel_times, self.wz, label='Angular Vel (wz)', linewidth=2, linestyle='--')
        plt.title('LQR Command Velocities vs. Time')
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s or rad/s)')
        plt.grid(True)
        plt.legend()
        
        # 2. Pose vs Time
        plt.subplot(2, 2, 2)
        plt.plot(self.pose_times, self.px, label='X Position (m)', linewidth=2)
        plt.plot(self.pose_times, self.py, label='Y Position (m)', linewidth=2)
        plt.plot(self.pose_times, self.ptheta, label='Yaw Angle (rad)', linewidth=2, linestyle='--')
        plt.title('Robot Pose vs. Time')
        plt.xlabel('Time (s)')
        plt.ylabel('Coordinate / Angle')
        plt.grid(True)
        plt.legend()

        # 3. 2D Top-Down Trajectory
        plt.subplot(2, 1, 2)
        plt.plot(self.px, self.py, 'b-', label='Robot Path', linewidth=2)
        if len(self.px) > 0:
            plt.plot(self.px[0], self.py[0], 'go', markersize=8, label='Start Point')
            plt.plot(self.px[-1], self.py[-1], 'ro', markersize=8, label='End Point')
        plt.title('2D Holonomic Trajectory (X vs Y)')
        plt.xlabel('X Distance (m)')
        plt.ylabel('Y Distance (m)')
        plt.axis('equal') # Keeps the grid perfectly square so circles don't look like ovals
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        
        # Save to the home directory for easy access
        save_path = os.path.expanduser('~/boombot_lqr_results.png')
        plt.savefig(save_path)
        self.get_logger().info(f"Graph successfully saved to: {save_path}")
        
        plt.show()

def main(args=None):
    rclpy.init(args=args)
    node = ResultsPlotter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Catch the Ctrl+C to stop spinning and render the plots
        pass
    finally:
        node.plot_graphs()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()