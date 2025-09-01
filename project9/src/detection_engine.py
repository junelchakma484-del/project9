"""
Detection Engine - AI-powered face mask detection
"""

import cv2
import numpy as np
import tensorflow as tf
import logging
import threading
import time
import queue
from typing import List, Dict, Tuple
from datetime import datetime
import os

from .config import Config
from .database import get_db_session, Detection as DetectionModel

logger = logging.getLogger(__name__)

class FaceMaskDetector:
    """AI model for face mask detection"""
    
    def __init__(self):
        self.model = None
        self.face_cascade = None
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        self._load_models()
    
    def _load_models(self):
        """Load AI models"""
        try:
            # Load face detection model
            if os.path.exists(Config.FACE_DETECTION_MODEL):
                self.face_cascade = cv2.CascadeClassifier(Config.FACE_DETECTION_MODEL)
            else:
                # Use default OpenCV face detection
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Load mask detection model
            if os.path.exists(Config.MODEL_PATH):
                self.model = tf.keras.models.load_model(Config.MODEL_PATH)
                logger.info("Loaded pre-trained mask detection model")
            else:
                logger.warning("No pre-trained model found, using basic detection")
                self.model = None
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        return faces
    
    def predict_mask(self, face_roi: np.ndarray) -> Tuple[str, float]:
        """Predict if face has mask"""
        if self.model is None:
            # Basic heuristic detection (placeholder)
            return self._basic_mask_detection(face_roi)
        
        try:
            # Preprocess image
            face_roi = cv2.resize(face_roi, (224, 224))
            face_roi = face_roi / 255.0
            face_roi = np.expand_dims(face_roi, axis=0)
            
            # Predict
            prediction = self.model.predict(face_roi, verbose=0)
            confidence = float(prediction[0][0])
            
            if confidence > self.confidence_threshold:
                return "mask", confidence
            else:
                return "no_mask", 1 - confidence
                
        except Exception as e:
            logger.error(f"Error in mask prediction: {e}")
            return "unknown", 0.0
    
    def _basic_mask_detection(self, face_roi: np.ndarray) -> Tuple[str, float]:
        """Basic mask detection using color analysis"""
        # Convert to HSV
        hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
        
        # Define skin color range
        lower_skin = np.array([0, 20, 70])
        upper_skin = np.array([20, 255, 255])
        
        # Create mask for skin color
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Calculate skin percentage
        skin_pixels = cv2.countNonZero(skin_mask)
        total_pixels = face_roi.shape[0] * face_roi.shape[1]
        skin_percentage = skin_pixels / total_pixels
        
        # Simple heuristic: if skin percentage is high, likely no mask
        if skin_percentage > 0.3:
            return "no_mask", skin_percentage
        else:
            return "mask", 1 - skin_percentage
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """Process frame and detect faces with masks"""
        results = {
            'faces_detected': 0,
            'masks_detected': 0,
            'no_masks_detected': 0,
            'detections': [],
            'confidence_score': 0.0
        }
        
        try:
            # Detect faces
            faces = self.detect_faces(frame)
            results['faces_detected'] = len(faces)
            
            if len(faces) == 0:
                return results
            
            total_confidence = 0.0
            
            for (x, y, w, h) in faces:
                # Extract face ROI
                face_roi = frame[y:y+h, x:x+w]
                
                # Predict mask
                mask_status, confidence = self.predict_mask(face_roi)
                
                detection = {
                    'bbox': (x, y, w, h),
                    'mask_status': mask_status,
                    'confidence': confidence
                }
                results['detections'].append(detection)
                
                if mask_status == "mask":
                    results['masks_detected'] += 1
                elif mask_status == "no_mask":
                    results['no_masks_detected'] += 1
                
                total_confidence += confidence
            
            # Calculate average confidence
            if len(faces) > 0:
                results['confidence_score'] = total_confidence / len(faces)
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return results

class DetectionEngine:
    """Main detection engine with multithreading"""
    
    def __init__(self):
        self.detector = FaceMaskDetector()
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=Config.QUEUE_SIZE)
        self.result_queue = queue.Queue(maxsize=Config.QUEUE_SIZE)
        self.worker_threads = []
        self.max_workers = Config.MAX_WORKERS
        
        # Statistics
        self.total_frames_processed = 0
        self.total_detections = 0
        self.processing_fps = 0
        self.last_fps_update = time.time()
        self.frames_since_update = 0
    
    def start(self):
        """Start detection engine"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            thread = threading.Thread(target=self._worker_loop, daemon=True, name=f"DetectionWorker-{i}")
            thread.start()
            self.worker_threads.append(thread)
        
        logger.info(f"Started detection engine with {self.max_workers} workers")
    
    def stop(self):
        """Stop detection engine"""
        self.is_running = False
        
        # Wait for threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        self.worker_threads.clear()
        logger.info("Stopped detection engine")
    
    def add_frame(self, frame_data: Dict):
        """Add frame to processing queue"""
        try:
            self.frame_queue.put_nowait(frame_data)
        except queue.Full:
            logger.warning("Frame queue full, dropping frame")
    
    def get_results(self, timeout: float = 1.0) -> List[Dict]:
        """Get detection results"""
        results = []
        try:
            while True:
                result = self.result_queue.get_nowait()
                results.append(result)
        except queue.Empty:
            pass
        return results
    
    def _worker_loop(self):
        """Worker thread loop"""
        while self.is_running:
            try:
                # Get frame from queue
                frame_data = self.frame_queue.get(timeout=1.0)
                
                # Process frame
                frame = frame_data['frame']
                camera_id = frame_data['camera_id']
                timestamp = frame_data['timestamp']
                
                # Detect faces and masks
                detection_results = self.detector.process_frame(frame)
                
                # Add metadata
                detection_results.update({
                    'camera_id': camera_id,
                    'timestamp': timestamp,
                    'frame_shape': frame.shape
                })
                
                # Save to database
                self._save_detection(detection_results)
                
                # Add to result queue
                try:
                    self.result_queue.put_nowait(detection_results)
                except queue.Full:
                    logger.warning("Result queue full, dropping result")
                
                # Update statistics
                self._update_statistics()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in detection worker: {e}")
    
    def _save_detection(self, detection_results: Dict):
        """Save detection to database"""
        try:
            session = get_db_session()
            
            detection = DetectionModel(
                camera_id=detection_results['camera_id'],
                timestamp=detection_results['timestamp'],
                face_count=detection_results['faces_detected'],
                mask_count=detection_results['masks_detected'],
                no_mask_count=detection_results['no_masks_detected'],
                confidence_score=detection_results['confidence_score']
            )
            
            session.add(detection)
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
    
    def _update_statistics(self):
        """Update processing statistics"""
        self.total_frames_processed += 1
        self.frames_since_update += 1
        
        current_time = time.time()
        if current_time - self.last_fps_update >= 1.0:
            self.processing_fps = self.frames_since_update / (current_time - self.last_fps_update)
            self.frames_since_update = 0
            self.last_fps_update = current_time
    
    def get_statistics(self) -> Dict:
        """Get engine statistics"""
        return {
            'is_running': self.is_running,
            'total_frames_processed': self.total_frames_processed,
            'processing_fps': round(self.processing_fps, 2),
            'queue_size': self.frame_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'active_workers': len([t for t in self.worker_threads if t.is_alive()])
        }
    
    def process_single_frame(self, frame: np.ndarray) -> Dict:
        """Process a single frame (for testing)"""
        return self.detector.process_frame(frame)
