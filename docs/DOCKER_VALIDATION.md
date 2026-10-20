# Docker Validation Guide

## Purpose
This document outlines the validation procedures and best practices for ensuring the reliability, security, and performance of Docker containers in the EnCompliance system.

## Validation Procedures

### 1. Container Health Checks
- **Purpose**: Ensure containers are running and healthy
- **Implementation**:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  ```

### 2. Security Scanning
- **Purpose**: Identify vulnerabilities in container images
- **Tools**:
  - Trivy
  - Docker Scout
  - Snyk
- **Frequency**: Before deployment and weekly

### 3. Performance Testing
- **Purpose**: Ensure containers meet performance requirements
- **Metrics**:
  - Response time
  - Resource usage
  - Memory consumption
  - CPU utilization

### 4. Network Validation
- **Purpose**: Verify container networking
- **Checks**:
  - Inter-container communication
  - Port exposure
  - Network isolation
  - DNS resolution

### 5. Volume Validation
- **Purpose**: Ensure data persistence
- **Checks**:
  - Volume mounting
  - Data persistence
  - Backup procedures
  - Restore procedures

## Best Practices

### 1. Image Optimization
- Use multi-stage builds
- Minimize layer count
- Remove unnecessary files
- Use .dockerignore

### 2. Security
- Run as non-root user
- Scan for vulnerabilities
- Use secrets management
- Implement network policies

### 3. Monitoring
- Implement health checks
- Set up logging
- Configure alerts
- Track resource usage

### 4. Maintenance
- Regular updates
- Version control
- Documentation
- Backup procedures

## Validation Checklist

### Pre-deployment
- [ ] Security scan completed
- [ ] Performance tests passed
- [ ] Health checks implemented
- [ ] Documentation updated
- [ ] Backup procedures tested

### Post-deployment
- [ ] Container health verified
- [ ] Network connectivity confirmed
- [ ] Volume persistence checked
- [ ] Logging configured
- [ ] Monitoring set up

## Troubleshooting

### Common Issues
1. **Container won't start**
   - Check logs
   - Verify dependencies
   - Check resource limits

2. **Network issues**
   - Verify network configuration
   - Check DNS settings
   - Test connectivity

3. **Volume problems**
   - Check permissions
   - Verify mount points
   - Test backup/restore

## Tools and Resources

### Validation Tools
- Docker Compose
- Trivy
- Docker Scout
- Prometheus
- Grafana

### Documentation
- Docker documentation
- Security guidelines
- Performance benchmarks
- Troubleshooting guides

# Docker Setup Validation

This document provides instructions on how to validate the Docker setup manually.

## Prerequisites

Before validating the Docker setup, ensure:

1. Docker and Docker Compose are installed and running
2. You have created the required storage directories:
   ```bash
   mkdir -p storage/encompliance-documents
   ```
3. You have a `.env` file with the required environment variables

## Validating the Dockerfiles

### Backend Dockerfile Validation

You can validate the backend Dockerfile with:

```bash
cd encompliance-backend
docker build -t encompliance-backend .
```

Expected result: The build should complete successfully without errors.

To run the container:

```bash
docker run -p 8000:8000 -v $(pwd)/../storage:/storage -e PDF_STORAGE_PATH=/storage/encompliance-documents --env-file ../.env encompliance-backend
```

You should see the FastAPI server start up. To verify it's working, open http://localhost:8000/docs in your browser.

### Frontend Dockerfile Validation

Validate the frontend Dockerfile with:

```bash
cd encompliance-frontend
docker build -t encompliance-frontend .
```

Expected result: The build should complete successfully without errors.

To run the container:

```bash
docker run -p 80:80 encompliance-frontend
```

You should be able to access the frontend at http://localhost

### Docker Compose Validation

Validate the full stack with:

```bash
# Make sure you're in the project root
cd /path/to/encompliance-project

# Create a .env file from the example
cp docs/env-example .env

# Edit .env to add your OpenAI API key
# Then run docker-compose
docker-compose up
```

## Validation Tests

After starting the containers, perform these tests to ensure everything is working:

### 1. Frontend Accessibility
```bash
curl -s http://localhost | head -n 10
```
This should return the EnCompliance HTML content, not the default Nginx page.

### 2. Backend API Accessibility
```bash
curl -s http://localhost:8000/docs | head -n 10
```
This should return the Swagger UI documentation.

### 3. Database Connection
```bash
docker-compose exec backend python -c "import socket; s = socket.socket(); print(s.connect_ex(('db', 5432)))"
```
A result of '0' indicates a successful connection.

### 4. Inter-container Communication
```bash
docker-compose exec frontend wget -q -O- --timeout=2 backend:8000/docs 2>/dev/null | head -n 5
```
This tests whether the frontend container can communicate with the backend.

## Troubleshooting Docker Daemon

If you get the error "Cannot connect to the Docker daemon", try:

1. On macOS:
   - Open Docker Desktop application
   - Wait for it to start completely
   - Try running the docker commands again

2. On Linux:
   - Check if the Docker service is running: `systemctl status docker`
   - Start it if needed: `sudo systemctl start docker`
   - Add your user to the docker group if needed: `sudo usermod -aG docker $USER`

3. On Windows:
   - Open Docker Desktop application
   - Check if WSL 2 is configured correctly
   - Restart Docker Desktop if needed

## Common Issues and Solutions

### Backend Starts But Isn't Accessible
- Check if any errors appear in the logs: `docker-compose logs backend`
- Verify the DATABASE_URL environment variable is correct
- Ensure the storage directories have correct permissions

### Frontend Shows Default Nginx Page
- Make sure the build process is completing correctly: `docker-compose build --no-cache frontend`
- Check if index.html exists in the dist directory
- Verify the nginx.conf file is correctly configured

### Missing Dependencies
- If the backend logs show missing Python packages, add them to the Dockerfile:
  ```
  RUN pip install --no-cache-dir package-name
  ```
- Rebuild the container: `docker-compose build --no-cache backend`

## Manual Validation Without Docker

If Docker is not available, you can still validate the setup manually:

### Backend
```bash
cd encompliance-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install emails  # Additional dependency that might be missing
python run.py
```

### Frontend
```bash
cd encompliance-frontend
npm install
npm run dev
``` 