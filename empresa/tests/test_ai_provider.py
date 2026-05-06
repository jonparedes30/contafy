"""
Tests para la capa de abstracción de IA (ai_provider.py).

Verifica que MockProvider funciona correctamente y que el factory
devuelve el proveedor configurado.
"""
import pytest
import json
from unittest.mock import patch
from django.test import TestCase, override_settings

from empresa.services.ai_provider import (
    MockProvider,
    get_ai_provider,
    _provider_instance,
)


class TestMockProvider(TestCase):
    """Tests del MockProvider para verificar respuestas predecibles."""

    def setUp(self):
        self.provider = MockProvider()

    def test_is_available(self):
        """MockProvider siempre está disponible."""
        self.assertTrue(self.provider.is_available())

    def test_complete_json_response(self):
        """Cuando el prompt pide JSON, MockProvider devuelve JSON válido."""
        response = self.provider.complete("Dame un analisis en formato JSON")
        data = json.loads(response)
        self.assertIn('resumen', data)
        self.assertIn('fortalezas', data)
        self.assertIn('debilidades', data)
        self.assertIsInstance(data['fortalezas'], list)

    def test_complete_ventas(self):
        """Pregunta sobre ventas devuelve respuesta relevante."""
        response = self.provider.complete("Como van las ventas?")
        self.assertIn('venta', response.lower())

    def test_complete_gastos(self):
        """Pregunta sobre gastos devuelve respuesta relevante."""
        response = self.provider.complete("Analiza los gastos operativos")
        self.assertIn('gasto', response.lower())

    def test_complete_generico(self):
        """Pregunta genérica devuelve respuesta no vacía."""
        response = self.provider.complete("Hola, como estas?")
        self.assertTrue(len(response) > 0)

    def test_complete_con_system(self):
        """El parámetro system no causa error."""
        response = self.provider.complete(
            "Analiza datos",
            system="Eres un experto financiero",
        )
        self.assertTrue(len(response) > 0)

    def test_embed(self):
        """embed() devuelve un vector de floats."""
        embedding = self.provider.embed("texto de prueba")
        self.assertIsInstance(embedding, list)
        self.assertTrue(len(embedding) > 0)
        self.assertTrue(all(isinstance(x, float) for x in embedding))

    def test_embed_determinista(self):
        """El mismo texto produce el mismo embedding."""
        emb1 = self.provider.embed("mismo texto")
        emb2 = self.provider.embed("mismo texto")
        self.assertEqual(emb1, emb2)

    def test_embed_diferente(self):
        """Textos diferentes producen embeddings diferentes."""
        emb1 = self.provider.embed("texto uno")
        emb2 = self.provider.embed("texto dos")
        self.assertNotEqual(emb1, emb2)


class TestGetAIProvider(TestCase):
    """Tests del factory get_ai_provider()."""

    def tearDown(self):
        # Limpiar cache del singleton
        import empresa.services.ai_provider as mod
        mod._provider_instance = None

    @override_settings(AI_PROVIDER='mock')
    def test_factory_mock(self):
        """Con AI_PROVIDER='mock', devuelve MockProvider."""
        provider = get_ai_provider(force_new=True)
        self.assertIsInstance(provider, MockProvider)
        self.assertTrue(provider.is_available())

    @override_settings(AI_PROVIDER='mock')
    def test_factory_caching(self):
        """El factory cachea la instancia (singleton)."""
        p1 = get_ai_provider(force_new=True)
        p2 = get_ai_provider()
        self.assertIs(p1, p2)

    @override_settings(AI_PROVIDER='mock')
    def test_factory_force_new(self):
        """force_new=True crea una nueva instancia."""
        p1 = get_ai_provider(force_new=True)
        p2 = get_ai_provider(force_new=True)
        self.assertIsNot(p1, p2)

    @override_settings(AI_PROVIDER='invalid_provider')
    def test_factory_invalid_fallback(self):
        """Proveedor inválido hace fallback (no crashea)."""
        provider = get_ai_provider(force_new=True)
        # Debe devolver algo funcional (MockProvider si el fallback no está disponible)
        self.assertTrue(provider.is_available())
