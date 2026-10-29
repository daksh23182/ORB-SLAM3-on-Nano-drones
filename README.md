# ORB-SLAM3 (Mono-Inertial) + Crazyflie AI Deck ROS2 Setup (Ubuntu 24.04)

## Overview

This repository contains the ROS2 workspace and custom nodes used to stream live images from the Crazyflie AI Deck and live IMU data from the Crazyflie into ORB-SLAM3 using ROS2 on Ubuntu 24.04.

**Mono-inertial ORB-SLAM3 is running at ~60 FPS with a 160x160 camera stream.**

Demo run video:
https://drive.google.com/file/d/1197XoA7jUXNwrQ64it4OxDi2Vhvk_fRE/view?usp=sharing

The setup was tested using:

* Ubuntu 24.04
* ROS2 Jazzy
* Crazyflie 2.1+
* AI Deck
* Crazyradio
* ORB-SLAM3 (Mono-Inertial)
* OpenCV
* cflib (Crazyflie Python library)

The AI Deck camera stream is published as:

```plaintext
/camera/image_raw
```

The Crazyflie IMU stream is published as:

```plaintext
/cf_imu
```

and ORB-SLAM3 subscribes to both topics for real-time mono-inertial SLAM.

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
git clone https://github.com/daksh23182/ORB-SLAM3-on-Nano-drones-.git ros2_ws
```

The repository already contains:

```plaintext
ros2_ws/src/aideck_camera
```

including:

* camera streaming node
* IMU streaming node (cf_imu_node)
* ROS2 package files
* launch structure
* setup configuration

---

# 4. AI Deck Streamer Setup (160x160)

The camera stream runs through the NanoCockpit streamer on the AI Deck.

Build and flash the streamer to the AI Deck by following the Bitcraze documentation linked above.

Camera settings used:

```plaintext
Resolution : 160 x 160
Format     : Grayscale
Frame rate : ~60 FPS
```

Connect the PC to the AI Deck Wi-Fi before running the camera node.

---

# 5. Camera + IMU Calibration (IMPORTANT)

Before running mono-inertial ORB-SLAM3, calibrate your AI Deck camera at **160x160** and your camera-IMU setup.

Camera (use ROS camera calibration tools or OpenCV calibration):

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

IMU and camera-IMU (needed for mono-inertial mode):

```plaintext
Camera-to-IMU transform (Tbc)
Camera-IMU time offset
Gyroscope noise and random walk
Accelerometer noise and random walk
IMU frequency (~100 Hz)
```

Create:

```plaintext
AI_DECK.yaml
```

Place it with the other ORB-SLAM3 Monocular-Inertial example files and use it in `run_mono_inertial.sh`.

Note: the camera values must be calibrated for the 160x160 stream. Values calibrated at any other resolution will not work.

---

# 6. ORB-SLAM3 YAML Notes

The YAML file is used directly by ORB-SLAM3 for:

* camera intrinsics
* distortion correction
* camera-IMU transform and IMU noise values
* ORB feature extraction
* image geometry
* tracking initialization

The camera and IMU nodes themselves do NOT use the YAML file.

The YAML is only loaded by ORB-SLAM3.

---

# 7. Live Pose Output

Modified ORB-SLAM3 tracking to extract pose:

From SLAM system (internally):

```cpp
Sophus::SE3f Tcw = mpTracker->GetPose();
```

Converted to world coordinates:

```cpp
Sophus::SE3f Twc = Tcw.inverse();
```

This gives the position (X, Y, Z) and orientation (quaternion) of the camera in the world frame.

The pose is printed live in the terminal with a timestamp:

```plaintext
[POSE] t=<time> X=<m> Y=<m> Z=<m> Qx=<> Qy=<> Qz=<> Qw=<>
```

You can:

* Print to terminal
* Publish as ROS topic
* Use for drone control

To make ORB-SLAM3 work with this setup, ROS topic remapping is used:

```plaintext
--ros-args -r /camera:=/camera/image_raw
```

---

# 8. ROS2 Workspace Build

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

# 9. Run the AI Deck Camera Node

Open Terminal 1:

```bash
cd ~/Desktop/crazyflie/ros2_ws
source install/setup.bash

