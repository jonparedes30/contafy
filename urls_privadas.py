# En contafy/urls.py - MODIFICAR para URL secreta

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # URL secreta - solo tú la conoces
    path('app-beta-2024/', include('empresa.urls')),  # En lugar de 'empresa/'
]

# RESULTADO:
# URL pública: https://contafy-pruebas.herokuapp.com/app-beta-2024/
# Solo quien tenga este link puede acceder

# En empresa/templates/empresa/registro.html - AGREGAR campo código
"""
<div class="mb-3">
    <label for="codigo_invitacion" class="form-label">Código de Invitación <span class="text-danger">*</span></label>
    <input type="text" class="form-control" id="codigo_invitacion" name="codigo_invitacion" 
           placeholder="Ej: CONTAFY-ABC123XYZ" required>
    <small class="text-muted">Ingresa el código que recibiste por email</small>
</div>
"""