"""
Telegram Bot - Sends alerts and notifications
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List
import requests

from .config import Config
from .database import get_db_session, Alert as AlertModel

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for sending alerts"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.enabled = Config.TELEGRAM_ENABLED
        self.is_connected = False
        
        # Alert cooldown tracking
        self.last_alert_time = {}
        self.alert_cooldown = Config.ALERT_COOLDOWN
        
        # Statistics
        self.messages_sent = 0
        self.failed_messages = 0
        
        if self.enabled and self.bot_token and self.chat_id:
            self._test_connection()
    
    def _test_connection(self):
        """Test bot connection"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    self.is_connected = True
                    logger.info(f"Telegram bot connected: @{bot_info['result']['username']}")
                else:
                    logger.error("Telegram bot connection failed")
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.messages_sent += 1
                    logger.debug(f"Telegram message sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
                    self.failed_messages += 1
                    return False
            else:
                logger.error(f"Telegram HTTP error: {response.status_code}")
                self.failed_messages += 1
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            self.failed_messages += 1
            return False
    
    def send_alert(self, alert_type: str, camera_id: str, message: str, 
                   severity: str = "medium", metadata: Dict = None) -> bool:
        """Send alert with cooldown protection"""
        # Check cooldown
        alert_key = f"{camera_id}_{alert_type}"
        current_time = time.time()
        
        if alert_key in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[alert_key]
            if time_since_last < self.alert_cooldown:
                logger.debug(f"Alert cooldown active for {alert_key}")
                return False
        
        # Format message
        formatted_message = self._format_alert_message(
            alert_type, camera_id, message, severity, metadata
        )
        
        # Send message
        success = self.send_message(formatted_message)
        
        if success:
            self.last_alert_time[alert_key] = current_time
            
            # Save to database
            self._save_alert(alert_type, camera_id, message, severity, metadata)
        
        return success
    
    def send_violation_alert(self, camera_id: str, camera_name: str, 
                           violations: int, location: str = None) -> bool:
        """Send mask violation alert"""
        message = f"🚨 <b>Mask Violation Detected</b>\n\n"
        message += f"📹 Camera: {camera_name}\n"
        if location:
            message += f"📍 Location: {location}\n"
        message += f"👥 Violations: {violations}\n"
        message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += "Please ensure proper mask usage in this area."
        
        return self.send_alert(
            alert_type="violation",
            camera_id=camera_id,
            message=message,
            severity="high"
        )
    
    def send_system_alert(self, component: str, message: str, severity: str = "medium") -> bool:
        """Send system alert"""
        formatted_message = f"🔧 <b>System Alert</b>\n\n"
        formatted_message += f"Component: {component}\n"
        formatted_message += f"Message: {message}\n"
        formatted_message += f"Severity: {severity.upper()}\n"
        formatted_message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_alert(
            alert_type="system",
            camera_id="system",
            message=formatted_message,
            severity=severity
        )
    
    def send_camera_alert(self, camera_id: str, camera_name: str, 
                         alert_type: str, message: str) -> bool:
        """Send camera-specific alert"""
        formatted_message = f"📹 <b>Camera Alert</b>\n\n"
        formatted_message += f"Camera: {camera_name}\n"
        formatted_message += f"Type: {alert_type}\n"
        formatted_message += f"Message: {message}\n"
        formatted_message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_alert(
            alert_type="camera",
            camera_id=camera_id,
            message=formatted_message,
            severity="medium"
        )
    
    def send_daily_report(self, report_data: Dict) -> bool:
        """Send daily summary report"""
        message = f"📊 <b>Daily Report</b>\n\n"
        message += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Summary statistics
        total_detections = report_data.get('total_detections', 0)
        total_violations = report_data.get('total_violations', 0)
        active_cameras = report_data.get('active_cameras', 0)
        
        message += f"📈 Total Detections: {total_detections}\n"
        message += f"🚨 Total Violations: {total_violations}\n"
        message += f"📹 Active Cameras: {active_cameras}\n"
        
        if total_detections > 0:
            violation_rate = (total_violations / total_detections) * 100
            message += f"📊 Violation Rate: {violation_rate:.1f}%\n"
        
        # Camera breakdown
        if 'camera_stats' in report_data:
            message += "\n📹 <b>Camera Breakdown:</b>\n"
            for camera in report_data['camera_stats']:
                message += f"• {camera['name']}: {camera['detections']} detections, {camera['violations']} violations\n"
        
        return self.send_message(message)
    
    def _format_alert_message(self, alert_type: str, camera_id: str, message: str,
                             severity: str, metadata: Dict = None) -> str:
        """Format alert message with emojis and styling"""
        # Add severity emoji
        severity_emoji = {
            "low": "ℹ️",
            "medium": "⚠️", 
            "high": "🚨",
            "critical": "💥"
        }.get(severity, "⚠️")
        
        # Add alert type emoji
        type_emoji = {
            "violation": "🚨",
            "system": "🔧",
            "camera": "📹"
        }.get(alert_type, "📢")
        
        formatted = f"{severity_emoji} {type_emoji} <b>{alert_type.upper()} ALERT</b>\n\n"
        formatted += message
        
        if metadata:
            formatted += "\n\n📋 <b>Additional Info:</b>\n"
            for key, value in metadata.items():
                formatted += f"• {key}: {value}\n"
        
        return formatted
    
    def _save_alert(self, alert_type: str, camera_id: str, message: str, 
                   severity: str, metadata: Dict = None):
        """Save alert to database"""
        try:
            session = get_db_session()
            
            alert = AlertModel(
                camera_id=camera_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.now()
            )
            
            session.add(alert)
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
    
    def get_statistics(self) -> Dict:
        """Get bot statistics"""
        return {
            'enabled': self.enabled,
            'is_connected': self.is_connected,
            'messages_sent': self.messages_sent,
            'failed_messages': self.failed_messages,
            'success_rate': (self.messages_sent / (self.messages_sent + self.failed_messages) * 100) 
                           if (self.messages_sent + self.failed_messages) > 0 else 0
        }
    
    def test_connection(self) -> bool:
        """Test bot connection"""
        test_message = "🤖 Face Mask Detection System - Connection Test\n\n"
        test_message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        test_message += "Status: System is running and connected!"
        
        return self.send_message(test_message)
