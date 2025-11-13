# Technology Stack - CONTAFY

## Programming Languages
- **Python 3.11+** - Primary backend language
- **JavaScript (ES6+)** - Frontend interactivity
- **HTML5/CSS3** - UI markup and styling
- **SQL** - Database queries (via Django ORM)

## Core Framework
- **Django 5.2.3** - Web framework
  - MVT (Model-View-Template) architecture
  - Built-in admin interface
  - ORM for database abstraction
  - Security features (CSRF, XSS protection)

## Key Dependencies

### Backend Frameworks & Libraries
```
Django==5.2.3                          # Web framework
djangorestframework==3.16.0            # REST API framework
djangorestframework_simplejwt==5.5.0   # JWT authentication
django-environ==0.12.0                 # Environment variable management
django-jazzmin==3.0.0                  # Admin UI theme
gunicorn==21.2.0                       # WSGI HTTP server
psycopg2-binary==2.9.10               # PostgreSQL adapter
whitenoise==6.6.0                      # Static file serving
dj-database-url==2.1.0                # Database URL parsing
```

### Data Processing & Analysis
```
pandas==2.3.1                          # Data manipulation
numpy                                  # Numerical computing (pandas dependency)
```

### File Generation & Export
```
openpyxl==3.1.5                       # Excel file handling
xlsxwriter==3.2.5                     # Excel file generation
reportlab==4.4.2                      # PDF generation
matplotlib==3.10.3                    # Chart generation
```

### Utilities
```
pillow==11.3.0                        # Image processing
requests==2.32.4                      # HTTP client
pytz==2025.2                          # Timezone handling
```

## Database Systems

### Development
- **SQLite 3** - Default for local development
  - File: `contafy_sistema.db`
  - Configuration: `ATOMIC_REQUESTS=True`, `timeout=20`

### Testing
- **SQLite 3** - Fast test execution (`core.test_settings`)
- **PostgreSQL** - CI/CD and concurrency tests (`core.ci_settings`)

### Production
- **PostgreSQL 12+** - Primary production database
  - Connection pooling: `CONN_MAX_AGE=600`
  - Atomic transactions enabled
  - Configured via `DATABASE_URL` environment variable

## Frontend Technologies

### UI Framework
- **Bootstrap 5** - Responsive CSS framework
- **AdminLTE** - Admin dashboard template
- **Jazzmin** - Django admin customization

### JavaScript Libraries
- **Vanilla JS** - Core interactivity (no heavy framework)
- **Chart.js** (via matplotlib backend) - Data visualization
- **Bootstrap Toasts** - User notifications

### Static Asset Management
- **WhiteNoise** - Static file serving in production
- **Compressed static storage** - Gzip compression for performance

## API & Authentication

### REST API
- **Django REST Framework (DRF)** - API framework
  - JSON serialization
  - Pagination (20 items per page)
  - Browsable API interface

### Authentication Methods
- **JWT (JSON Web Tokens)** - API authentication
  - Access token: 2 hours lifetime
  - Refresh token: 7 days lifetime
  - Token rotation enabled
- **Session-based** - Web interface authentication
  - 24-hour session lifetime
  - Database-backed sessions

## External Services & APIs

### AI/ML Services
- **OpenAI API** - GPT models for AI assistant
- **Google Gemini API** - Alternative AI provider
- Configuration via `OPENAI_API_KEY`, `GEMINI_API_KEY`

### Communication
- **SMTP (Gmail)** - Email notifications
  - TLS encryption on port 587
- **Twilio** - WhatsApp integration (optional)

## Development Tools

### Code Quality
- **Flake8** - Python linting (`.flake8` config)
- **Pre-commit hooks** - Automated checks (`.pre-commit-config.yaml`)

### Testing
- **Django Test Framework** - Unit and integration tests
- **pytest** (compatible) - Alternative test runner
- Test database: SQLite for speed, PostgreSQL for accuracy

### Version Control
- **Git** - Source control
- **GitHub Actions** - CI/CD pipelines
  - `.github/workflows/test.yml` - Main test suite
  - `.github/workflows/test-postgres.yml` - PostgreSQL tests
  - `.github/workflows/ci.yml` - Continuous integration

## Deployment Platforms

### Supported Platforms
- **Heroku** - PaaS deployment
  - `Procfile` for process definition
  - `runtime.txt` specifies Python version
- **Render** - Alternative PaaS
  - `render.yaml` for configuration
  - `build.sh` for build process
- **Docker** - Containerized deployment
  - `Dockerfile` and `docker-compose.yml`
  - PostgreSQL service in compose

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Running the Application
```bash
# Development server
python manage.py runserver

# Production server (Gunicorn)
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Testing
```bash
# Run all tests (SQLite)
set DJANGO_SETTINGS_MODULE=core.test_settings
python manage.py test

# Run specific test module
python manage.py test empresa.tests.test_aprendizaje

# Run with PostgreSQL (requires Docker)
docker-compose -f docker-compose.postgres.yml up -d
set DJANGO_SETTINGS_MODULE=core.ci_settings
python manage.py test
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Database shell
python manage.py dbshell

# Backup database (custom script)
python backup_manager.py
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### Utilities
```bash
# Django shell
python manage.py shell

# Create demo content
python manage.py crear_contenido_demo

# Generate invitation codes
python crear_codigos_invitacion.py
```

## Environment Variables

### Required
- `SECRET_KEY` - Django secret key (auto-generated in dev)
- `DATABASE_URL` - PostgreSQL connection string (production)

### Optional
- `DEBUG` - Enable debug mode (default: False)
- `ALLOWED_HOSTS` - Comma-separated host list
- `OPENAI_API_KEY` - OpenAI API access
- `GEMINI_API_KEY` - Google Gemini API access
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password
- `TWILIO_ACCOUNT_SID` - Twilio account ID
- `TWILIO_AUTH_TOKEN` - Twilio auth token

## Performance Optimizations
- Database connection pooling (600s max age)
- Atomic transactions for data integrity
- Local memory caching (300s timeout, 1000 max entries)
- Static file compression via WhiteNoise
- Query optimization via `select_related` and `prefetch_related`

## Security Features
- CSRF protection enabled
- XSS filtering
- Content type sniffing prevention
- Secure cookies in production
- HSTS headers (31536000s)
- SQL injection prevention via ORM
- Password validation (length, complexity, common passwords)
