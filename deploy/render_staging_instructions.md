# Deploy to Render - Staging

This file contains step-by-step instructions to deploy the `staging` branch to Render.

1) Create a `staging` branch locally and push:

```powershell
git checkout -b staging
git push -u origin staging
```

2) Configure Render service
- In Render dashboard, create a new Web Service.
- Connect to your GitHub/GitLab repo and select the `staging` branch.
- Set the build and start commands (example):
  - Build command: `./build.sh` or `pip install -r requirements.txt && python manage.py collectstatic --noinput`
  - Start command: `gunicorn core.wsgi:application --log-file -`
- Add environment variables:
  - `DJANGO_SETTINGS_MODULE=core.settings` (or a `core.settings.render` file if present)
  - `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `SENTRY_DSN` (optional)

3) Trigger deploy and monitor logs
- After pushing, Trigger a manual deploy in Render (or let it auto-deploy).
- Monitor live logs for 500/403 or NoReverseMatch.

4) Smoke tests to run after deploy
- Visit `/app-beta-2024/` home and login.
- Verify `resumen` dashboard loads, manufactura pages, and product API endpoints.
- Check export PDF endpoints (reportlab dependency) and Excel exports (openpyxl) work.

5) Rollback
- Use Render's deploy history to rollback if errors are detected.
