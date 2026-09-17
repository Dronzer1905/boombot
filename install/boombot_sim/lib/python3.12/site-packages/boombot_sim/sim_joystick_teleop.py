import sys
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import pygame

DEADZONE = 0.2

def get_proportional_value(axis_value, max_speed=1.0):
    """
    Calculates the proportional velocity based on joystick input and deadzone.
    Maps to physical units (m/s or rad/s) for Gazebo simulation.
    """
    if abs(axis_value) < DEADZONE:
        return 0.0
    sign = 1.0 if axis_value > 0 else -1.0
    magnitude = (abs(axis_value) - DEADZONE) / (1.0 - DEADZONE)
    return sign * magnitude * max_speed

class SimJoystickPublisher(Node):
    def __init__(self):
        super().__init__('sim_joystick_publisher')
        
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.last_command = ""
        self.init_joystick()

    def init_joystick(self):
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            self.get_logger().error("NO CONTROLLER FOUND")
            sys.exit()
            
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.get_logger().info(f"Connected : {self.joystick.get_name()}")

    def timer_callback(self):
        pygame.event.pump()
        
        raw_y = self.joystick.get_axis(1)   # left Y
        raw_x = self.joystick.get_axis(0)   # left X
        raw_rot = self.joystick.get_axis(3) # right thumbstick X/Y
        
        # Set realistic simulation maximums: 1.0 m/s linear, 2.0 rad/s angular
        vx = get_proportional_value(-raw_y, max_speed=1.0) 
        vy = get_proportional_value(raw_x, max_speed=1.0)
        wz = get_proportional_value(raw_rot, max_speed=2.0)
        
        command = f"{vx:.2f} {vy:.2f} {wz:.2f}\n"
        
        if command != self.last_command:
            msg = Twist()
            msg.linear.x = vx
            msg.linear.y = vy
            msg.angular.z = wz
            
            self.publisher_.publish(msg)
            self.get_logger().info(f"Published Simulation Twist: {command.strip()}")
            self.last_command = command

def main(args=None):
    rclpy.init(args=args)
    
    try:
        joystick_publisher = SimJoystickPublisher()
        rclpy.spin(joystick_publisher)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pygame.quit()
        if 'joystick_publisher' in locals():
            joystick_publisher.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()