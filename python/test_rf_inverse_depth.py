#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import numpy as np
import sys
import os
import glob
import cv2
import time
import open3d as o3d

#from open3d.open3d.visualization import draw_geometries
from sister.sister import Utilities, Camera
from open3d import *
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--camera_file", help="Camera parameters filename", type=str, required=True)
parser.add_argument("--depth_file", help="Depth filename", type=str, required=True)
parser.add_argument("--rgb_file", help="Rgb filename", type=str, default='')
parser.add_argument("--baseline", help="Stereo baseline", type=float, default=0.1)
parser.add_argument("--min_distance", help="Min clip distance", type=float, default=0.0)
parser.add_argument("--max_distance", help="Max clip distance", type=float, default=0.8)
parser.add_argument("--scaling_factor", help="Scaling factor s  -> will be applied (1/s)", type=float, default=256.)
parser.add_argument("--is_depth", help="Is input a depth?", type=int, default=0)
parser.add_argument("--visualization_type", help="Visualziation Type", type=str, default="pcd")
args = parser.parse_args()


# Camera
camera = Camera(filename=args.camera_file)

# Input files
depth_file = args.depth_file
rgb_file = args.rgb_file

# Disparity&Depth
disparity = Utilities.loadRangeImage(depth_file, scaling_factor=1./args.scaling_factor)
#disparity = disparity[:1080, ::]

# DISPARITY SMOOTH
for i in range(0):
    disparity = cv2.bilateralFilter(disparity.astype(np.float32), 5, 6, 6)
for i in range(0):
    disparity = cv2.medianBlur(disparity.astype(np.float32), 5)


if args.is_depth:
    print("IT IS A DEPTH IMAGE!")
    depth = disparity
else:
    depth = camera.getFx() * args.baseline / (disparity)

print("MAX MIN", np.max(depth), np.min(depth))
depth = np.clip(depth, args.min_distance, args.max_distance)

# RGB Image
rgb = None
if len(rgb_file) > 0:
    rgb = cv2.cvtColor(cv2.imread(rgb_file), cv2.COLOR_BGR2RGB)

# DEPTH SMOOTH
for i in range(10):
    depth = cv2.bilateralFilter(depth.astype(np.float32), 5, 0.01, 0)


# Cloud generation
cloud = camera.depthMapToPointCloud(depth)
cloud[:, 2] *= -1

# Open3D Visualizatoin


ext = np.array([[0.79450722, -0.60297211,  0.07199249, -0.01164862],
                [0.29629451, 0.4884098, 0.82077124, -0.10244214],
                [-0.530064,  -0.6307777,  0.56670243,  0.05412735],
                [0.,      0.,   0.,  1.]])


if args.visualization_type == 'pcd':

    geom = Utilities.createPcd(cloud, color_image=rgb)

elif args.visualization_type == 'mesh':

    geom = Utilities.meshFromPointCloud(cloud, color_image=rgb)


outputfile = Path(args.depth_file.replace('.png', '_3D.png'))


vis = o3d.visualization.Visualizer()
vis.create_window()
ctr = vis.get_view_control()
param = ctr.convert_to_pinhole_camera_parameters()
param.extrinsic = ext

vis.add_geometry(geom)

ctr.convert_from_pinhole_camera_parameters(param)
opt = vis.get_render_option()
opt.background_color = np.asarray([46./255.]*3)


vis.update_geometry(geom)
vis.poll_events()
vis.update_renderer()
image = (np.asarray(vis.capture_screen_float_buffer())*255.).astype(np.uint8)
print("IMAGE:", np.max(image))

cv2.imwrite(str(outputfile), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

param = ctr.convert_to_pinhole_camera_parameters()
print(param.extrinsic)
#trajectory = PinholeCameraTrajectory()
#trajectory.intrinsic = param.intrinsic
# trajectory.extrinsic = ext #Matrix4dVector([param[1]])
#write_pinhole_camera_trajectory("/tmp/test.json", trajectory)
vis.destroy_window()

# draw_geometries([mesh])

#write_triangle_mesh("/tmp/mesh.ply", mesh)