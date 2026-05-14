# ORB-SLAM3(Monocular) + Crazyflie AI Deck ROS2 Setup (Ubuntu 24.04)

## Overview

This repository contains the ROS2 workspace and custom UDP camera node used to stream live images from the Crazyflie AI Deck into ORB-SLAM3 using ROS2 on Ubuntu 24.04.

The setup was tested using:

* Ubuntu 24.04
* ROS2 Jazzy
* Crazyflie 2.1+
* AI Deck
* ORB-SLAM3
* OpenCV
* Python ROS2 node for UDP image streaming

The AI Deck camera stream is published as:

```plaintext
/camera/image_raw
```

and ORB-SLAM3 subscribes to this topic for real-time monocular SLAM.

There is no proper documentation to setup orbslam3 library on ubuntu 24.0, this is the resource i found online that worked for me(You can translate to English and follow the instructions)
https://hackmd.io/@dennis40816/rJqjMi6tJe

To learn about the AI deck and to setup streaming over wifi please follow the documentation - https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/#preparing-the-ai-deck-and-crazyflie-firmware 

---

# 1. Clone ORB-SLAM3

Create a working directory:

```bash
mkdir -p ~/Desktop/crazyflie
cd ~/Desktop/crazyflie
```

Clone ORB-SLAM3:

```bash
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
```

Rename if needed:

```bash
mv ORB_SLAM3 orb-slam3-root
```

---

# 2. Build ORB-SLAM3

Install dependencies first.

Then build:

```bash
cd ~/Desktop/crazyflie/orb-slam3-root/ORB-SLAM3
chmod +x build.sh
./build.sh
```

After successful build:

```bash
ls lib
```

should show:

```plaintext
libORB_SLAM3.so
```

---

# 3. Clone This ROS2 Workspace

Clone this repository:

```bash
cd ~/Desktop/crazyflie
git clone <YOUR_REPOSITORY_LINK>
```

The repository already contains:

```plaintext
ros2_ws/src/aideck_camera
```

including:

* udp_camera_node.py
* ROS2 package files
* launch structure
* setup configuration

---

# 4. Camera Calibration (IMPORTANT)

Before running ORB-SLAM3, calibrate your AI Deck camera.

Use ROS camera calibration tools or OpenCV calibration.

Extract:

```plaintext
fx
fy
cx
cy
k1
k2
p1
p2
```

Create:

```plaintext
AI_DECK.yaml
```

Place it here:

```plaintext
ORB-SLAM3/Examples/Monocular/AI_DECK.yaml
```

An example YAML file has already been uploaded in this repository for reference using the calibration parameters extracted from my Crazyflie AI Deck.

---

# 5. ORB-SLAM3 YAML Notes

The YAML file is used directly by ORB-SLAM3 for:

* camera intrinsics
* distortion correction
* ORB feature extraction
* image geometry
* tracking initialization

The UDP camera node itself does NOT use the YAML file.

The YAML is only loaded by ORB-SLAM3.

---
# 6.  Live Pose (XYZ) Output
Modified ORB-SLAM3 tracking to extract pose:

From SLAM system (internally):

Sophus::SE3f Tcw = mpTracker->GetPose();
Converted to world coordinates:

Twc = Tcw.inverse();
Extracted translation:

cv::Mat t = Twc.translation();
This gives:

X, Y, Z position of camera in world frame
You can:

Print to terminal

Publish as ROS topic

Use for drone control

To make ORB-SLAM3 work with this setup and extract live pose: ROS Topic Remapping
Used:
--ros-args -r /camera:=/camera/image_ra
---
# 7. ROS2 Workspace Build

Go to workspace:

```bash
cd ~/Desktop/crazyflie/ros2_ws
```

Build:

```bash
colcon build --merge-install
```

Source:

```bash
source install/setup.bash
```

---

# 8. Run the AI Deck UDP Camera Node

Open Terminal 1:

```bash
cd ~/Desktop/crazyflie/ros2_ws
source install/setup.bash

ros2 run aideck_camera udp_camera_node
```

This starts:

* UDP packet reception
* image reconstruction
* OpenCV visualization
* ROS2 image publishing

The live stream should appear in an OpenCV window.

Published topic:

```plaintext
/camera/image_raw
```

---

# 9. Verify Camera Topic

