# CSRF and URL namespacing guidance

This document explains the project's conventions for CSRF tokens and URL namespacing.

1) CSRF token usage
- Include the meta token in `base.html` head:
  ```html
  <meta name="contafy-csrf-token" content="{{ csrf_token }}" />
  <script>
    window.CONTAFY_CSRF_TOKEN = document.querySelector('meta[name="contafy-csrf-token"]').content;
  </script>
  ```
- For AJAX requests, set header `X-CSRFToken: window.CONTAFY_CSRF_TOKEN` or use the helper where available.

2) URL namespacing
- All `empresa` app URLs must be referenced using the `empresa` namespace:
  ```django
  {% url 'empresa:producto_info_api' %}
  ```
- Avoid hard-coded `/empresa/` paths in templates. Use `{% url %}` so reversals work across environments (local, Render, Heroku).

3) Enabling pre-commit hook locally
- Run:
  ```powershell
  git config core.hooksPath .githooks
  ```
- This will run the pre-commit script which calls `scripts/check_hardcoded_paths.py` on each commit.
