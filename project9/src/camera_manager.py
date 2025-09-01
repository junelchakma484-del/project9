"""
Camera Manager - Handles multiple camera streams with multithreading
"""

import cv2
import json
import logging
import threading
import time
import queue
from typing import Dict, List, Optional
from datetime import datetime

from .config import Config
from .database import get_db_session, Camera as CameraModel

logger = logging.getLogger(__name__)

class CameraStream:
    """Individual camera stream handler"""
    
    def __init__(self, camera_id: str, name: str, camera_type: str, 
                 url: str = None, device_id: int = None, location: str = None):
        self.camera_id = camera_id
        self.name = name
        self.camera_type = camera_type
        self.url = url
        self.device_id = device_id
        self.location = location
        
        self.cap = None
        self.is_running = False
        self.is_active = False
        self.frame_queue = queue.Queue(maxsize=Config.BUFFER_SIZE)
        self.thread = None
        self.fps = 0
        self.total_frames = 0
        self.dropped_frames = 0
        
    def start(self):
        """Start camera stream"""
        if self.camera_type == 'ip':
            self.cap = cv2.VideoCapture(self.url)
        elif self.camera_type == 'rpi':
            self.cap = cv2.VideoCapture(self.device_id)
        
        if not self.cap.isOpened():
            raise Exception(f"Failed to open camera {self.camera_id}")
        
        self.is_running = True
        self.is_active = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started camera: {self.camera_id}")
    
    def stop(self):
        """Stop camera stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info(f"Stopped camera: {self.camera_id}")
    
    def _stream_loop(self):
        """Main streaming loop"""
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                try:
                    self.frame_queue.put_nowait({
                        'frame': frame,
                        'timestamp': datetime.now(),
                        'camera_id': self.camera_id
                    })
                    self.total_frames += 1
                except queue.Full:
                    self.dropped_frames += 1
            time.sleep(1.0 / Config.FRAME_RATE)
    
    def get_frame(self, timeout: float = 1.0):
        """Get latest frame"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

class CameraManager:
    """Manages multiple camera streams"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.is_running = False
        self._load_cameras()
    
    def _load_cameras(self):
        """Load camera configuration"""
        try:
            with open(Config.CAMERA_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            for camera_config in config.get('cameras', []):
                camera = CameraStream(
                    camera_id=camera_config['id'],
                    name=camera_config['name'],
                    camera_type=camera_config['type'],
                    url=camera_config.get('url'),
                    device_id=camera_config.get('device_id'),
                    location=camera_config.get('location')
                )
                self.cameras[camera_config['id']] = camera
            
            logger.info(f"Loaded {len(self.cameras)} cameras")
        except Exception as e:
            logger.error(f"Failed to load cameras: {e}")
    
    def start(self):
        """Start all cameras"""
        self.is_running = True
        for camera in self.cameras.values():
            try:
                camera.start()
            except Exception as e:
                logger.error(f"Failed to start camera {camera.camera_id}: {e}")
    
    def stop(self):
        """Stop all cameras"""
        self.is_running = False
        for camera in self.cameras.values():
            camera.stop()
    
    def get_cameras(self):
        """Get all cameras"""
        return list(self.cameras.values())
    
    def get_camera(self, camera_id: str):
        """Get specific camera"""
        return self.cameras.get(camera_id)
    
    def start_camera(self, camera_id: str):
        """Start specific camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].start()
    
    def stop_camera(self, camera_id: str):
        """Stop specific camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
    
    def restart_camera(self, camera_id: str):
        """Restart specific camera"""
        self.stop_camera(camera_id)
        time.sleep(1)
        self.start_camera(camera_id)
