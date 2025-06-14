// Este es el punto de entrada principal para la lógica del frontend.

// Es importante importar las funciones que necesitamos de otros módulos.
// Nota: Para que los imports/exports funcionen, el script en index.html
// debe ser cargado con type="module".
import { analyzeStartupAPI } from './api.js';
import { showLoading, hideLoading, displayResults, displayError } from './ui.js';

// Hacemos que la función sea accesible globalmente para el `onclick` del HTML.
window.analyzeStartup = async function() {
    const urlInput = document.getElementById('websiteUrl');
    let url = urlInput.value.trim();

    if (!url) {
        displayError("Por favor, introduce una URL para analizar.");
        return;
    }

    // Añadir 'https://' si no se especifica un protocolo.
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
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

// Modal handling
document.addEventListener('DOMContentLoaded', () => {
    // Get modals
    const privacyModal = document.getElementById('privacy-modal');
    const termsModal = document.getElementById('terms-modal');
    const promptModal = document.getElementById('prompt-modal');

    // Get trigger links
    const privacyLink = document.getElementById('privacy-link');
    const termsLink = document.getElementById('terms-link');
    const promptLink = document.getElementById('prompt-link');

    // Get close buttons
    const closeBtns = document.querySelectorAll('.close-btn');

    // Open modals
    if (privacyLink) {
        privacyLink.onclick = (e) => {
            e.preventDefault();
            privacyModal.style.display = 'block';
        }
    }
    if (termsLink) {
        termsLink.onclick = (e) => {
            e.preventDefault();
            termsModal.style.display = 'block';
        }
    }
    if (promptLink) {
        promptLink.onclick = (e) => {
            e.preventDefault();
            promptModal.style.display = 'block';
        }
    }

    // Close modals with close button
    closeBtns.forEach(btn => {
        btn.onclick = () => {
            if (privacyModal) privacyModal.style.display = 'none';
            if (termsModal) termsModal.style.display = 'none';
            if (promptModal) promptModal.style.display = 'none';
        }
    });

    // Close modals by clicking outside
    window.onclick = (event) => {
        if (event.target == privacyModal || event.target == termsModal || event.target == promptModal) {
            if (privacyModal) privacyModal.style.display = 'none';
            if (termsModal) termsModal.style.display = 'none';
            if (promptModal) promptModal.style.display = 'none';
        }
    }
}); 