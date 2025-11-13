# Project Structure - CONTAFY

## Directory Organization

### Root Level
```
contafy/
├── core/                    # Django project configuration
├── empresa/                 # Main application (all business logic)
├── static/                  # Static assets (CSS, JS, images)
├── staticfiles/            # Collected static files for production
├── scripts/                # Deployment and utility scripts
├── logs/                   # Application logs
├── backups/                # Database backups
└── .github/workflows/      # CI/CD pipelines
```

### Core Module (`core/`)
Django project settings and configuration:
- `settings.py` - Main configuration (database, middleware, apps)
- `test_settings.py` - SQLite-based test configuration
- `ci_settings.py` - CI environment settings
- `test_postgres.py` - PostgreSQL test configuration
- `urls.py` - Root URL routing
- `wsgi.py` / `asgi.py` - WSGI/ASGI application entry points

### Main Application (`empresa/`)

#### Models Layer
- `models.py` - Core business models (Empresa, Usuario, Gasto, Ingreso, etc.)
- `models_aprendizaje.py` - Learning system (ModuloAprendizaje, Leccion, ProgresoUsuario)
- `models_gamificacion.py` - Gamification (Logro, Insignia, Nivel)
- `models_simulaciones.py` - Simulation scenarios (EscenarioSimulacion, SimulacionUsuario)
- `models_social.py` - Social features (Liga, Reto, Ranking)
- `models_audit.py` - Audit trail and change tracking

#### Services Layer (`empresa/services/`)
Business logic encapsulated in service classes:
- `ai_agent_service.py` - AI assistant orchestration
- `contabilidad_service.py` - Accounting operations
- `gamificacion_service.py` - XP, levels, achievements
- `simulacion_service.py` - Sandbox simulation engine
- `predicciones_service.py` - ML-based predictions
- `niif_service.py` - NIIF compliance logic
- `recommendation_service.py` - Adaptive learning recommendations
- `automation_service.py` - Automated workflows
- `social_service.py` - Social features management

#### Views Layer (`empresa/views/`)
Request handlers organized by feature:
- `autenticacion.py` - Login, registration, password reset
- `dashboard.py` - Main dashboard and home
- `contabilidad.py` - Accounting views
- `aprendizaje.py` - Learning academy views
- `ai_agent.py` - AI assistant interface
- `ventas.py`, `compras.py`, `gastos.py` - Transaction views
- `reportes_*.py` - Various report generators
- `simulaciones_api.py` - Simulation endpoints

#### API Layer (`empresa/api/`)
RESTful API endpoints:
- `views.py` - Main API views
- `serializers.py` - DRF serializers
- `urls.py` - API routing
- `contrapartidas.py` - Accounting contrapartida logic

#### Utilities (`empresa/utils/`)
- `normalizador.py` - Data normalization and validation
- `money.py` - Currency handling utilities
- `security.py` - Security helpers

#### Templates (`empresa/templates/empresa/`)
Django templates organized by feature area:
- `aprendizaje/` - Learning academy UI
- `dashboard/` - Dashboard templates
- `reportes/` - Report templates
- `auth/` - Authentication pages

#### Static Assets (`empresa/static/empresa/`)
- `js/` - JavaScript modules (aprendizaje.js, dashboard_charts.js, etc.)
- `css/` - Stylesheets

#### Tests (`empresa/tests/`)
Comprehensive test suite:
- `test_aprendizaje*.py` - Learning system tests
- `test_simulacion*.py` - Simulation tests
- `test_api_academia.py` - API tests
- `test_paso_concurrency.py` - Concurrency tests
- `test_models_aprendizaje.py` - Model tests

## Architectural Patterns

### Layered Architecture
1. **Presentation Layer**: Views and templates handle HTTP requests/responses
2. **Service Layer**: Business logic isolated in service classes
3. **Data Layer**: Django ORM models with database abstraction
4. **API Layer**: RESTful endpoints for mobile/external access

### Key Design Patterns

#### Service Pattern
Business logic encapsulated in dedicated service classes:
```python
# Services handle complex operations
GamificacionService.otorgar_xp(usuario, cantidad, razon)
SimulacionService.ejecutar_simulacion(escenario, usuario)
```

#### Repository Pattern (via Django ORM)
Models act as repositories with custom managers and querysets.

#### Middleware Pattern
Custom middleware for:
- Current user context (`CurrentUserMiddleware`)
- Security headers (`SecurityMiddleware`)

#### Sandbox Pattern
Isolated execution environment for simulations with transaction rollback.

### Component Relationships

```
Views → Services → Models → Database
  ↓         ↓
Templates  Utils
  ↓
Static Assets (JS/CSS)
```

### Multi-Tenancy
- Each `Usuario` belongs to one or more `Empresa` instances
- Data isolation via foreign key relationships
- Row-level security through queryset filtering

### Authentication Flow
1. User logs in via `autenticacion.py`
2. JWT token issued via `rest_framework_simplejwt`
3. Token validated on API requests
4. Session-based auth for web interface

### Learning System Architecture
```
ModuloAprendizaje (Module)
  └── Leccion (Lesson)
        ├── pasos (JSON field with steps)
        └── ProgresoUsuario (User progress tracking)
              └── PasoCompletado (Individual step completion)
```

### Simulation System
```
TipoSimulacion (Type: venta, receta, servicio)
  └── EscenarioSimulacion (Predefined scenario)
        └── SimulacionUsuario (User's simulation instance)
              ├── datos_iniciales (Starting state)
              ├── datos_finales (End state)
              └── puntos_obtenidos (Score)
```

## Configuration Management
- Environment variables via `django-environ`
- `.env` file for local development
- Platform-specific settings (Heroku, Render) detected automatically
- Separate settings modules for testing (SQLite) and CI (PostgreSQL)
