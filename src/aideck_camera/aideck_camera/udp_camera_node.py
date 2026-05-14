import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import socket
import struct
import cv2
import numpy as np


ESP32_IP = "192.168.4.1"
ESP32_PORT = 5000
UDP_IP = "0.0.0.0"
UDP_PORT = 5001

CPX_HEADER_SIZE = 4
IMG_HEADER_MAGIC = 0xBC
IMG_HEADER_SIZE = 11

MAGIC_BYTE = b'FER'


class AIDeckCameraNode(Node):

    def __init__(self):
        super().__init__('aideck_camera_node')

        self.publisher_ = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()

        # UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)  # 🔥 IMPORTANT FIX

        # Send initial trigger
        self.sock.sendto(MAGIC_BYTE, (ESP32_IP, ESP32_PORT))

        self.get_logger().info("UDP camera ROS2 node started")

        # Stream state
        self.stream = {
            "buffer": bytearray(),
            "expected_size": None,
            "receiving": False,
        }

        # Timers
        self.timer = self.create_timer(0.001, self.receive_packet)
        self.trigger_timer = self.create_timer(1.0, self.send_trigger)

    def send_trigger(self):
        # Keep stream alive
        self.sock.sendto(MAGIC_BYTE, (ESP32_IP, ESP32_PORT))

    def receive_packet(self):

        try:
            data, addr = self.sock.recvfrom(4096)  # 🔥 increased buffer
            self.get_logger().info("Packet received")
        except BlockingIOError:
            return

        s = self.stream

        # ---------- HEADER ----------
        if len(data) >= CPX_HEADER_SIZE + 1 and data[CPX_HEADER_SIZE] == IMG_HEADER_MAGIC:

            payload = data[CPX_HEADER_SIZE:]

            if len(payload) < IMG_HEADER_SIZE:
                return

            magic, width, height, depth, fmt, size = struct.unpack(
                "<BHHBBI", payload[:IMG_HEADER_SIZE]
            )

            s["expected_size"] = size
            s["buffer"] = bytearray(payload[IMG_HEADER_SIZE:])
            s["receiving"] = True

        # ---------- PAYLOAD ----------
        elif s["receiving"]:

            s["buffer"].extend(data[CPX_HEADER_SIZE:])

            if len(s["buffer"]) >= s["expected_size"]:

                try:
                    img = cv2.imdecode(
                        np.frombuffer(s["buffer"], np.uint8),
                        cv2.IMREAD_UNCHANGED
                    )

                    if img is not None:

                        # Ensure grayscale
                        if len(img.shape) == 3:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                        # 🔥 DEBUG VIEW
                        cv2.imshow("AI Deck Stream", img)
                        cv2.waitKey(1)

                        # Publish ROS image
                        msg = self.bridge.cv2_to_imgmsg(img, encoding="mono8")
                        msg.header.stamp = self.get_clock().now().to_msg()
                        msg.header.frame_id = "camera"

                        self.publisher_.publish(msg)

                except Exception as e:
                    self.get_logger().warn(f"Decode error: {e}")

                # Reset
                s["receiving"] = False
                s["expected_size"] = None
                s["buffer"] = bytearray()


def main(args=None):
    rclpy.init(args=args)
    node = AIDeckCameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
