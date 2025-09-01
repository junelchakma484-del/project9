"""
Analytics Engine - Data analysis and reporting
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import func, and_, desc
import pandas as pd

from .config import Config
from .database import get_db_session, Detection as DetectionModel, Camera as CameraModel, Alert as AlertModel

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Analytics engine for data analysis and reporting"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
    
    def get_today_detections(self) -> int:
        """Get total detections for today"""
        try:
            session = get_db_session()
            today = datetime.now().date()
            
            count = session.query(func.count(DetectionModel.id)).filter(
                func.date(DetectionModel.timestamp) == today
            ).scalar()
            
            session.close()
            return count or 0
            
        except Exception as e:
            logger.error(f"Error getting today's detections: {e}")
            return 0
    
    def get_today_violations(self) -> int:
        """Get total violations for today"""
        try:
            session = get_db_session()
            today = datetime.now().date()
            
            count = session.query(func.count(DetectionModel.id)).filter(
                and_(
                    func.date(DetectionModel.timestamp) == today,
                    DetectionModel.no_mask_count > 0
                )
            ).scalar()
            
            session.close()
            return count or 0
            
        except Exception as e:
            logger.error(f"Error getting today's violations: {e}")
            return 0
    
    def get_analytics(self, period: str = "today") -> Dict:
        """Get comprehensive analytics for specified period"""
        cache_key = f"analytics_{period}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_data
        
        try:
            session = get_db_session()
            
            # Calculate date range
            end_date = datetime.now()
            if period == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)  # Default to yesterday
            
            # Get detections in range
            detections = session.query(DetectionModel).filter(
                and_(
                    DetectionModel.timestamp >= start_date,
                    DetectionModel.timestamp <= end_date
                )
            ).all()
            
            # Calculate statistics
            total_detections = len(detections)
            total_faces = sum(d.face_count for d in detections)
            total_masks = sum(d.mask_count for d in detections)
            total_violations = sum(d.no_mask_count for d in detections)
            
            # Calculate rates
            mask_rate = (total_masks / total_faces * 100) if total_faces > 0 else 0
            violation_rate = (total_violations / total_faces * 100) if total_faces > 0 else 0
            
            # Get camera statistics
            camera_stats = self._get_camera_statistics(session, start_date, end_date)
            
            # Get hourly breakdown
            hourly_stats = self._get_hourly_statistics(session, start_date, end_date)
            
            # Get alerts
            alerts = session.query(AlertModel).filter(
                and_(
                    AlertModel.timestamp >= start_date,
                    AlertModel.timestamp <= end_date
                )
            ).all()
            
            analytics_data = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'summary': {
                    'total_detections': total_detections,
                    'total_faces': total_faces,
                    'total_masks': total_masks,
                    'total_violations': total_violations,
                    'mask_rate': round(mask_rate, 2),
                    'violation_rate': round(violation_rate, 2)
                },
                'camera_statistics': camera_stats,
                'hourly_breakdown': hourly_stats,
                'alerts': {
                    'total': len(alerts),
                    'by_type': self._group_alerts_by_type(alerts),
                    'by_severity': self._group_alerts_by_severity(alerts)
                }
            }
            
            session.close()
            
            # Cache the result
            self.cache[cache_key] = (analytics_data, datetime.now())
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    def _get_camera_statistics(self, session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get statistics by camera"""
        try:
            # Get detections grouped by camera
            camera_detections = session.query(
                DetectionModel.camera_id,
                func.count(DetectionModel.id).label('detection_count'),
                func.sum(DetectionModel.face_count).label('total_faces'),
                func.sum(DetectionModel.mask_count).label('total_masks'),
                func.sum(DetectionModel.no_mask_count).label('total_violations')
            ).filter(
                and_(
                    DetectionModel.timestamp >= start_date,
                    DetectionModel.timestamp <= end_date
                )
            ).group_by(DetectionModel.camera_id).all()
            
            # Get camera names
            camera_names = {}
            cameras = session.query(CameraModel).all()
            for camera in cameras:
                camera_names[camera.id] = camera.name
            
            camera_stats = []
            for det in camera_detections:
                total_faces = det.total_faces or 0
                total_masks = det.total_masks or 0
                total_violations = det.total_violations or 0
                
                mask_rate = (total_masks / total_faces * 100) if total_faces > 0 else 0
                violation_rate = (total_violations / total_faces * 100) if total_faces > 0 else 0
                
                camera_stats.append({
                    'camera_id': det.camera_id,
                    'name': camera_names.get(det.camera_id, 'Unknown'),
                    'detections': det.detection_count,
                    'total_faces': total_faces,
                    'total_masks': total_masks,
                    'total_violations': total_violations,
                    'mask_rate': round(mask_rate, 2),
                    'violation_rate': round(violation_rate, 2)
                })
            
            return camera_stats
            
        except Exception as e:
            logger.error(f"Error getting camera statistics: {e}")
            return []
    
    def _get_hourly_statistics(self, session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get hourly breakdown of detections"""
        try:
            # Get detections grouped by hour
            hourly_detections = session.query(
                func.extract('hour', DetectionModel.timestamp).label('hour'),
                func.count(DetectionModel.id).label('detection_count'),
                func.sum(DetectionModel.face_count).label('total_faces'),
                func.sum(DetectionModel.mask_count).label('total_masks'),
                func.sum(DetectionModel.no_mask_count).label('total_violations')
            ).filter(
                and_(
                    DetectionModel.timestamp >= start_date,
                    DetectionModel.timestamp <= end_date
                )
            ).group_by(func.extract('hour', DetectionModel.timestamp)).all()
            
            hourly_stats = []
            for det in hourly_detections:
                total_faces = det.total_faces or 0
                total_masks = det.total_masks or 0
                total_violations = det.total_violations or 0
                
                mask_rate = (total_masks / total_faces * 100) if total_faces > 0 else 0
                violation_rate = (total_violations / total_faces * 100) if total_faces > 0 else 0
                
                hourly_stats.append({
                    'hour': int(det.hour),
                    'detections': det.detection_count,
                    'total_faces': total_faces,
                    'total_masks': total_masks,
                    'total_violations': total_violations,
                    'mask_rate': round(mask_rate, 2),
                    'violation_rate': round(violation_rate, 2)
                })
            
            # Sort by hour
            hourly_stats.sort(key=lambda x: x['hour'])
            
            return hourly_stats
            
        except Exception as e:
            logger.error(f"Error getting hourly statistics: {e}")
            return []
    
    def _group_alerts_by_type(self, alerts: List[AlertModel]) -> Dict:
        """Group alerts by type"""
        grouped = {}
        for alert in alerts:
            alert_type = alert.alert_type
            if alert_type not in grouped:
                grouped[alert_type] = 0
            grouped[alert_type] += 1
        return grouped
    
    def _group_alerts_by_severity(self, alerts: List[AlertModel]) -> Dict:
        """Group alerts by severity"""
        grouped = {}
        for alert in alerts:
            severity = alert.severity
            if severity not in grouped:
                grouped[severity] = 0
            grouped[severity] += 1
        return grouped
    
    def get_trends(self, days: int = 7) -> Dict:
        """Get trend analysis for the last N days"""
        try:
            session = get_db_session()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get daily statistics
            daily_stats = session.query(
                func.date(DetectionModel.timestamp).label('date'),
                func.count(DetectionModel.id).label('detection_count'),
                func.sum(DetectionModel.face_count).label('total_faces'),
                func.sum(DetectionModel.mask_count).label('total_masks'),
                func.sum(DetectionModel.no_mask_count).label('total_violations')
            ).filter(
                and_(
                    DetectionModel.timestamp >= start_date,
                    DetectionModel.timestamp <= end_date
                )
            ).group_by(func.date(DetectionModel.timestamp)).all()
            
            trends = []
            for stat in daily_stats:
                total_faces = stat.total_faces or 0
                total_masks = stat.total_masks or 0
                total_violations = stat.total_violations or 0
                
                mask_rate = (total_masks / total_faces * 100) if total_faces > 0 else 0
                violation_rate = (total_violations / total_faces * 100) if total_faces > 0 else 0
                
                trends.append({
                    'date': stat.date.isoformat(),
                    'detections': stat.detection_count,
                    'total_faces': total_faces,
                    'total_masks': total_masks,
                    'total_violations': total_violations,
                    'mask_rate': round(mask_rate, 2),
                    'violation_rate': round(violation_rate, 2)
                })
            
            session.close()
            
            # Sort by date
            trends.sort(key=lambda x: x['date'])
            
            return {
                'period_days': days,
                'trends': trends
            }
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict:
        """Get system performance metrics"""
        try:
            session = get_db_session()
            
            # Get recent detections (last hour)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_detections = session.query(DetectionModel).filter(
                DetectionModel.timestamp >= one_hour_ago
            ).all()
            
            # Calculate processing metrics
            total_detections = len(recent_detections)
            avg_confidence = 0
            if total_detections > 0:
                avg_confidence = sum(d.confidence_score or 0 for d in recent_detections) / total_detections
            
            # Get system alerts
            recent_alerts = session.query(AlertModel).filter(
                AlertModel.timestamp >= one_hour_ago
            ).all()
            
            session.close()
            
            return {
                'last_hour': {
                    'detections': total_detections,
                    'average_confidence': round(avg_confidence, 2),
                    'alerts': len(recent_alerts)
                },
                'system_health': {
                    'database_connected': True,  # If we got here, DB is working
                    'cache_size': len(self.cache),
                    'cache_hit_rate': self._calculate_cache_hit_rate()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        # This is a simplified implementation
        # In a real system, you'd track cache hits/misses
        return 85.0  # Placeholder
    
    def clear_cache(self):
        """Clear analytics cache"""
        self.cache.clear()
        logger.info("Analytics cache cleared")
    
    def export_data(self, format: str = "json", period: str = "today") -> str:
        """Export analytics data"""
        try:
            data = self.get_analytics(period)
            
            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            elif format.lower() == "csv":
                # Convert to CSV format (simplified)
                return self._convert_to_csv(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return ""
    
    def _convert_to_csv(self, data: Dict) -> str:
        """Convert analytics data to CSV format"""
        # This is a simplified CSV conversion
        # In a real implementation, you'd use pandas or similar
        csv_lines = []
        
        # Add summary
        csv_lines.append("Metric,Value")
        for key, value in data.get('summary', {}).items():
            csv_lines.append(f"{key},{value}")
        
        return "\n".join(csv_lines)
