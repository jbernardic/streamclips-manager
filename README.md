# StreamClips Manager

A FastAPI-based management system for deploying and monitoring multiple StreamClips instances across different servers. StreamClips Manager automatically creates highlight clips from live streams by detecting chat activity surges.

## Features

- **Multi-Instance Management**: Deploy and monitor StreamClips processes across multiple Hetzner Cloud servers
- **Web Dashboard**: FastAPI-powered admin interface for managing streamers and configurations
- **Automated Deployment**: GitHub Actions workflow for containerized deployment
- **Chat Surge Detection**: Monitor chat activity and automatically create clips during high engagement moments
- **Remote Storage**: Upload clips to remote servers via SSH/SCP
- **Process Monitoring**: Track process health and automatically restart failed instances
- **Configurable Parameters**: Adjust clip duration, surge thresholds, and monitoring settings

## Architecture

### Core Components

- **FastAPI Application**: Web API and admin interface (`app/`)
- **StreamClips Library**: Core clipping functionality (`streamclips/`)
- **Database Models**: PostgreSQL models for streamers, processes, and logs
- **Process Management**: Distributed process orchestration across instances
- **Scheduler**: Background tasks for health monitoring and cleanup

### Database Schema

- **Streamers**: Stream URLs and configuration
- **Instances**: Server hostnames and capacity limits  
- **Processes**: Active StreamClips processes with PIDs and health status
- **Configs**: Global settings for clip parameters
- **Logs**: System and process logging

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Docker (for deployment)
- Hetzner Cloud account (for multi-instance deployment)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd streamclips-manager
   pip install -r requirements.txt
   ```

2. **Environment variables**:
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost/db
   SECRET_KEY=your-secret-key
   ADMIN_PASSWORD=admin-password
   INSTANCE_ID=instance-name
   ```

3. **Database migration**:
   ```bash
   alembic upgrade head
   ```

4. **Run application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

```bash
docker run -d \
  --name streamclips-manager \
  -p 8000:8000 \
  -v streamclips-manager_data:/app/data \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  -e ADMIN_PASSWORD=... \
  -e INSTANCE_ID=instance-name \
  ghcr.io/your-repo/streamclips-manager:latest
```

### Remote Storage (optional)

Configure remote storage env variables for clips:

```bash
STORAGE_SERVER_HOST=user@server.com
STORAGE_SERVER_PASSWORD=password  # or use SSH keys
STORAGE_SERVER_PATH=/path/to/data
```

## Configuration

### Stream Configuration

Default parameters can be adjusted via the admin interface:

- `clip_duration`: Video clip length in seconds (default: 60)
- `window_timespan`: Chat analysis window in seconds (default: 30)  
- `sample_interval`: Chat sampling rate (default: 1)
- `baseline_duration`: Baseline calculation period (default: 180)
- `surge_threshold`: Activity surge multiplier (default: 2.0)

## API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `POST /auth/logout` - Logout

### Streamers
- `GET /streamers` - List all streamers
- `POST /streamers` - Create new streamer
- `PUT /streamers/{id}` - Update streamer
- `DELETE /streamers/{id}` - Delete streamer

### Stream Clips
- `GET /stream-clips` - List active processes
- `POST /stream-clips/{streamer_id}/start` - Start clipping process
- `POST /stream-clips/{process_id}/stop` - Stop process

## Development

### Testing

```bash
pytest tests/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration  
alembic upgrade head
```
