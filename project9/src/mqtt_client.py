"""
MQTT Client - IoT device communication and control
"""

import logging
import json
import threading
import time
from typing import Dict, Callable, Any
import paho.mqtt.client as mqtt

from .config import Config

logger = logging.getLogger(__name__)

class MQTTClient:
    """MQTT client for IoT device communication"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.broker = Config.MQTT_BROKER
        self.port = Config.MQTT_PORT
        self.username = Config.MQTT_USERNAME
        self.password = Config.MQTT_PASSWORD
        self.topic_prefix = Config.MQTT_TOPIC_PREFIX
        
        # Message handlers
        self.message_handlers = {}
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_attempts = 0
        
        # Auto-reconnect settings
        self.auto_reconnect = True
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        
        if self.broker and self.port:
            self._setup_client()
    
    def _setup_client(self):
        """Setup MQTT client"""
        try:
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set will message
            will_topic = f"{self.topic_prefix}/status"
            will_message = json.dumps({
                "status": "offline",
                "timestamp": time.time()
            })
            self.client.will_set(will_topic, will_message, qos=1, retain=True)
            
            logger.info("MQTT client setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT client: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        if not self.client:
            logger.error("MQTT client not initialized")
            return False
        
        try:
            self.connection_attempts += 1
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}")
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                self.is_connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Connection callback"""
        if rc == 0:
            self.is_connected = True
            self.connection_attempts = 0
            logger.info("Connected to MQTT broker")
            
            # Subscribe to topics
            self._subscribe_to_topics()
            
            # Publish online status
            self.publish_status("online")
            
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Disconnection callback"""
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")
        
        # Auto-reconnect
        if self.auto_reconnect and rc != 0:
            if self.connection_attempts < self.max_reconnect_attempts:
                logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
                threading.Timer(self.reconnect_delay, self.connect).start()
            else:
                logger.error("Max reconnection attempts reached")
    
    def _on_message(self, client, userdata, msg):
        """Message received callback"""
        try:
            self.messages_received += 1
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw": payload}
            
            # Call registered handlers
            if topic in self.message_handlers:
                for handler in self.message_handlers[topic]:
                    try:
                        handler(topic, data)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Message published callback"""
        self.messages_sent += 1
        logger.debug(f"Message published with ID: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Subscribe callback"""
        logger.info(f"Subscribed to topic with QoS: {granted_qos}")
    
    def _subscribe_to_topics(self):
        """Subscribe to relevant topics"""
        topics = [
            f"{self.topic_prefix}/+/control",  # Camera control
            f"{self.topic_prefix}/+/status",   # Device status
            f"{self.topic_prefix}/+/alert",    # Device alerts
            f"{self.topic_prefix}/system/+/",  # System messages
        ]
        
        for topic in topics:
            try:
                self.client.subscribe(topic, qos=1)
                logger.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")
    
    def publish(self, topic: str, message: Dict, qos: int = 1, retain: bool = False) -> bool:
        """Publish message to topic"""
        if not self.is_connected:
            logger.warning("MQTT client not connected")
            return False
        
        try:
            full_topic = f"{self.topic_prefix}/{topic}"
            payload = json.dumps(message)
            
            result = self.client.publish(full_topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to {full_topic}")
                return True
            else:
                logger.error(f"Failed to publish message: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def publish_status(self, status: str, metadata: Dict = None):
        """Publish system status"""
        message = {
            "status": status,
            "timestamp": time.time(),
            "component": "face_mask_detection_system"
        }
        
        if metadata:
            message.update(metadata)
        
        return self.publish("status", message, retain=True)
    
    def publish_detection(self, camera_id: str, detection_data: Dict):
        """Publish detection results"""
        message = {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "detection": detection_data
        }
        
        return self.publish(f"detection/{camera_id}", message)
    
    def publish_alert(self, alert_type: str, alert_data: Dict):
        """Publish alert"""
        message = {
            "type": alert_type,
            "timestamp": time.time(),
            "data": alert_data
        }
        
        return self.publish(f"alert/{alert_type}", message)
    
    def publish_camera_control(self, camera_id: str, action: str, params: Dict = None):
        """Publish camera control command"""
        message = {
            "action": action,
            "timestamp": time.time(),
            "params": params or {}
        }
        
        return self.publish(f"camera/{camera_id}/control", message)
    
    def add_message_handler(self, topic: str, handler: Callable[[str, Dict], Any]):
        """Add message handler for topic"""
        if topic not in self.message_handlers:
            self.message_handlers[topic] = []
        
        self.message_handlers[topic].append(handler)
        logger.info(f"Added message handler for topic: {topic}")
    
    def remove_message_handler(self, topic: str, handler: Callable[[str, Dict], Any]):
        """Remove message handler"""
        if topic in self.message_handlers and handler in self.message_handlers[topic]:
            self.message_handlers[topic].remove(handler)
            logger.info(f"Removed message handler for topic: {topic}")
    
    def get_statistics(self) -> Dict:
        """Get client statistics"""
        return {
            'is_connected': self.is_connected,
            'broker': self.broker,
            'port': self.port,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'connection_attempts': self.connection_attempts,
            'auto_reconnect': self.auto_reconnect
        }
    
    def test_connection(self) -> bool:
        """Test MQTT connection"""
        if not self.is_connected:
            return False
        
        test_message = {
            "test": True,
            "timestamp": time.time(),
            "message": "Connection test"
        }
        
        return self.publish("test", test_message)
