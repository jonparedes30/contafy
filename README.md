# CONTAFY

Plataforma SaaS de gestión contable–financiera para pymes ecuatorianas.

## Características principales
- Gestión de gastos, ingresos y cuentas contables
- Reportes: balance general, estado de resultados, flujo de caja
- Autenticación JWT segura
- Soporte para PostgreSQL

## Instalación rápida

```bash
git clone https://github.com/tuusuario/contafy.git
cd contafy
python -m venv venv
source venv/bin/activate  # o .\\venv\\Scripts\\activate en Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Configuración

Edita el archivo `.env` con tus credenciales y variables de entorno.

## Licencia

MIT 