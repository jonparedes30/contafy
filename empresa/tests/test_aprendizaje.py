from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, PasoCompletado

User = get_user_model()


class AprendizajeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.mod = ModuloAprendizaje.objects.create(
            nombre='Módulo demo', tipo_empresa='comercial', descripcion='d', orden=1
        )
        self.leccion = Leccion.objects.create(
            modulo=self.mod,
            titulo='Lección demo',
            tipo='practica',
            contenido='contenido',
            puntos_xp=10,
        )

    def test_paso_completado_success(self):
        self.client.login(username='tester', password='pass')
        payload = {
            'leccion_id': str(self.leccion.id),
            'paso_index': 0,
            'micro_xp': 5,
        }
        url = reverse('empresa:aprendizaje_paso_completado')
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

        exists = PasoCompletado.objects.filter(
            usuario=self.user, leccion=self.leccion, paso_index=0
        ).exists()
        self.assertTrue(exists)

    def test_paso_completado_duplicate(self):
        self.client.login(username='tester', password='pass')
        payload = {'leccion_id': str(self.leccion.id), 'paso_index': 1}
        url = reverse('empresa:aprendizaje_paso_completado')
        r1 = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertFalse(d2.get('ok'))
        self.assertIn('Paso ya registrado', d2.get('message'))
