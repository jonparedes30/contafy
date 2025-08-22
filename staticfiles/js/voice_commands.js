/**
 * Sistema de Comandos de Voz para CONTAFY AI
 */
class VoiceCommandsIA {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.initSpeechRecognition();
    }

    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.lang = 'es-ES';  // Cambiar a es-ES (más compatible)
            this.recognition.continuous = false;
            this.recognition.interimResults = true;  // Mostrar resultados parciales
            this.recognition.maxAlternatives = 3;    // Más alternativas

            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceButton(true);
                this.showVoiceIndicator('Escuchando...');
            };

            this.recognition.onresult = (event) => {
                let comando = '';
                // Obtener el resultado más reciente
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        comando += event.results[i][0].transcript;
                    } else {
                        // Mostrar resultado parcial
                        this.showVoiceIndicator('Escuchando: ' + event.results[i][0].transcript, 'info');
                    }
                }
                
                if (comando.trim()) {
                    console.log('Comando reconocido:', comando);
                    this.processVoiceCommand(comando.trim());
                }
            };

            this.recognition.onerror = (event) => {
                console.error('Error de reconocimiento:', event.error);
                this.showVoiceIndicator('Error: ' + event.error, 'error');
                this.stopListening();
            };

            this.recognition.onend = () => {
                this.stopListening();
            };
        } else {
            console.warn('Reconocimiento de voz no soportado');
            // Crear indicador de no soportado
            setTimeout(() => {
                this.showVoiceIndicator('Reconocimiento de voz no disponible en este navegador. Usa Chrome o Edge.', 'error');
            }, 1000);
        }
    }

    startListening() {
        if (this.recognition && !this.isListening) {
            try {
                console.log('Iniciando reconocimiento de voz...');
                this.recognition.start();
            } catch (error) {
                console.error('Error iniciando reconocimiento:', error);
                this.showVoiceIndicator('Error: Permisos de micrófono requeridos', 'error');
                
                // Solicitar permisos explícitamente
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(() => {
                        console.log('Permisos concedidos, reintentando...');
                        setTimeout(() => this.recognition.start(), 500);
                    })
                    .catch(err => {
                        console.error('Permisos denegados:', err);
                        this.showVoiceIndicator('Permisos de micrófono denegados', 'error');
                    });
            }
        } else if (!this.recognition) {
            this.showVoiceIndicator('Reconocimiento de voz no soportado en este navegador', 'error');
        }
    }

    stopListening() {
        this.isListening = false;
        this.updateVoiceButton(false);
        this.hideVoiceIndicator();
    }

    processVoiceCommand(comando) {
        this.showVoiceIndicator(`Procesando: "${comando}"`, 'processing');
        
        // Enviar comando al sistema de IA
        fetch('/empresa/api/comando-voz/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ comando: comando })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showVoiceIndicator(`✅ ${data.mensaje}`, 'success');
                
                // Si hay respuesta de voz, reproducirla
                if (data.respuesta_voz) {
                    this.speakResponse(data.respuesta_voz);
                }
                
                // Actualizar interfaz si es necesario
                if (data.actualizar_pagina) {
                    setTimeout(() => location.reload(), 2000);
                }
            } else {
                this.showVoiceIndicator(`❌ ${data.error}`, 'error');
            }
        })
        .catch(error => {
            this.showVoiceIndicator('Error de conexión', 'error');
        });
    }

    speakResponse(texto) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-EC';
            utterance.rate = 0.9;
            utterance.pitch = 1;
            speechSynthesis.speak(utterance);
        }
    }

    updateVoiceButton(listening) {
        const btn = document.getElementById('voice-btn');
        if (btn) {
            if (listening) {
                btn.innerHTML = '<i class="bi bi-mic-fill text-danger"></i>';
                btn.classList.add('btn-danger');
                btn.classList.remove('btn-primary');
            } else {
                btn.innerHTML = '<i class="bi bi-mic"></i>';
                btn.classList.add('btn-primary');
                btn.classList.remove('btn-danger');
            }
        }
    }

    showVoiceIndicator(mensaje, tipo = 'info') {
        let indicator = document.getElementById('voice-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'voice-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                z-index: 9999;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(indicator);
        }

        const colores = {
            info: '#17a2b8',
            processing: '#ffc107',
            success: '#28a745',
            error: '#dc3545'
        };

        indicator.style.backgroundColor = colores[tipo] || colores.info;
        indicator.textContent = mensaje;
        indicator.style.display = 'block';

        if (tipo === 'success' || tipo === 'error') {
            setTimeout(() => this.hideVoiceIndicator(), 3000);
        }
    }

    hideVoiceIndicator() {
        const indicator = document.getElementById('voice-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

// Inicializar sistema de voz
const voiceCommands = new VoiceCommandsIA();

// Función global para activar desde botones
function toggleVoiceCommand() {
    if (voiceCommands.isListening) {
        voiceCommands.stopListening();
    } else {
        voiceCommands.startListening();
    }
}