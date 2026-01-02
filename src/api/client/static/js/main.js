// ~/dev/projects/python/tc_fiap_fase4/src/api/client/static/js/main.js

function scrollToPredict() {
    document.getElementById('predict').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function criarCardIndicador(titulo, valor, cor="blue") {
    return `
        <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0;">
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">${titulo}</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: var(--petrobras-${cor}, #003399);">${valor}</div>
        </div>
    `;
}

async function fazerPrevisao() {
    console.log("Iniciando previsão..."); // Debug
    const dias = document.getElementById('dias').value;
    const loadingDiv = document.getElementById('loading');
    const resultadoDiv = document.getElementById('resultado');
    
    // Limpar resultado anterior
    resultadoDiv.innerHTML = '';
    
    // Mostrar loading
    loadingDiv.style.display = 'block';
    
    try {
        console.log("Enviando dados:", JSON.stringify({ dias: parseInt(dias) })); // Debug

        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ dias: parseInt(dias) })
        });
        
        console.log("Status da resposta:", response.status); // Debug

        // Se der erro (ex: 422 ou 500), tenta ler o JSON de erro
        if (!response.ok) {
            const errorData = await response.json();
            console.error("Detalhe do erro:", errorData); // Debug
            
            // Formata o erro do FastAPI (Pydantic) para ficar legível
            let msgErro = 'Erro ao buscar previsão';
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    msgErro = errorData.detail.map(e => `${e.loc.join('.')} - ${e.msg}`).join(', ');
                } else {
                    msgErro = errorData.detail;
                }
            }
            throw new Error(`Erro ${response.status}: ${msgErro}`);
        }
        
        const data = await response.json();
        console.log("Dados recebidos:", data); // Debug
        
        loadingDiv.style.display = 'none';
        mostrarResultado(data);
        
    } catch (error) {
        console.error("Erro capturado:", error); // Debug
        loadingDiv.style.display = 'none';
        resultadoDiv.innerHTML = `
            <div style="color: #dc2626; padding: 1rem; background: #fee2e2; border-radius: 8px; border: 1px solid #ef4444;">
                <strong>❌ Ops! Algo deu errado:</strong><br>
                ${error.message}
            </div>
        `;
    }
}

