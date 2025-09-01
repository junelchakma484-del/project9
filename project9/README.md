# Face Mask Detection System

A comprehensive AI-powered face mask detection system with real-time monitoring, reporting, and alerting capabilities.

## Features

- **AI-Powered Detection**: Real-time face mask detection using OpenCV and TensorFlow
- **Multi-Camera Support**: RPI cameras and IP cameras with RTSP streams
- **Optimized Performance**: 50% faster processing with message queue architecture
- **Multithreading**: Parallel processing of video streams, analysis, and alerts
- **Real-time Monitoring**: Web dashboard with live video feeds and statistics
- **Database Integration**: PostgreSQL for data persistence and analytics
- **Grafana Dashboards**: Advanced monitoring and reporting
- **Telegram Notifications**: Instant alerts for violations
- **MQTT Integration**: IoT device control and communication
- **RESTful API**: Complete backend API for frontend integration

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IP Cameras    │    │   RPI Cameras   │    │   Web Interface │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Video Stream Manager   │
                    │    (Message Queue)        │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Face Detection Engine   │
                    │   (Multithreaded)         │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   PostgreSQL DB   │  │   Telegram Bot    │  │   Grafana Dash    │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Node.js (for frontend)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd face-mask-detection-system
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

5. **Start the system**
   ```bash
   # Start backend services
   python app.py
   
   # Start frontend (in another terminal)
   cd frontend && npm install && npm start
   ```

## Configuration

### Camera Configuration

Edit `config/cameras.json`:
```json
{
  "cameras": [
    {
      "id": "camera_1",
      "name": "Main Entrance",
      "type": "ip",
      "url": "rtsp://username:password@192.168.1.100:554/stream",
      "location": "Building A - Entrance"
    },
    {
      "id": "camera_2", 
      "name": "RPI Camera",
      "type": "rpi",
      "device_id": 0,
      "location": "Building B - Lab"
    }
  ]
}
```

### Telegram Bot Setup

1. Create a bot via @BotFather
2. Add bot token to `.env`
3. Configure chat IDs for notifications

### Grafana Setup

1. Install Grafana
2. Import dashboard from `grafana/dashboard.json`
3. Configure PostgreSQL data source

## API Documentation

### Endpoints

- `GET /api/status` - System status
- `GET /api/cameras` - List all cameras
- `GET /api/detections` - Get detection history
- `POST /api/cameras/{id}/control` - Camera control
- `GET /api/analytics` - Analytics data

### WebSocket Events

- `detection_update` - Real-time detection updates
- `camera_status` - Camera status changes
- `alert` - New alerts

## Performance Optimization

- **Message Queue**: Redis-based queue for video frame processing
- **Multithreading**: Parallel processing of multiple video streams
- **GPU Acceleration**: CUDA support for faster inference
- **Frame Skipping**: Configurable frame processing rate
- **Memory Management**: Efficient buffer management

## Monitoring & Alerts

- **Real-time Dashboard**: Live video feeds and statistics
- **Grafana Dashboards**: Historical data and trends
- **Telegram Alerts**: Instant notifications for violations
- **Email Reports**: Daily/weekly summary reports
- **SMS Alerts**: Critical violation notifications

## Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Production Setup

1. Use Gunicorn for WSGI server
2. Configure Nginx as reverse proxy
3. Set up SSL certificates
4. Configure monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:
- Create an issue on GitHub
- Contact: support@facemaskdetection.com
