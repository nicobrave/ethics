export async function analyzeStartupAPI(url) {
    const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url })
    });
    if (!response.ok) {
        throw new Error('Error al analizar la startup');
    }
    return await response.json();
} 