ros2 run aideck_camera nanocockpit_camera_node
```

This starts:

* image reception from the AI Deck over Wi-Fi
* image reconstruction
* ROS2 image publishing

Published topic:

```plaintext
/camera/image_raw
```

---

# 10. Verify Camera Topic

In another terminal:

```bash
ros2 topic hz /camera/image_raw
```

You should see approximately:

```plaintext
~40-60 Hz
```

Verify images:

```bash
ros2 topic echo /camera/image_raw --once
```

---

# 11. Run the Crazyflie IMU Node

Open Terminal 2:

```bash
cd ~/Desktop/crazyflie/ros2_ws
source install/setup.bash

ros2 run aideck_camera cf_imu_node
```

This starts:

* connection to the Crazyflie over the Crazyradio
* Crazyradio transmit power set to -18 dBm
* IMU log block streaming at ~100 Hz
* ROS2 IMU publishing

Published topic:

```plaintext
/cf_imu
```

Verify:

```bash
ros2 topic hz /cf_imu
```

You should see approximately:

```plaintext
~100 Hz
```

---

# 12. Start ORB-SLAM3 (Mono-Inertial)

Open Terminal 3:

```bash
cd ~/Desktop/crazyflie/orb-slam3-root
source /opt/ros/jazzy/setup.bash
source ~/Desktop/crazyflie/ros2_ws/install/setup.bash
```

Run ORB-SLAM3:

```bash
./run_mono_inertial.sh
```

This launches:

* ORB-SLAM3 viewer
* real-time feature extraction
* mono-inertial SLAM pipeline
* map creation
* camera tracking

---

# 13. Important Motion During Initialization

During startup, ORB-SLAM3 initializes using visual motion and IMU data.

Move the camera slowly:

* left-right
* forward-backward
* slight rotations

The IMU needs some motion to estimate scale and gravity direction.

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

# 14. What Worked to Increase FPS

The camera stream went from ~7 FPS to ~60 FPS using the following changes:

## NanoCockpit streamer on the AI Deck

Streams frames from the GAP8 over Wi-Fi much more efficiently than the basic image-streaming example. This was the biggest improvement.

## 160x160 resolution

Each frame has a quarter of the pixels of a 320x320 frame, so many more frames fit through the Wi-Fi link. Resolution is still enough for ORB features indoors.

## Grayscale frames

ORB-SLAM3 only needs intensity, so no colour data is sent or converted.

## Lower Crazyradio transmit power (-18 dBm)

The Crazyradio (IMU link) and the AI Deck Wi-Fi share the 2.4 GHz band. Lowering the radio power stops it from interfering with the video link, so fewer frames are dropped.

---

# 15. QoS Issue Fix (IMPORTANT)

A major issue encountered during setup was:

```plaintext
incompatible QoS policy
```

ORB-SLAM3 uses RELIABLE QoS for image subscription.

The camera node publisher was configured to use:

```python
ReliabilityPolicy.RELIABLE
```

This fixed:

```plaintext
Waiting for images
```

inside ORB-SLAM3.

---

# 16. ORB-SLAM3 Output

After successful initialization:

* sparse feature map generation
* camera trajectory estimation
* live localization
* keyframe generation
* loop closure support
* metric scale from the IMU

The viewer displays:

* tracked features
* keyframes
* camera pose
* sparse 3D map
* inertial graph

---

# 17. Current Working Pipeline

Final working pipeline:

```plaintext
Crazyflie AI Deck (160x160, grayscale)
        ↓
Wi-Fi (NanoCockpit streamer)
        ↓
nanocockpit_camera_node
        ↓
ROS2 topic (/camera/image_raw)  ~60 Hz ─────┐
                                            ├──► ORB-SLAM3 Mono-Inertial
Crazyflie IMU                               │          ↓
        ↓                                   │   Real-time tracking +
Crazyradio (-18 dBm)                        │   sparse map generation +
        ↓                                   │   live [POSE] output
cf_imu_node                                 │
        ↓                                   │
ROS2 topic (/cf_imu)  ~100 Hz ──────────────┘
```

---

# 18. Future Improvements

Possible extensions:

* Fuse the Loco Positioning (LPS) deck with the AI Deck and use the UWB anchors as ground truth to measure the accuracy of the SLAM trajectory
* Navigation stack integration

---

# 19. Credits

* https://github.com/zang09/ORB_SLAM3_ROS2
* Bitcraze Crazyflie 2.1+ (https://www.bitcraze.io/products/crazyflie-2-1-plus/)
* AI Deck (https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/#preparing-the-ai-deck-and-crazyflie-firmware)
