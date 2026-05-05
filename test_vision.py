import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from empresa.models import Usuario

c = Client()
user = Usuario.objects.first()
if user:
    c.force_login(user)
    try:
        res = c.post('/app-beta-2024/compra/vision-search/', '{"image": "data:image/jpeg;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7", "contexto": "venta"}', content_type='application/json')
        print("STATUS_CODE:", res.status_code)
        import json
        print("RESPONSE:", json.dumps(res.json(), indent=2))
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("No user found")
