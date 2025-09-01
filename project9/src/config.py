"""
Configuration module for Face Mask Detection System
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/face_mask_detection')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Camera Configuration
    CAMERA_CONFIG_PATH = os.getenv('CAMERA_CONFIG_PATH', 'config/cameras.json')
    FRAME_RATE = int(os.getenv('FRAME_RATE', 30))
    PROCESSING_INTERVAL = float(os.getenv('PROCESSING_INTERVAL', 0.1))
    
    # AI Model Configuration
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/face_mask_detector.h5')
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.8))
    FACE_DETECTION_MODEL = os.getenv('FACE_DETECTION_MODEL', 'models/haarcascade_frontalface_default.xml')
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
    
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
    MQTT_TOPIC_PREFIX = os.getenv('MQTT_TOPIC_PREFIX', 'face_mask_detection')
    
    # Grafana Configuration
    GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
    GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')
    
    # Performance Settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    QUEUE_SIZE = int(os.getenv('QUEUE_SIZE', 100))
    BUFFER_SIZE = int(os.getenv('BUFFER_SIZE', 10))
    
    # Alert Configuration
    ALERT_COOLDOWN = int(os.getenv('ALERT_COOLDOWN', 300))  # 5 minutes
    VIOLATION_THRESHOLD = int(os.getenv('VIOLATION_THRESHOLD', 3))
    
    # Email Configuration
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
