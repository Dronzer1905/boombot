import time
import serial
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SerialTransmitter(Node):
    def __init__(self):
        super().__init__('serial_transmitter')
        
        # Serial Port Configuration
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 115200
        
        # Initialize serial connection with ESP
        self.init_serial()
        
        # Create subscriber to listen to /cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.subscription  # prevent unused variable warning
        self.get_logger().info("Subscribed to /cmd_vel. Waiting for commands...")

    def init_serial(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f"Connected successfully to serial port: {self.serial_port}")
            time.sleep(2)  # Wait for ESP to reset upon serial connection
        except serial.SerialException as e:
            self.get_logger().error(f"Connection error: {e}")
            raise SystemExit

    def cmd_vel_callback(self, msg):
        vx = int(msg.linear.x)
        vy = int(msg.linear.y)
        wz = int(msg.angular.z)
        
        # Exact format from original script
        command = f"{vx} {vy} {wz}\n"
        
        try:
            self.ser.write(command.encode('utf-8'))
            self.get_logger().info(f"Sent Serial Command: {command.strip()}")
        except Exception as e:
            self.get_logger().error(f"Failed to send serial data: {e}")

    def send_stop_command(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            try:
                self.ser.write("0 0 0\n".encode('utf-8'))
                self.ser.close()
                self.get_logger().info("Sent stop command (0 0 0) and closed serial port.")
            except Exception as e:
                self.get_logger().error(f"Error closing serial port: {e}")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        serial_transmitter = SerialTransmitter()
        rclpy.spin(serial_transmitter)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
    finally:
        if 'serial_transmitter' in locals():
            serial_transmitter.send_stop_command()
            serial_transmitter.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()