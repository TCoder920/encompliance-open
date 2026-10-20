# Docker Configuration Guide

## Purpose
This document provides comprehensive documentation for the Docker configuration of the EnCompliance system, including container setup, networking, and best practices for deployment.

## Container Architecture

### Backend Container
- **Purpose**: Hosts the Python FastAPI application
- **Base Image**: Python 3.10-slim
- **Ports**: 8000 (API)
- **Volumes**:
  - `/app`: Application code
  - `/storage`: Document storage
  - `/app/venv`: Virtual environment (excluded)
  - `/app/__pycache__`: Python cache (excluded)
- **Environment Variables**:
  - `DATABASE_URL`: PostgreSQL connection string
  - `PORT`: API port
  - `DEBUG`: Debug mode flag
  - `OPENAI_API_KEY`: OpenAI API key
  - `PDF_STORAGE_PATH`: Document storage path

### Frontend Container
- **Purpose**: Serves the Vue.js application
- **Base Image**: Node 18-alpine
- **Ports**: 80 (Web interface)
- **Volumes**:
  - `/etc/nginx/conf.d/default.conf`: Nginx configuration
- **Dependencies**: Backend service

### Database Container
- **Purpose**: PostgreSQL database
- **Base Image**: postgres:15-alpine
- **Ports**: 5432 (Database)
- **Volumes**:
  - `postgres_data`: Persistent database storage
- **Environment Variables**:
  - `POSTGRES_PASSWORD`: Database password
  - `POSTGRES_USER`: Database user
  - `POSTGRES_DB`: Database name

## Network Configuration
- **Network Name**: encompliance-network
- **Driver**: bridge
- **Purpose**: Isolated network for inter-container communication

## Volume Management
- **postgres_data**: Persistent storage for PostgreSQL database
- **Purpose**: Ensure data persistence across container restarts

## Best Practices
1. **Security**:
   - Use non-root users in containers
   - Implement proper secrets management
   - Regular security scanning
   - Network isolation

2. **Performance**:
   - Resource limits and requests
   - Proper caching strategies
   - Optimized base images

3. **Maintenance**:
   - Regular image updates
   - Health checks
   - Logging and monitoring
   - Backup strategies

## Deployment
1. **Development**:
   ```bash
   docker-compose up --build
   ```

2. **Production**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Troubleshooting
- Container logs: `docker-compose logs [service]`
- Container status: `docker-compose ps`
- Container shell: `docker-compose exec [service] sh`

## Monitoring
- Container health: `docker-compose ps`
- Resource usage: `docker stats`
- Logs: `docker-compose logs -f`

# Docker Setup for EnCompliance Project

This document explains how to run the EnCompliance project using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- OpenAI API Key (for AI features)

## Configuration

1. Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

2. Make sure storage directories exist:

```bash
mkdir -p storage/encompliance-documents
```

## Running the Application

To run the full stack:

```bash
docker-compose up
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend on port 80

## Development Mode

For development with hot-reloading:

### Backend Development

```bash
# Run just the database
docker-compose up db

# Then run the backend locally
cd encompliance-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install emails  # Additional dependency
python run.py
```

### Frontend Development

```bash
# Run the backend services
docker-compose up backend db

# Then run the frontend locally
cd encompliance-frontend
npm install
npm run dev
```

## Building Individual Components

To build and run individual components:

```bash
# Build and run backend only
docker-compose up --build backend

# Build and run frontend only
docker-compose up --build frontend
```

## Database Access

The PostgreSQL database is accessible at `localhost:5432` with:
- Username: postgres
- Password: postgres
- Database: encompliance

## Container Management

```bash
# View running containers
docker-compose ps

# Stop all containers
docker-compose down

# Stop and remove volumes (will delete database data)
docker-compose down -v

# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## Troubleshooting

### Backend Connectivity Issues
If the frontend cannot connect to the backend, ensure the API URL is correctly configured in the frontend environment.

### Database Migration Issues
If database migrations aren't applied automatically, you can run:

```bash
docker-compose exec backend python -m alembic upgrade head
```

### Missing Dependencies
If you encounter a `ModuleNotFoundError` for packages like 'emails', you may need to rebuild the backend container:

```bash
docker-compose build --no-cache backend
docker-compose up -d
```

### Frontend Static Files Issues
If the frontend shows a "403 Forbidden" error or the default Nginx welcome page, check:

1. That the index.html file exists in the dist directory
2. That the Docker build process correctly copies the files
3. That the Nginx configuration is correct

You can rebuild the frontend without using cache:

```bash
docker-compose build --no-cache frontend
docker-compose up -d
```

### Container Communication
To verify that containers can communicate with each other:

```bash
# Check if backend can connect to database
docker-compose exec backend python -c "import socket; s = socket.socket(); print(s.connect_ex(('db', 5432)))"
# Result of 0 means successful connection

# Check if frontend can connect to backend
docker-compose exec frontend wget -q -O- --timeout=2 backend:8000/docs 2>/dev/null | head -n 5
```

## Recent Changes and Improvements

1. Added storage directory mounting for document storage
2. Fixed permissions for storage access
3. Added missing 'emails' package to backend container
4. Improved Nginx configuration for serving the frontend application
5. Added file cleanup step to frontend Dockerfile to remove default Nginx static assets 