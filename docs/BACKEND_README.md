# EnCompliance Backend

## Purpose
The backend application serves as the core of the EnCompliance system, providing RESTful API endpoints, database management, and business logic for compliance tracking and document management. It is built with Python and Flask, offering robust security and scalability.

## Features
- RESTful API endpoints
- Database management with SQLAlchemy
- Document processing and storage
- Authentication and authorization
- Integration with external services
- Automated testing and coverage reporting

## Setup Instructions
1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize database:
   ```bash
   python init_db.py
   ```

4. Run development server:
   ```bash
   python run.py
   ```

5. Run tests:
   ```bash
   pytest
   ```

## Configuration
- Environment variables are managed through `.env` files
- Database configuration in `alembic.ini`
- API documentation generated with OpenAPI/Swagger 