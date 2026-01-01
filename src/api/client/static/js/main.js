// ~/dev/projects/python/tc_fiap_fase4/src/api/client/static/js/main.js

function scrollToPredict() {
    document.getElementById('predict').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

async function fazerPrevisao() {
    const dias = document.getElementById('dias').value;
    const loadingDiv = document.getElementById('loading');
    const resultadoDiv = document.getElementById('resultado');
    
    // Limpar resultado anterior
    resultadoDiv.innerHTML = '';
    
    // Mostrar loading
    loadingDiv.style.display = 'block';
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ dias: parseInt(dias) })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao buscar previsão');
        }
        
        const data = await response.json();
        
        // Ocultar loading
        loadingDiv.style.display = 'none';
        
        // Mostrar resultado
        mostrarResultado(data);
        
    } catch (error) {
        loadingDiv.style.display = 'none';
        resultadoDiv.innerHTML = `
            <div style="color: #dc2626; padding: 1rem; background: #fee2e2; border-radius: 8px;">
                <strong>Erro:</strong> ${error.message}
            </div>
        `;
    }
}

function mostrarResultado(data) {
    const resultadoDiv = document.getElementById('resultado');
    
    let html = `
        <h3>📈 Previsões para PETR4.SA</h3>
        <p><strong>Modelo:</strong> ${data.modelo_usado}</p>
        <p><strong>Gerado em:</strong> ${new Date(data.data_geracao).toLocaleString('pt-BR')}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Preço Previsto</th>
                    <th>Confiança</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    data.previsoes.forEach(previsao => {
        const data = new Date(previsao.data_previsao).toLocaleDateString('pt-BR');
        const preco = `R$ ${previsao.preco_previsto.toFixed(2)}`;
        const confianca = previsao.confianca 
            ? `${(previsao.confianca * 100).toFixed(0)}%` 
            : 'N/A';
        
        html += `
            <tr>
                <td>${data}</td>
                <td>${preco}</td>
                <td>${confianca}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    resultadoDiv.innerHTML = html;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const diasInput = document.getElementById('dias');
    
    if (diasInput) {
        diasInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                fazerPrevisao();
            }
        });
    }
});