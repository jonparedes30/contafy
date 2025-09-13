from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion

User = get_user_model()

class ModuloAprendizajeTests(TestCase):
    def test_slug_auto_generation(self):
        modulo = ModuloAprendizaje.objects.create(
            nombre="Contabilidad Básica",
            tipo_empresa="comercial",
            descripcion="Módulo de prueba"
        )
        self.assertEqual(modulo.slug, "contabilidad-basica")
    
    def test_unique_slug(self):
        ModuloAprendizaje.objects.create(
            nombre="Test",
            slug="test-slug",
            tipo_empresa="comercial",
            descripcion="Test"
        )
        with self.assertRaises(Exception):
            ModuloAprendizaje.objects.create(
                nombre="Test 2",
                slug="test-slug",
                tipo_empresa="servicios",
                descripcion="Test 2"
            )

class LeccionTests(TestCase):
    def setUp(self):
        self.modulo = ModuloAprendizaje.objects.create(
            nombre="Test Módulo",
            tipo_empresa="comercial",
            descripcion="Test"
        )
    
    def test_slug_auto_generation(self):
        leccion = Leccion.objects.create(
            modulo=self.modulo,
            titulo="Mi Primera Lección",
            contenido="Contenido de prueba"
        )
        self.assertEqual(leccion.slug, "mi-primera-leccion")
    
    def test_pasos_json_validation_valid(self):
        leccion = Leccion(
            modulo=self.modulo,
            titulo="Test",
            contenido="Test",
            pasos=[
                {"titulo": "Paso 1", "descripcion": "Test"},
                {"titulo": "Paso 2", "descripcion": "Test"}
            ]
        )
        leccion.clean()  # No debe lanzar excepción
    
    def test_pasos_json_validation_invalid(self):
        leccion = Leccion(
            modulo=self.modulo,
            titulo="Test",
            contenido="Test",
            pasos=[
                {"descripcion": "Sin título"},  # Falta 'titulo'
            ]
        )
        with self.assertRaises(ValidationError):
            leccion.clean()
    
    def test_pasos_json_validation_not_list(self):
        leccion = Leccion(
            modulo=self.modulo,
            titulo="Test",
            contenido="Test",
            pasos={"not": "a list"}
        )
        with self.assertRaises(ValidationError):
            leccion.clean()