function mostrarResultado(data) {
    const resultadoDiv = document.getElementById('resultado');
    const mercado = data.dados_mercado;
    
    // Formatação de Datas e Valores
    const dataRef = new Date(mercado.data_referencia + 'T00:00:00');
    const dataFormatada = dataRef.toLocaleDateString('pt-BR');
    
    // Formatadores Auxiliares
    const fmtMoeda = (valor) => valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const fmtNum = (valor) => valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    // Novo: Formata Ibovespa sem casas decimais
    const fmtInteiro = (valor) => valor.toLocaleString('pt-BR', { maximumFractionDigits: 0 });

    // HTML do Dashboard
    let html = `
        <div class="market-dashboard">
            
            <!-- 1. Cabeçalho com Preço Atual -->
            <div class="dashboard-header">
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">
                    📅 Dados de Fechamento: ${dataFormatada}
                </div>
                <div style="font-size: 2.5rem; font-weight: 700;">
                    ${fmtMoeda(mercado.preco_atual)}
                </div>
                <div>Último preço real da PETR4.SA utilizado como base.</div>
            </div>

            <!-- 2. Grid de Variáveis Macroeconômicas -->
            <h3 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem;">
                🌎 Cenário Macroeconômico (Inputs do Modelo)
            </h3>
            <div class="indicators-grid">
                <div class="indicator-card">
                    <div class="indicator-title">💵 Dólar (USD)</div>
                    <div class="indicator-value">${fmtMoeda(mercado.macro.dolar)}</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">🛢️ Petróleo Brent</div>
                    <div class="indicator-value">US$ ${fmtNum(mercado.macro.brent)}</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">📈 Ibovespa</div>
                    <!-- Alterado: Usa fmtInteiro para tirar o .125 -->
                    <div class="indicator-value">${fmtInteiro(mercado.macro.ibovespa)} pts</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">🏦 Taxa Selic (Anualizada)</div>
                    <!-- Alterado: Adiciona % a.a. -->
                    <div class="indicator-value">${fmtNum(mercado.macro.selic)}% a.a.</div>
                </div>
            </div>

            <!-- 3. Grid de Indicadores Técnicos -->
            <h3 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem;">
                📊 Indicadores Técnicos Calculados
            </h3>
            <div class="indicators-grid">
                <div class="indicator-card">
                    <div class="indicator-title">RSI (Força Relativa)</div>
                    <div class="indicator-value" style="color: ${mercado.tecnicos.rsi > 70 ? '#dc2626' : mercado.tecnicos.rsi < 30 ? '#16a34a' : '#1e293b'}">
                        ${fmtNum(mercado.tecnicos.rsi)}
                    </div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">MACD</div>
                    <div class="indicator-value">${fmtNum(mercado.tecnicos.macd)}</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">Volatilidade (ATR)</div>
                    <div class="indicator-value">${fmtNum(mercado.tecnicos.volatilidade_atr)}</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">Tendência (SMA200)</div>
                    <div class="indicator-value">${mercado.tecnicos.tendencia_sma200}</div>
                </div>
            </div>

            <!-- 4. Explicação Metodológica (O que o usuário pediu) -->
            <div class="methodology-box">
                <h4 style="margin-top:0; color: #1e40af;">🧠 Entenda como a IA processou esses dados</h4>
                <div class="methodology-grid">
                    <div class="method-item">
                        <h5>📉 Retorno Logarítmico (Log Return)</h5>
                        <p>O modelo não prevê o preço absoluto (ex: R$ 40), mas sim o <em>logaritmo do retorno</em> diário. Isso torna a série temporal estacionária e melhora a estabilidade matemática da rede neural LSTM.</p>
                    </div>
                    <div class="method-item">
                        <h5>⏳ Janelas Móveis (Rolling Windows)</h5>
                        <p>Utilizamos médias móveis de 20 dias (curto prazo) e 200 dias (longo prazo) para capturar a tendência. O modelo "olha" para os últimos 20 dias de histórico para prever o dia seguinte.</p>
                    </div>
                    <div class="method-item">
                        <h5>⚡ Volatilidade & Sazonalidade</h5>
                        <p>Indicadores como Bandas de Bollinger e ATR medem o risco. Também inserimos dados cíclicos (Seno/Cosseno) para ensinar à IA sobre padrões semanais e mensais.</p>
                    </div>
                </div>
            </div>

            <!-- 5. Tabela de Previsão -->
            <h3 class="section-title" style="font-size: 1.4rem; margin-top: 2rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">
                🚀 Previsão do Modelo
            </h3>
            <table>
                <thead>
                    <tr>
                        <th>Data Futura</th>
                        <th>Preço Previsto</th>
                        <th>Tendência*</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Loop das previsões
    let precoAnterior = mercado.preco_atual;
    data.previsoes.forEach(previsao => {
        const variacao = ((previsao.preco_previsto - precoAnterior) / precoAnterior) * 100;
        const corVar = variacao >= 0 ? '#16a34a' : '#dc2626';
        const icone = variacao >= 0 ? '▲' : '▼';
        
        html += `
            <tr>
                <td>${previsao.data_previsao}</td>
                <td style="font-weight: bold; font-size: 1.1rem;">${fmtMoeda(previsao.preco_previsto)}</td>
                <td style="color: ${corVar}; font-weight: 600;">
                    ${icone} ${Math.abs(variacao).toFixed(2)}%
                </td>
            </tr>
        `;
        precoAnterior = previsao.preco_previsto;
    });
    
    html += `
                </tbody>
            </table>
            <p style="font-size: 0.8rem; color: #94a3b8; text-align: center; margin-top: 1rem;">
                * A tendência é comparada em relação ao dia anterior previsto. <br>
                Modelo: ${data.modelo_usado} | Processado em: ${new Date(data.data_geracao).toLocaleTimeString()}
            </p>
        </div>
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