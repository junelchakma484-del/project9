#!/usr/bin/env python3
"""
Database initialization script for Face Mask Detection System
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_db_session, Camera as CameraModel
from src.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_cameras():
    """Create sample camera records"""
    try:
        session = get_db_session()
        
        # Check if cameras already exist
        existing_cameras = session.query(CameraModel).count()
        if existing_cameras > 0:
            logger.info(f"Found {existing_cameras} existing cameras, skipping sample creation")
            session.close()
            return
        
        # Sample camera data
        sample_cameras = [
            {
                'id': 'camera_1',
                'name': 'Main Entrance',
                'type': 'ip',
                'url': 'rtsp://admin:password@192.168.1.100:554/stream1',
                'location': 'Building A - Main Entrance',
                'is_active': True
            },
            {
                'id': 'camera_2',
                'name': 'Computer Lab',
                'type': 'rpi',
                'device_id': 0,
                'location': 'Building B - Computer Lab',
                'is_active': True
            },
            {
                'id': 'camera_3',
                'name': 'Library Entrance',
                'type': 'ip',
                'url': 'rtsp://admin:password@192.168.1.101:554/stream1',
                'location': 'Building C - Library',
                'is_active': True
            },
            {
                'id': 'camera_4',
                'name': 'Cafeteria',
                'type': 'rpi',
                'device_id': 1,
                'location': 'Building A - Cafeteria',
                'is_active': False
            }
        ]
        
        # Create camera records
        for camera_data in sample_cameras:
            camera = CameraModel(**camera_data)
            session.add(camera)
        
        session.commit()
        logger.info(f"Created {len(sample_cameras)} sample cameras")
        session.close()
        
    except Exception as e:
        logger.error(f"Error creating sample cameras: {e}")
        session.rollback()
        session.close()

def main():
    """Main initialization function"""
    try:
        logger.info("Starting database initialization...")
        
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize database tables
        init_db()
        logger.info("Database tables created successfully")
        
        # Create sample data
        create_sample_cameras()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
