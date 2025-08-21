# Run tests locally

This repository uses Django. For fast local unit testing we provide `core.test_settings` which uses SQLite in-memory DB.

Run a single test:

```powershell
$env:DJANGO_SETTINGS_MODULE='core.test_settings'; python manage.py test empresa.tests.test_aprendizaje.AprendizajeTests.test_paso_completado_success
Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

Run the whole `empresa` tests:

```powershell
$env:DJANGO_SETTINGS_MODULE='core.test_settings'; python manage.py test empresa.tests
Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

CI (recommended): run tests against Postgres. Example (GitHub Actions) workflow is included in `.github/workflows/test.yml`.

Notes:
- Concurrency tests are skipped on SQLite; run them on Postgres to validate transactional behavior.
- To run tests with a PostgreSQL locally, set `DATABASE_URL` or configure `DJANGO_SETTINGS_MODULE` to a settings file that points to Postgres.
