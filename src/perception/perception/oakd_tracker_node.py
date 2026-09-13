import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

import depthai as dai
import blobconverter

class OakdTrackerNode(Node):
    def __init__(self):
        super().__init__('oakd_tracker_node')
        
        self.pose_pub = self.create_publisher(Point, '/target_person_pose', 10)
        
        self.get_logger().info("Initializing Headless OAK-D Pipeline...")
        self.pipeline = self.create_pipeline()
        
        self.device = dai.Device(self.pipeline)
        
        # We only need the neural network detections queue now! No video stream.
        self.q_nn = self.device.getOutputQueue(name="detections", maxSize=4, blocking=False)
        
        self.timer = self.create_timer(0.033, self.process_data)
        self.get_logger().info("Tracker Active. Publishing to /target_person_pose")

    def create_pipeline(self):
        pipeline = dai.Pipeline()

        cam_rgb = pipeline.create(dai.node.ColorCamera)
        spatial_net = pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
        mono_left = pipeline.create(dai.node.MonoCamera)
        mono_right = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)

        # Output node ONLY for detections, nothing for video
        xout_nn = pipeline.create(dai.node.XLinkOut)
        xout_nn.setStreamName("detections")

        cam_rgb.setPreviewSize(300, 300)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.CAM_C)

        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)

        spatial_net.setBlobPath(blobconverter.from_zoo(name='mobilenet-ssd', shaves=6))
        spatial_net.setConfidenceThreshold(0.5)
        spatial_net.input.setBlocking(False)
        spatial_net.setBoundingBoxScaleFactor(0.5)
        spatial_net.setDepthLowerThreshold(100)
        spatial_net.setDepthUpperThreshold(5000)

        # Linking everything up inside the camera
        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)
        
        cam_rgb.preview.link(spatial_net.input)
        stereo.depth.link(spatial_net.inputDepth)
        spatial_net.out.link(xout_nn.input) # Send ONLY the text data to the Pi

        return pipeline

    def process_data(self):
        in_nn = self.q_nn.tryGet()

        if in_nn is not None:
            for detection in in_nn.detections:
                if detection.label == 15: # 15 is 'Person'
                    
                    bot_x = detection.spatialCoordinates.x / 1000.0
                    bot_y = detection.spatialCoordinates.y / 1000.0
                    bot_z = detection.spatialCoordinates.z / 1000.0

                    msg = Point()
                    msg.x = float(bot_x)
                    msg.y = float(bot_y)
                    msg.z = float(bot_z)
                    
                    self.pose_pub.publish(msg)
                    self.get_logger().info(f"Tracking: X:{bot_x:.2f}m | Z:{bot_z:.2f}m")

    def destroy_node(self):
        self.device.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = OakdTrackerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down tracker node...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()