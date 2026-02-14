# CONTAFY - Technology Stack

## Backend Framework
- **Django 5.2.3** - Web framework
- **Python 3.10+** - Programming language
- **Django REST Framework 3.16.0** - API development
- **djangorestframework_simplejwt 5.5.0** - JWT authentication

## Database
- **PostgreSQL** - Production database (via psycopg2-binary 2.9.10)
- **SQLite3** - Development database
- **dj-database-url 2.1.0** - Database URL parsing

## Authentication & Security
- **JWT (JSON Web Tokens)** - API authentication
- **Django Auth** - User authentication
- **django-environ 0.12.0** - Environment variable management
- **WhiteNoise 6.6.0** - Static file serving

## Admin Interface
- **django-jazzmin 3.0.0** - Professional admin theme

## Data Processing & Analysis
- **pandas 2.3.1** - Data manipulation
- **openpyxl 3.1.5** - Excel file handling
- **xlsxwriter 3.2.5** - Excel generation
- **reportlab 4.4.2** - PDF generation
- **matplotlib 3.10.3** - Data visualization

## Deployment
- **gunicorn 21.2.0** - WSGI HTTP server
- **Heroku** - Cloud platform (legacy)
- **Render** - Cloud platform (current)
- **Docker** - Containerization

## Development Tools
- **Black 88** - Code formatting (line-length: 88)
- **isort** - Import sorting (profile: black)
- **pytest** - Testing framework
- **flake8** - Linting

## Additional Libraries
- **Pillow 11.3.0** - Image processing
- **requests 2.32.4** - HTTP client
- **pytz 2025.2** - Timezone handling

## Build & Deployment Commands

### Local Development
```bash
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

### Testing
```bash
pytest
python manage.py test
```

### Production Deployment
```bash
# Render
git push origin main  # Triggers automatic deployment

# Manual
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

## Environment Variables
- `DEBUG` - Debug mode (bool, default: False)
- `SECRET_KEY` - Django secret key (required in production)
- `ALLOWED_HOSTS` - Comma-separated allowed hosts
- `DATABASE_URL` - PostgreSQL connection string
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - SMTP config
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `GEMINI_API_KEY` - Google Gemini API key
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` - WhatsApp integration
- `RENDER_EXTERNAL_URL` - Render deployment URL

## Configuration Highlights

### Security Settings
- CSRF protection with SameSite=Lax
- HTTPS redirect in production
- HSTS enabled (31536000 seconds)
- XSS and clickjacking protection
- Secure session cookies

### Database Configuration
- Atomic requests enabled
- Connection pooling (CONN_MAX_AGE: 600)
- Health checks enabled

### Caching
- Local memory cache (LocMemCache)
- 300-second timeout
- 1000 max entries

### Session Management
- Database-backed sessions
- 24-hour session age
- Save on every request
- Persistent across browser close

### Logging
- Console output for production
- INFO level logging
- Separate loggers for Django and empresa app

### Regional Settings
- Language: Spanish (es)
- Timezone: America/Guayaquil (Ecuador)
- Currency: USD ($)
- IVA Rate: 15% (Ecuador standard)

## API Configuration
- JWT token lifetime: 2 hours
- Refresh token lifetime: 7 days
- Token rotation enabled
- Pagination: 20 items per page
- Default renderers: JSON and Browsable API

## File Storage
- Static files: `/staticfiles`
- Media files: Configurable via MEDIA_ROOT
- WhiteNoise compression enabled in production
