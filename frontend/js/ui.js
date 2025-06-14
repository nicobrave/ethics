// Este archivo contiene funciones para manipular la interfaz de usuario (DOM).

export function showLoading() {
    document.querySelector('.results').style.display = 'none';
    document.querySelector('.loading').style.display = 'block';
    document.getElementById('analyze-btn').disabled = true;
}

export function hideLoading() {
    document.querySelector('.loading').style.display = 'none';
    document.getElementById('analyze-btn').disabled = false;
}

export function displayResults(data) {
    const resultsDiv = document.querySelector('.results');
    
    // Rellenar la tarjeta de puntuación
    const scoreCard = document.getElementById('ethicsScore');
    const scoreNumber = document.getElementById('scoreNumber');
    scoreCard.className = 'ethics-score'; // Reset class
    scoreNumber.textContent = data.overall_score;
    
    if (data.category === 'ethical') {
        scoreCard.classList.add('score-ethical');
    } else if (data.category === 'warning') {
        scoreCard.classList.add('score-warning');
    } else {
        scoreCard.classList.add('score-danger');
    }

    // Rellenar detalles del análisis
    document.getElementById('scoreText').textContent = data.title;
    document.getElementById('justificationText').textContent = data.justification;

    // Rellenar puntuaciones de criterios
    document.getElementById('privacyScore').textContent = `${data.criteria_scores.privacy}/10`;
    document.getElementById('socialScore').textContent = `${data.criteria_scores.social_impact}/10`;
    document.getElementById('transparencyScore').textContent = `${data.criteria_scores.transparency}/10`;
    document.getElementById('fairnessScore').textContent = `${data.criteria_scores.fairness}/10`;

    // Rellenar banderas rojas
    const redFlagsList = document.getElementById('flagsList');
    redFlagsList.innerHTML = '';

    const categoryTranslations = {
        "privacy": "Privacidad",
        "social_impact": "Impacto Social",
        "social": "Impacto Social",
        "transparency": "Transparencia",
        "fairness": "Equidad",
        "technical": "Técnico"
    };

    if (data.red_flags && data.red_flags.length > 0) {
        data.red_flags.forEach(flag => {
            const li = document.createElement('div');
            li.className = 'flag-item';
            const categoryInSpanish = categoryTranslations[flag.category.toLowerCase()] || flag.category;
            li.innerHTML = `<strong>${categoryInSpanish}:</strong> ${flag.description}`;
            redFlagsList.appendChild(li);
        });
        document.getElementById('redFlags').style.display = 'block';
    } else {
        document.getElementById('redFlags').style.display = 'none';
    }
    
    resultsDiv.style.display = 'block';
}

export function displayError(message) {
    // Podríamos crear un modal o una notificación más elegante, pero por ahora una alerta servirá.
    alert(`Error en el análisis:\n\n${message}`);
} 