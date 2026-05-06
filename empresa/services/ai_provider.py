"""
Capa de abstracción para proveedores de IA.

Permite intercambiar entre OpenAI, Gemini y Mock sin modificar la lógica
de negocio. Configurar AI_PROVIDER en settings.py o .env.

Uso:
    from empresa.services.ai_provider import get_ai_provider
    provider = get_ai_provider()
    response = provider.complete("Analiza estos datos financieros...")
"""
import json
import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Interfaz base que todos los proveedores de IA deben implementar."""

    @abstractmethod
    def complete(self, prompt, system=None):
        """
        Genera una respuesta de texto a partir de un prompt.

        Args:
            prompt: El texto del prompt principal.
            system: Instrucciones de sistema opcionales.

        Returns:
            str: La respuesta generada por el modelo.
        """
        pass

    @abstractmethod
    def embed(self, text):
        """
        Genera un vector embedding para el texto dado.

        Args:
            text: El texto a convertir en embedding.

        Returns:
            list[float]: Vector de embedding.
        """
        pass

    @abstractmethod
    def is_available(self):
        """
        Verifica si el proveedor está correctamente configurado y disponible.

        Returns:
            bool: True si el proveedor puede recibir requests.
        """
        pass


class OpenAIProvider(BaseAIProvider):
    """Proveedor usando la API de OpenAI (GPT)."""

    def __init__(self):
        self._client = None
        self._available = False
        try:
            import openai
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            if api_key:
                self._client = openai.OpenAI(api_key=api_key)
                self._available = True
                logger.info("OpenAI provider inicializado correctamente")
        except ImportError:
            logger.warning("openai no instalado. pip install openai")
        except Exception as e:
            logger.error(f"Error inicializando OpenAI: {e}")

    def complete(self, prompt, system=None):
        if not self._available:
            raise RuntimeError("OpenAI no está disponible")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content

    def embed(self, text):
        if not self._available:
            raise RuntimeError("OpenAI no está disponible")

        response = self._client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def is_available(self):
        return self._available


class GeminiProvider(BaseAIProvider):
    """Proveedor usando Google Gemini."""

    def __init__(self):
        self._model = None
        self._available = False
        try:
            import google.generativeai as genai
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            if api_key:
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel('gemini-1.5-flash')
                self._available = True
                logger.info("Gemini provider inicializado correctamente")
        except ImportError:
            logger.warning("google-generativeai no instalado")
        except Exception as e:
            logger.error(f"Error inicializando Gemini: {e}")

    def complete(self, prompt, system=None):
        if not self._available:
            raise RuntimeError("Gemini no está disponible")

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        response = self._model.generate_content(full_prompt)
        text = response.text.strip()

        # Limpiar markdown si viene envuelto en ```json
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        return text.strip()

    def embed(self, text):
        if not self._available:
            raise RuntimeError("Gemini no está disponible")

        import google.generativeai as genai
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
        )
        return result['embedding']

    def is_available(self):
        return self._available


class MockProvider(BaseAIProvider):
    """
    Proveedor simulado para tests. Devuelve respuestas predecibles
    sin necesitar API keys ni conexión a internet.
    """

    def __init__(self):
        logger.info("MockProvider inicializado (modo test)")

    def complete(self, prompt, system=None):
        """Devuelve una respuesta predecible basada en el prompt."""
        prompt_lower = prompt.lower()

        # Detectar si se espera JSON
        if 'json' in prompt_lower or 'formato json' in prompt_lower:
            return json.dumps({
                "resumen": "Analisis simulado para testing.",
                "fortalezas": ["Margen de utilidad saludable", "Crecimiento constante"],
                "debilidades": ["Gastos operativos altos", "Dependencia de un solo producto"],
                "oportunidades": ["Expansion digital", "Nuevos mercados"],
                "acciones_inmediatas": ["Reducir gastos en 10%", "Diversificar productos"],
                "prediccion_proximo_mes": "Tendencia estable con posible crecimiento del 5%",
                "recomendacion_principal": "Optimizar estructura de costos operativos"
            }, ensure_ascii=False)

        # Respuesta genérica para consultas de chat
        if 'venta' in prompt_lower:
            return "Las ventas muestran una tendencia estable. Se recomienda diversificar canales."
        elif 'gasto' in prompt_lower:
            return "Los gastos operativos representan un porcentaje elevado. Revisar contratos."
        elif 'liquidez' in prompt_lower:
            return "La liquidez es adecuada para cubrir obligaciones de corto plazo."

        return "Analisis completado exitosamente. Datos procesados correctamente."

    def embed(self, text):
        """Devuelve un vector de embedding simulado (dimensión 256)."""
        import hashlib
        # Generar embedding determinístico basado en hash del texto
        h = hashlib.sha256(text.encode()).hexdigest()
        return [int(h[i:i+2], 16) / 255.0 for i in range(0, min(len(h), 512), 2)]

    def is_available(self):
        return True


# ============================================================================
# Factory function
# ============================================================================

_provider_instance = None


def get_ai_provider(force_new=False):
    """
    Factory que retorna el proveedor de IA configurado en settings.AI_PROVIDER.

    Opciones:
        - 'openai': Usa OpenAI GPT
        - 'gemini': Usa Google Gemini (default)
        - 'mock': Respuestas simuladas para testing

    Args:
        force_new: Si True, crea una nueva instancia ignorando el cache.

    Returns:
        BaseAIProvider: Instancia del proveedor configurado.
    """
    global _provider_instance

    if _provider_instance is not None and not force_new:
        return _provider_instance

    provider_name = getattr(settings, 'AI_PROVIDER', 'gemini').lower()

    providers = {
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
        'mock': MockProvider,
    }

    provider_class = providers.get(provider_name)

    if provider_class is None:
        logger.warning(
            f"AI_PROVIDER='{provider_name}' no reconocido. "
            f"Opciones: {list(providers.keys())}. Usando 'gemini'."
        )
        provider_class = GeminiProvider

    instance = provider_class()

    # Si el proveedor elegido no está disponible, fallback a mock
    if not instance.is_available() and provider_name != 'mock':
        logger.warning(
            f"AI_PROVIDER='{provider_name}' no disponible "
            f"(falta API key o libreria). Fallback a MockProvider."
        )
        instance = MockProvider()

    _provider_instance = instance
    return _provider_instance
