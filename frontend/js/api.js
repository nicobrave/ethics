export async function analyzeStartupAPI(url) {
    const response = await fetch('https://ethics-36kr.onrender.com/api/v1/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url, deep_scan: false })
    });

    if (response.ok) {
        return await response.json();
    }

    // Manejar errores de forma más robusta
    let errorDetail = 'No se pudo obtener el detalle del error del servidor.';
    try {
        const errorBody = await response.json();
        if (errorBody.detail && Array.isArray(errorBody.detail)) {
            // Formatear el error de validación de FastAPI para que sea legible
            errorDetail = errorBody.detail.map(err => `Campo: '${err.loc.join('.')}', Mensaje: ${err.msg}`).join('; ');
        } else if (errorBody.detail) {
            errorDetail = JSON.stringify(errorBody.detail);
        }
    } catch (e) {
        errorDetail = 'La respuesta de error del servidor no estaba en formato JSON.';
    }

    throw new Error(`El servidor respondió con un error ${response.status}. Detalles: ${errorDetail}`);
} 