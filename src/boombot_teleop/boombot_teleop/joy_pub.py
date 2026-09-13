import sys
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import pygame

DEADZONE = 0.2

def get_proportional_value(axis_value):
    """
    Calculates the proportional velocity based on joystick input and deadzone.
    Maps to -255 to 255 range.
    """
    if abs(axis_value) < DEADZONE:
        return 0
    sign = 1 if axis_value > 0 else -1
    magnitude = (abs(axis_value) - DEADZONE) / (1.0 - DEADZONE)
    return int(sign * magnitude * 255)

class JoystickPublisher(Node):
    def __init__(self):
        super().__init__('joystick_publisher')
        
        # Create publisher for velocity commands on /cmd_vel
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Timer running at 20Hz (0.05s interval, matching original sleep duration)
        self.timer = self.create_timer(0.05, self.timer_callback)
        
        # Track last command to avoid spamming unchanged data
        self.last_command = ""
        
        # Initialize Pygame and Joystick input
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
        raw_rot = self.joystick.get_axis(3) # right Y
        
        vx = get_proportional_value(-raw_y) 
        vy = get_proportional_value(raw_x)
        wz = get_proportional_value(raw_rot)
        
        command = f"{vx} {vy} {wz}\n"
        
        # Only publish when command changes (identical to original condition)
        if command != self.last_command:
            msg = Twist()
            msg.linear.x = float(vx)
            msg.linear.y = float(vy)
            msg.angular.z = float(wz)
            
            self.publisher_.publish(msg)
            self.get_logger().info(f"Published Command: {command.strip()}")
            self.last_command = command

def main(args=None):
    rclpy.init(args=args)
    
    try:
        joystick_publisher = JoystickPublisher()
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