export async function analyzeStartupAPI(url) {
    const response = await fetch('https://ethics-36kr.onrender.com/api/v1/analyze', {
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