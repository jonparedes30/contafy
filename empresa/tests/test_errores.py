from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from empresa.utils.errores import MENSAJE_GENERICO, mensaje_error


class MensajeErrorTests(SimpleTestCase):
    @override_settings(DEBUG=False)
    def test_no_expone_detalles_tecnicos(self):
        try:
            raise RuntimeError('no such table: empresa_venta; key=AIza-secreta')
        except RuntimeError as e:
            texto = mensaje_error(e)
        self.assertEqual(texto, MENSAJE_GENERICO)

    def test_validacion_se_muestra_al_usuario(self):
        try:
            raise ValidationError('El RUC no es válido.')
        except ValidationError as e:
            self.assertEqual(mensaje_error(e), 'El RUC no es válido.')
