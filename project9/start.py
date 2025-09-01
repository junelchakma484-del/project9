#!/usr/bin/env python3
"""
Face Mask Detection System - Startup Script
Coordinates all system components and services
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.database import init_db
from src.camera_manager import CameraManager
from src.detection_engine import DetectionEngine
from src.telegram_bot import TelegramBot
from src.mqtt_client import MQTTClient
from src.analytics import AnalyticsEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FaceMaskDetectionSystem:
    """Main system coordinator"""
    
    def __init__(self):
        self.camera_manager = None
        self.detection_engine = None
        self.telegram_bot = None
        self.mqtt_client = None
        self.analytics_engine = None
        self.is_running = False
        
    def initialize_system(self):
        """Initialize all system components"""
        try:
            logger.info("Starting Face Mask Detection System...")
            
            # Validate configuration
            Config.validate()
            logger.info("Configuration validated successfully")
            
            # Initialize database
            init_db()
            logger.info("Database initialized successfully")
            
            # Initialize components
            self.camera_manager = CameraManager()
            self.detection_engine = DetectionEngine()
            self.telegram_bot = TelegramBot()
            self.mqtt_client = MQTTClient()
            self.analytics_engine = AnalyticsEngine()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False
    
    def start_services(self):
        """Start all services"""
        try:
            logger.info("Starting services...")
            
            # Start detection engine
            self.detection_engine.start()
            logger.info("Detection engine started")
            
            # Start camera manager
            self.camera_manager.start()
            logger.info("Camera manager started")
            
            # Connect MQTT client
            if self.mqtt_client.broker:
                self.mqtt_client.connect()
                logger.info("MQTT client connected")
            
            # Test Telegram bot
            if self.telegram_bot.enabled:
                self.telegram_bot.test_connection()
                logger.info("Telegram bot tested")
            
            self.is_running = True
            logger.info("All services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            return False
    
    def start_processing_loop(self):
        """Main processing loop"""
        logger.info("Starting processing loop...")
        
        while self.is_running:
            try:
                # Get frames from cameras
                frames = self.camera_manager.get_active_frames()
                
                # Add frames to detection engine
                for frame_data in frames:
                    self.detection_engine.add_frame(frame_data)
                
                # Get detection results
                results = self.detection_engine.get_results()
                
                # Process results
                for result in results:
                    self._process_detection_result(result)
                
                # Sleep to prevent CPU overload
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1)
    
    def _process_detection_result(self, result):
        """Process detection results"""
        try:
            camera_id = result.get('camera_id')
            no_mask_count = result.get('no_masks_detected', 0)
            
            # Check for violations
            if no_mask_count > 0:
                # Get camera info
                camera = self.camera_manager.get_camera(camera_id)
                if camera:
                    # Send Telegram alert
                    if self.telegram_bot.enabled:
                        self.telegram_bot.send_violation_alert(
                            camera_id=camera_id,
                            camera_name=camera.name,
                            violations=no_mask_count,
                            location=camera.location
                        )
                    
                    # Publish MQTT alert
                    if self.mqtt_client.is_connected:
                        self.mqtt_client.publish_alert('violation', {
                            'camera_id': camera_id,
                            'violations': no_mask_count,
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Publish detection to MQTT
            if self.mqtt_client.is_connected:
                self.mqtt_client.publish_detection(camera_id, result)
                
        except Exception as e:
            logger.error(f"Error processing detection result: {e}")
    
    def stop_services(self):
        """Stop all services"""
        logger.info("Stopping services...")
        
        self.is_running = False
        
        if self.camera_manager:
            self.camera_manager.stop()
            logger.info("Camera manager stopped")
        
        if self.detection_engine:
            self.detection_engine.stop()
            logger.info("Detection engine stopped")
        
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        logger.info("All services stopped")
    
    def get_system_status(self):
        """Get system status"""
        return {
            'is_running': self.is_running,
            'camera_manager': {
                'is_running': self.camera_manager.is_running if self.camera_manager else False,
                'cameras': len(self.camera_manager.get_cameras()) if self.camera_manager else 0
            },
            'detection_engine': {
                'is_running': self.detection_engine.is_running if self.detection_engine else False,
                'statistics': self.detection_engine.get_statistics() if self.detection_engine else {}
            },
            'telegram_bot': {
                'enabled': self.telegram_bot.enabled if self.telegram_bot else False,
                'is_connected': self.telegram_bot.is_connected if self.telegram_bot else False
            },
            'mqtt_client': {
                'is_connected': self.mqtt_client.is_connected if self.mqtt_client else False,
                'statistics': self.mqtt_client.get_statistics() if self.mqtt_client else {}
            }
        }

def main():
    """Main entry point"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create system instance
    system = FaceMaskDetectionSystem()
    
    try:
        # Initialize system
        if not system.initialize_system():
            logger.error("Failed to initialize system")
            sys.exit(1)
        
        # Start services
        if not system.start_services():
            logger.error("Failed to start services")
            sys.exit(1)
        
        # Start processing loop
        system.start_processing_loop()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Stop services
        system.stop_services()
        logger.info("System shutdown complete")

if __name__ == "__main__":
    main()
