import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point
import numpy as np
import scipy.linalg

class LQR(Node):
    def __init__(self):
        super().__init__('lqr')
        self.publisher= self.create_publisher(Twist,'/cmd_vel',10)
        self.subscriber=self.create_subscription(Point,'/target_person_pose',self.pose_callback,10)

        #lqr constants
        self.dt=0.05
        self.target=1.0
        self.A=np.eye(3) #state matrix A
        self.B= -np.eye(3)*self.dt #input matrix B
        self.Q= np.diag([2.0,5.0,1.0]) # state error penalty matrix Q [distance, lateral, heading]
        self.R= np.diag([1.0,2.0,5.0]) #control effort error penalty matrix [vx,vy,wz]

        #math
        P= scipy.linalg.solve_discrete_are(self.A,self.B,self.Q, self.R) # solve discrete liear algebra
        self.K=np.linalg.inv(self.B.T @ P @ self.B+self.R) @ (self.B.T @ P @ self.A) # K=(transpose(B)*P*B+R)^-1 * (transpose(B)*P*A)

        self.get_logger().info(f"LQR ready K=\n{self.K}")

    def pose_callback(self,msg):
        e_foreward=msg.x-self.target
        e_lateral=msg.y
        e_heading= np.arctan2(msg.y,msg.x) #theta= tan^-1(x,y)
        x_error=np.array([[e_foreward],[e_lateral],[e_heading]]) #error vector

        #velocity optimisation
        u= self.K @ x_error
        cmd=Twist()
        cmd.linear.x = float(np.clip(0.5 * e_foreward, -1.0, 1.0))
        
        # Strafe sideways to fix lateral error
        cmd.linear.y = float(np.clip(0.5 * e_lateral, -1.0, 1.0))
        
        # Rotate on the spot to face the target
        cmd.angular.z = float(np.clip(1.0 * e_heading, -2.0, 2.0))
        '''
        cmd.linear.x = float(np.clip(u[0][0], -1.0, 1.0))
        cmd.linear.y = float(np.clip(u[1][0], -1.0, 1.0))
        cmd.angular.z = 0.0 #float(np.clip(u[2][0], -2.0, 2.0))
        '''

        self.publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    lqr_node= LQR()
    
    try:
        rclpy.spin(lqr_node)
    except:
        lqr_node.publisher.publish(Twist())
    finally:
        lqr_node.destroy_node()
        rclpy.try_shutdown()

if __name__ =='__main__':
    main()