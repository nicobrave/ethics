// Este es el punto de entrada principal para la lógica del frontend.

// Es importante importar las funciones que necesitamos de otros módulos.
// Nota: Para que los imports/exports funcionen, el script en index.html
// debe ser cargado con type="module".
import { analyzeStartupAPI } from './api.js';
import { showLoading, hideLoading, displayResults, displayError } from './ui.js';

// Hacemos que la función sea accesible globalmente para el `onclick` del HTML.
window.analyzeStartup = async function() {
    const urlInput = document.getElementById('websiteUrl');
    const url = urlInput.value;

    if (!url) {
        displayError("Por favor, introduce una URL para analizar.");
        return;
    }

    showLoading();

    try {
        const result = await analyzeStartupAPI(url);
        // La API ahora devuelve un objeto con { success, data, error }
        if (result.success) {
            displayResults(result.data);
        } else {
            displayError(result.error || 'Ocurrió un error desconocido.');
        }
    } catch (error) {
        console.error('Error en el análisis:', error);
        displayError(error.message);
    } finally {
        hideLoading();
    }
} 