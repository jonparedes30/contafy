# CONTAFY - Project Structure

## Directory Organization

### Core Application (`/core`)
- `settings.py` - Main Django configuration with environment-based setup
- `urls.py` - Root URL routing
- `wsgi.py` - WSGI application entry point
- `asgi.py` - ASGI application entry point
- `ci_settings.py`, `dev_settings.py`, `test_settings.py` - Environment-specific configs

### Main App (`/empresa`)
The primary Django app containing all business logic:

#### Models (`models.py`)
- **User & Company**: `Usuario`, `Empresa`, `CodigoInvitacion`
- **Transactions**: `Venta`, `Compra`, `Gasto`, `Capital`
- **Accounting**: `MovimientoContable`, `CuentaContable`
- **Receivables/Payables**: `CuentaPorCobrar`, `CuentaPorPagar`, `PagoCuentaPorCobrar`, `PagoCuentaPorPagar`
- **Inventory**: `Producto`, `MovimientoInventario`, `CategoriaProducto`
- **Manufacturing**: `MateriaPrima`, `ProductoManufacturado`, `RecetaProduccion`, `OrdenProduccion`, `ConsumoMateriaPrima`
- **Services**: `TipoServicio`, `MaterialServicio`
- **NIIF 15**: `ContratoVenta`, `ObligacionDesempeno`
- **Financial**: `MetaFinanciera`, `HistorialMeta`, `AlertaMeta`, `BenchmarkingSectorial`
- **Support**: `SolicitudAyuda`, `ConversacionSoporte`, `MensajeSoporte`
- **Permissions**: `PoderEmpleado`

#### Services (`/services`)
Centralized business logic:
- `contabilidad_service.py` - Double-entry bookkeeping and journal entries
- `ai_agent_service.py` - AI-powered command processing
- `ai_comandos_service.py` - Command parsing and execution
- `categorizador.py` - Automatic expense categorization
- `niif_service.py` - NIIF compliance calculations
- `reportes_niif_service.py` - NIIF-compliant financial reports
- `benchmarking_real_service.py` - Sector benchmarking analysis
- `predicciones_service.py` - Financial forecasting
- `recommendation_service.py` - Business recommendations
- `valuacion_service.py` - Asset valuation
- `ml_service.py` - Machine learning models
- `conversational_ai.py` - Natural language processing
- `workflows_ia.py` - AI workflow orchestration

#### Views (`/views`)
Organized by feature:
- `dashboard.py` - Main dashboard and analytics
- `ai_dashboard.py` - AI-powered insights dashboard
- `ai_agent.py` - AI agent interface
- `ai_comandos.py` - Command processing UI
- `ai_reports.py` - AI-generated reports
- `ventas.py` - Sales management
- `compras.py` - Purchase management
- `gastos.py` - Expense tracking
- `capital.py` - Capital management
- `contabilidad.py` - Accounting interface
- `cuentas_contables.py` - Chart of accounts
- `inventario.py` - Inventory management
- `productos.py` - Product catalog
- `manufactura.py` - Manufacturing operations
- `servicios.py` - Service management
- `metas.py` - Financial goals
- `niif_compliance.py` - NIIF compliance reporting
- `exportaciones.py` - Data export functionality
- `api.py`, `api_comercio.py`, `api_movil.py` - REST API endpoints

#### API (`/api`)
- `views.py` - API view implementations
- `serializers.py` - DRF serializers
- `urls.py` - API routing
- `contrapartidas.py` - Counterparty management

#### Templates (`/templates/empresa`)
HTML templates organized by feature with breadcrumb support

#### Static Files (`/static/empresa`)
- `css/` - Stylesheets
- `js/` - JavaScript (barcode scanner, voice commands, dashboard charts)

#### Utilities (`/utils`)
- `money.py` - Currency and decimal handling
- `normalizador.py` - Data normalization for benchmarking
- `security.py` - Security utilities

#### Template Tags (`/templatetags`)
- `currency_filters.py` - Currency formatting
- `custom_filters.py` - Custom template filters
- `empresa_filters.py` - Business-specific filters

#### Tests (`/tests`)
- `test_asiento_audit.py` - Accounting entry tests
- `test_presenter.py` - Presenter logic tests
- `test_recommendation_service.py` - Recommendation engine tests
- `test_template_rendering.py` - Template rendering tests

#### Middleware (`middleware.py`)
- `CurrentUserMiddleware` - Tracks current user for audit fields
- `EmpresaValidationMiddleware` - Validates company context
- `SecurityMiddleware` - Security headers and CSRF handling

#### Other Key Files
- `admin.py` - Django admin customization
- `forms.py` - Django forms for data entry
- `serializers.py` - DRF serializers
- `signals.py` - Django signals for automation
- `tasks.py` - Celery tasks (if async processing)
- `decorators.py` - Custom decorators
- `validators.py` - Custom validators
- `context_processors.py` - Template context processors

### Static Files (`/static` and `/staticfiles`)
- Admin and REST Framework assets
- Jazzmin theme for admin interface
- Bootstrap, FontAwesome, Select2 vendor libraries
- Custom JavaScript for barcode scanning and voice commands
- Service worker for PWA support

### Database
- `db.sqlite3` - Development SQLite database
- PostgreSQL in production (via DATABASE_URL)

### Configuration Files
- `.env` - Environment variables (not in repo)
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Black and isort configuration
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Multi-container setup
- `Procfile` - Heroku deployment
- `render.yaml` - Render deployment config

### Documentation
- `README.md` - Project overview
- `_REVISION_DOCS/` - Detailed implementation documentation
- Various analysis and implementation guides

## Architectural Patterns

### Layered Architecture
1. **Presentation Layer**: Views and templates
2. **API Layer**: REST endpoints with DRF
3. **Business Logic Layer**: Services (contabilidad_service, ai_agent_service, etc.)
4. **Data Access Layer**: Django ORM models
5. **Database Layer**: PostgreSQL/SQLite

### Service-Oriented Design
- Centralized services handle complex business logic
- Services are reusable across views and API endpoints
- Clear separation of concerns

### Audit Trail Pattern
- `AuditModel` base class tracks creation and modification
- `creado_por`, `modificado_por`, `creado_en`, `modificado_en` fields
- Middleware captures current user automatically

### Double-Entry Bookkeeping
- Every transaction creates balanced journal entries
- `MovimientoContable` records debits and credits
- Automatic account creation and linking

### NIIF Compliance
- Models implement NIIF 9 (Financial Instruments)
- NIIF 15 (Revenue Recognition) with contracts and performance obligations
- NIC 2 (Inventory) with PEPS valuation
- NIC 16 (Property, Plant & Equipment) with revaluation support
