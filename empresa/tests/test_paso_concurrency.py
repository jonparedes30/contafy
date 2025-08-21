import threading
import json
import unittest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, PasoCompletado
from django.conf import settings

User = get_user_model()


class PasoConcurrencyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='concur', password='pass')
        self.mod = ModuloAprendizaje.objects.create(
            nombre='Módulo concur', tipo_empresa='comercial', descripcion='d', orden=1
        )
        self.leccion = Leccion.objects.create(
            modulo=self.mod,
            titulo='Lección concur',
            tipo='practica',
            contenido='contenido',
            puntos_xp=5,
        )
        # definir pasos
        self.leccion.pasos = json.dumps(['p1'])
        self.leccion.save()

    @unittest.skipIf('sqlite' in settings.DATABASES['default']['ENGINE'], "SQLite can't reliably simulate concurrent writes; run this test on Postgres")
    def test_concurrent_mark_same_paso(self):
        threads = []
        n_threads = 6
        barrier = threading.Barrier(n_threads)
        results = []

        def worker():
            try:
                barrier.wait()
            except Exception:
                pass
            # Retry loop to handle transient SQLite 'database table is locked'
            import time
            from django.db import transaction, utils as db_utils
            attempts = 6
            for attempt in range(attempts):
                try:
                    with transaction.atomic():
                        obj, created = PasoCompletado.objects.get_or_create(
                            usuario_id=self.user.id,
                            leccion_id=self.leccion.id,
                            paso_index=0
                        )
                    results.append({'created': bool(created)})
                    break
                except db_utils.OperationalError as e:
                    # SQLite can raise 'database table is locked' under concurrency; retry
                    if 'locked' in str(e).lower() and attempt < attempts - 1:
                        time.sleep(0.05 + attempt * 0.01)
                        continue
                    results.append({'error': str(e)})
                    break

        for i in range(n_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # Only one PasoCompletado should be created
        count = PasoCompletado.objects.filter(usuario=self.user, leccion=self.leccion, paso_index=0).count()
        self.assertEqual(count, 1, f"Expected 1 PasoCompletado, found {count}. Results: {results}")

        # At least one thread should report created=True
        created_found = any(r.get('created') for r in results if isinstance(r, dict))
        self.assertTrue(created_found, f"No thread reported creation; results: {results}")
