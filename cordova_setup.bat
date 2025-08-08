@echo off
echo Instalando Cordova...
npm install -g cordova

echo Creando proyecto Cordova...
cordova create ContafyApp com.contafy.app CONTAFY

echo Agregando plataformas...
cd ContafyApp
cordova platform add android
cordova platform add ios

echo Cordova configurado exitosamente!
echo Ahora ejecuta: copy_web_files.bat
pause