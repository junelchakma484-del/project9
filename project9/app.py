#!/usr/bin/env python3
"""
Face Mask Detection System - Main Application
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Import our modules
from src.database import init_db, get_db_session
from src.models import Detection, Camera, Alert
from src.camera_manager import CameraManager
from src.detection_engine import DetectionEngine
from src.telegram_bot import TelegramBot
from src.mqtt_client import MQTTClient
from src.analytics import AnalyticsEngine
from src.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
camera_manager = None
detection_engine = None
telegram_bot = None
mqtt_client = None
analytics_engine = None

def initialize_services():
    """Initialize all system services"""
    global camera_manager, detection_engine, telegram_bot, mqtt_client, analytics_engine
    
    try:
        # Initialize database
        init_db()
        
        # Initialize services
        camera_manager = CameraManager()
        detection_engine = DetectionEngine()
        telegram_bot = TelegramBot()
        mqtt_client = MQTTClient()
        analytics_engine = AnalyticsEngine()
        
        # Start camera manager
        camera_manager.start()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        cameras = camera_manager.get_cameras() if camera_manager else []
        active_cameras = len([c for c in cameras if c.is_active])
        
        return jsonify({
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'cameras': {
                'total': len(cameras),
                'active': active_cameras
            },
            'detections': {
                'total_today': analytics_engine.get_today_detections() if analytics_engine else 0,
                'violations_today': analytics_engine.get_today_violations() if analytics_engine else 0
            },
            'services': {
                'camera_manager': camera_manager.is_running if camera_manager else False,
                'detection_engine': detection_engine.is_running if detection_engine else False,
                'telegram_bot': telegram_bot.is_connected if telegram_bot else False,
                'mqtt_client': mqtt_client.is_connected if mqtt_client else False
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras')
def get_cameras():
    """Get all cameras"""
    try:
        cameras = camera_manager.get_cameras() if camera_manager else []
        return jsonify([camera.to_dict() for camera in cameras])
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/control', methods=['POST'])
def control_camera(camera_id):
    """Control camera (start/stop)"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start':
            camera_manager.start_camera(camera_id)
        elif action == 'stop':
            camera_manager.stop_camera(camera_id)
        elif action == 'restart':
            camera_manager.restart_camera(camera_id)
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
        return jsonify({'message': f'Camera {camera_id} {action}ed successfully'})
    except Exception as e:
        logger.error(f"Error controlling camera {camera_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/detections')
def get_detections():
    """Get detection history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        camera_id = request.args.get('camera_id')
        
        session = get_db_session()
        query = session.query(Detection)
        
        if camera_id:
            query = query.filter(Detection.camera_id == camera_id)
            
        detections = query.order_by(Detection.timestamp.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return jsonify([detection.to_dict() for detection in detections])
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get analytics data"""
    try:
        period = request.args.get('period', 'today')
        
        if not analytics_engine:
            return jsonify({'error': 'Analytics engine not available'}), 500
            
        data = analytics_engine.get_analytics(period)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get alert history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        session = get_db_session()
        alerts = session.query(Alert).order_by(
            Alert.timestamp.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify([alert.to_dict() for alert in alerts])
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to Face Mask Detection System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_detections')
def handle_subscribe_detections():
    """Subscribe to detection updates"""
    logger.info(f"Client {request.sid} subscribed to detections")

@socketio.on('subscribe_camera_status')
def handle_subscribe_camera_status():
    """Subscribe to camera status updates"""
    logger.info(f"Client {request.sid} subscribed to camera status")

def broadcast_detection(detection_data):
    """Broadcast detection to all connected clients"""
    socketio.emit('detection_update', detection_data)

def broadcast_camera_status(camera_data):
    """Broadcast camera status to all connected clients"""
    socketio.emit('camera_status', camera_data)

def broadcast_alert(alert_data):
    """Broadcast alert to all connected clients"""
    socketio.emit('alert', alert_data)

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Initialize services
    initialize_services()
    
    # Start the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Face Mask Detection System on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
