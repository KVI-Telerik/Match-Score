 Tennis Tournament Platform 🎾

A comprehensive web application for managing tennis tournaments, matches, and player profiles.

## 📋 Features

### 🏆 Tournament Management
* Create and manage knockout and league tournaments
* Automatic match generation based on tournament format
* Real-time tournament progression
* Tournament standings and statistics
* Prize pool management

### ⚔️ Match System
* Support for both time-limited and score-limited matches
* Real-time score tracking
* Match history and statistics
* Automated match scheduling

### 👥 Player Profiles
* Detailed player statistics
* Win/loss/draw tracking
* Tournament participation history
* Club affiliations
* Country representation

### 👤 User Management
* Role-based access control (Admin, Director, Player)
* Profile claiming system
* Email notifications for match participation and status updates
* Session management with activity tracking

## 🛠️ Technical Stack

### Backend
* FastAPI framework
* PostgreSQL database
* AsyncPG for asynchronous database operations
* Pydantic for data validation
* JWT for authentication
* Mailjet for email notifications

### Frontend
* Jinja2 templating engine
* Bootstrap for responsive design
* Custom CSS for tennis-themed styling

### Security Features
* Session-based authentication with middleware
* Rate limiting for API endpoints
* Input sanitization for all user inputs
* CSRF protection for form submissions
* Secure password hashing with bcrypt
* HTTP-only cookies for token storage

### Containerization
* Docker support for easy deployment
* Docker Compose for service orchestration
* Containerized PostgreSQL database
* Isolated development environment

## 🏗️ Architecture

### N-Layer Architecture
1. **Presentation Layer**
   * Web Routes (`/routers/web/`)
   * API Routes (`/routers/api/`)
   * Templates (`/templates/`)

2. **Service Layer** (`/services/`)
   * Business logic implementation
   * Data processing
   * External service integration

3. **Data Access Layer**
   * Database models
   * Query execution
   * Data validation

### Key Components
* Rate Limiter middleware for API protection
* Input Sanitization for XSS prevention
* CSRF token generation and validation
* Session management for user tracking
* Email notification service
* Custom template engine configuration

## 🚀 Getting Started

### Using Docker (Recommended)

1. Clone the repository

2. Request API keys from project maintainers
   * Email notification service keys
   * Database access credentials
   * JWT secret keys

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Manual Setup

1. Clone the repository

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Request and configure environment variables:
```bash
SECRET_KEY=your_secret_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_DATABASE=your_db_name
MJ_APIKEY_PUBLIC=your_mailjet_public_key
MJ_APIKEY_PRIVATE=your_mailjet_private_key
```

> **Note**: API keys and credentials are not publicly available and must be requested from the project maintainers.

5. Run database migrations
6. Start the application:
```bash
uvicorn main:app --reload
```

## 📚 API Documentation

Access the interactive API documentation at:
* Swagger UI: `/docs`
* ReDoc: `/redoc`

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Test coverage includes:
* Unit tests for services
* Integration tests for API endpoints
* Security feature validation
* Database operation testing

## 🐳 Docker Compose Services

```yaml
services:
  - web: FastAPI application
  - db: PostgreSQL database
```

Environment variables for Docker are managed through `.env` file (request from maintainers).


## 📧 Contact

For API keys and credentials, please contact the project maintainers at [tennisdaddy.help@mail.bg].

