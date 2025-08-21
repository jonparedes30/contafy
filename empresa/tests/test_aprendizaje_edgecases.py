import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion

User = get_user_model()


class AprendizajeEdgeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='edge', password='pass')
        self.mod = ModuloAprendizaje.objects.create(
            nombre='Módulo edge', tipo_empresa='comercial', descripcion='d', orden=1
        )
        self.leccion = Leccion.objects.create(
            modulo=self.mod,
            titulo='Lección edge',
            tipo='practica',
            contenido='contenido',
            puntos_xp=5,
        )
        # Definir pasos para poder validar rango
        self.leccion.pasos = json.dumps(['paso1', 'paso2'])
        self.leccion.save()

    def test_paso_index_out_of_range(self):
        self.client.login(username='edge', password='pass')
        payload = {'leccion_id': str(self.leccion.id), 'paso_index': 9999}
        url = reverse('empresa:aprendizaje_paso_completado')
        r = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_paso_unauthenticated_redirects(self):
        payload = {'leccion_id': str(self.leccion.id), 'paso_index': 0}
        url = reverse('empresa:aprendizaje_paso_completado')
        r = self.client.post(url, data=payload, content_type='application/json')
        # @login_required should redirect to login (302)
        self.assertEqual(r.status_code, 302)