In another terminal:

```bash
ros2 topic hz /camera/image_raw
```

You should see approximately:

```plaintext
~7 Hz
```

Verify images:

```bash
ros2 topic echo /camera/image_raw --once
```

---

# 10. Start ORB-SLAM3

Open Terminal 2:

```bash
cd ~/Desktop/crazyflie/orb-slam3-root
source /opt/ros/jazzy/setup.bash
source ~/Desktop/crazyflie/ros2_ws/install/setup.bash
```

Run ORB-SLAM3:

```bash
ros2 run orbslam3 mono \
$ORB_SLAM3_ROOT_PATH/ORB-SLAM3/Vocabulary/ORBvoc.txt \
$ORB_SLAM3_ROOT_PATH/ORB-SLAM3/Examples/Monocular/AI_DECK.yaml \
--ros-args -r /camera:=/camera/image_raw
```

This launches:

* ORB-SLAM3 viewer
* real-time feature extraction
* monocular SLAM pipeline
* map creation
* camera tracking

---

# 11. Important Motion During Initialization

During startup, ORB-SLAM3 initializes using visual motion.

Move the camera slowly:

* left-right
* forward-backward
* slight rotations

Avoid:

* fast motion
* blurry frames
* blank walls
* sudden jerks

After initialization:

* map points appear
* tracking begins
* pose estimation starts

---

# 12. QoS Issue Fix (IMPORTANT)

A major issue encountered during setup was:

```plaintext
incompatible QoS policy
```

ORB-SLAM3 uses RELIABLE QoS for image subscription.

The UDP camera node publisher was modified to use:

```python
ReliabilityPolicy.RELIABLE
```

This fixed:

```plaintext
Waiting for images
```

inside ORB-SLAM3.

---

# 13. Changes Made to udp_camera_node.py

The following modifications were implemented:

## Thread-based packet receiving

Instead of ROS timers, a dedicated receive thread was used for stable UDP handling.

## Blocking socket mode

Used:

```python
self.sock.setblocking(True)
```

for stable packet reception.

## Continuous stream trigger

Periodic trigger packets are sent to maintain the AI Deck stream.

## OpenCV debug visualization

Live frames displayed using:

```python
cv2.imshow()
```

## ROS2 image publishing

Frames are converted using CvBridge and published to:

```plaintext
/camera/image_raw
```

## QoS compatibility fix

Publisher configured with:

```python
ReliabilityPolicy.RELIABLE
```

for ORB-SLAM3 compatibility.

---

# 14. ORB-SLAM3 Output

After successful initialization:

* sparse feature map generation
* camera trajectory estimation
* live localization
* keyframe generation
* loop closure support

The viewer displays:

* tracked features
* keyframes
* camera pose
* sparse 3D map

---

# 15. Live XYZ Pose Output

Changes were additionally made inside the ORB-SLAM3 ROS2 wrapper files to obtain live XYZ pose output from the SLAM system.

The modifications were implemented using guidance and debugging through GPT-assisted development sessions.

The changes involved:

* accessing ORB-SLAM3 pose matrices
* extracting translation vectors
* converting pose into live XYZ coordinates
* exposing pose information from the SLAM pipeline

These modifications were applied inside the ORB-SLAM3 ROS2 integration source files.

---

# 16. Current Working Pipeline

Final working pipeline:

```plaintext
Crazyflie AI Deck
        ↓
UDP packets over WiFi
        ↓
udp_camera_node.py
        ↓
ROS2 topic (/camera/image_raw)
        ↓
ORB-SLAM3 monocular SLAM
        ↓
Real-time tracking + sparse map generation
```

---

# 17. Future Improvements

Possible extensions:

* Mono-Inertial ORB-SLAM3
* IMU synchronization
* Navigation stack integration
* Autonomous waypoint navigation

---

# 17. Notes

This setup uses monocular SLAM.

Current limitations:

* sparse map only
* scale ambiguity
* low camera FPS (~7 Hz)

Mono-inertial integration is the next planned step.

---

# 18. Credits

* https://github.com/zang09/ORB_SLAM3_ROS2
* Bitcraze Crazyflie 2.1+ (https://www.bitcraze.io/products/crazyflie-2-1-plus/)
* AI Deck (https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/#preparing-the-ai-deck-and-crazyflie-firmware)



