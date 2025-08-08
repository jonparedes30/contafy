/**
 * Escáner de códigos de barras usando BarcodeDetector API (moderna)
 */
class BarcodeScanner {
    constructor() {
        this.isScanning = false;
        this.onDetected = null;
        this.stream = null;
        this.video = null;
        this.detector = null;
        this.scanInterval = null;
    }

    /**
     * Inicializa el escáner
     */
    async init(containerId, onDetectedCallback) {
        this.onDetected = onDetectedCallback;
        
        try {
            // Verificar soporte de cámara
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Cámara no soportada en este navegador');
            }

            // Intentar usar BarcodeDetector moderno primero
            if ('BarcodeDetector' in window) {
                await this.initModernScanner(containerId);
            } else {
                // Fallback a QuaggaJS
                await this.initLegacyScanner(containerId);
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.onError(error.message);
        }
    }

    /**
     * Inicializa escáner moderno con BarcodeDetector
     */
    async initModernScanner(containerId) {
        console.log('Usando BarcodeDetector API moderna');
        
        // Crear detector
        this.detector = new BarcodeDetector({
            formats: ['code_128', 'code_39', 'ean_13', 'ean_8', 'upc_a']
        });

        // Obtener stream de video
        this.stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment',
                width: { ideal: 640 },
                height: { ideal: 480 }
            }
        });

        // Crear elemento video
        const container = document.getElementById(containerId);
        this.video = document.createElement('video');
        this.video.style.width = '100%';
        this.video.style.height = '100%';
        this.video.style.objectFit = 'cover';
        this.video.autoplay = true;
        this.video.playsInline = true;
        
        container.appendChild(this.video);
        this.video.srcObject = this.stream;
        
        // Esperar a que el video esté listo
        await new Promise((resolve) => {
            this.video.onloadedmetadata = resolve;
        });
        
        this.isScanning = true;
        this.startScanning();
    }

    /**
     * Inicializa escáner legacy con QuaggaJS
     */
    async initLegacyScanner(containerId) {
        console.log('Usando QuaggaJS como fallback');
        
        // Cargar QuaggaJS
        await this.loadQuagga();
        
        // Configurar Quagga
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector(`#${containerId}`),
                constraints: {
                    width: 640,
                    height: 480,
                    facingMode: "environment"
                }
            },
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader"
                ]
            }
        }, (err) => {
            if (err) {
                this.onError('Error inicializando escáner: ' + err.message);
                return;
            }
            
            Quagga.start();
            this.isScanning = true;
            Quagga.onDetected(this.handleLegacyDetection.bind(this));
        });
    }

    /**
     * Inicia el escaneo continuo (API moderna)
     */
    startScanning() {
        if (!this.detector || !this.video) return;
        
        this.scanInterval = setInterval(async () => {
            if (!this.isScanning) return;
            
            try {
                const barcodes = await this.detector.detect(this.video);
                
                if (barcodes.length > 0) {
                    const barcode = barcodes[0];
                    console.log('Código detectado:', barcode.rawValue, 'Formato:', barcode.format);
                    
                    if (this.onDetected) {
                        this.onDetected(barcode.rawValue);
                    }
                    
                    this.stop();
                }
            } catch (error) {
                console.error('Error detectando código:', error);
            }
        }, 100); // Escanear cada 100ms
    }

    /**
     * Maneja detección legacy
     */
    handleLegacyDetection(result) {
        const code = result.codeResult.code;
        const confidence = result.codeResult.confidence || 0;
        
        if (confidence > 75) {
            console.log('Código detectado (legacy):', code);
            
            if (this.onDetected) {
                this.onDetected(code);
            }
            
            this.stop();
        }
    }

    /**
     * Carga QuaggaJS dinámicamente
     */
    loadQuagga() {
        return new Promise((resolve, reject) => {
            if (window.Quagga) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Error cargando librería'));
            document.head.appendChild(script);
        });
    }

    /**
     * Detiene el escáner
     */
    stop() {
        this.isScanning = false;
        
        // Detener intervalo de escaneo
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        
        // Detener stream de video
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        // Detener Quagga si está activo
        if (window.Quagga && window.Quagga.stop) {
            try {
                window.Quagga.stop();
            } catch (error) {
                console.error('Error deteniendo Quagga:', error);
            }
        }
        
        console.log('Escáner detenido');
    }

    /**
     * Maneja errores
     */
    onError(message) {
        console.error('Error del escáner:', message);
        alert('Error del escáner: ' + message);
    }
}

// Función global
window.BarcodeScanner = BarcodeScanner;