export async function analyzeStartupAPI(url) {
    const response = await fetch('https://ethics-36kr.onrender.com/api/v1/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url, deep_scan: false })
    });

    if (!response.ok) {
        try {
            const errorBody = await response.json();
            console.error("Server validation error:", errorBody);
            const detail = errorBody.detail ? JSON.stringify(errorBody.detail) : 'No se proporcionaron detalles adicionales.';
            throw new Error(`El servidor respondió con un error ${response.status}. Detalles: ${detail}`);
        } catch (e) {
            throw new Error(`El servidor respondió con un error ${response.status} y la respuesta no pudo ser leída.`);
        }
    }

    return await response.json();
} 