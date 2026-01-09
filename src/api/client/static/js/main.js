
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

// Renderiza o Dashboard
function mostrarResultado(data) {
    const resultadoDiv = document.getElementById('resultado');
    const mercado = data.dados_mercado;
    
    const dataRef = new Date(mercado.data_referencia + 'T00:00:00');
    const dataFormatada = dataRef.toLocaleDateString('pt-BR');
    
    const fmtMoeda = (valor) => {
        if (valor === undefined || valor === null) return "R$ --";
        return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    };
    
    const fmtNum = (valor) => {
        if (valor === undefined || valor === null) return "--";
        return valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };
    
    const fmtInteiro = (valor) => {
        if (valor === undefined || valor === null) return "--";
        return valor.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
    };

    // Cores dinâmicas
    const momColor = mercado.tecnicos.momentum_5d >= 0 ? '#16a34a' : '#dc2626'; 
    const momSinal = mercado.tecnicos.momentum_5d >= 0 ? '+' : '';

    let html = `
        <div class="market-dashboard">
            
            <!-- 1. Cabeçalho -->
            <div class="dashboard-header">
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">
                    📅 Dados de Fechamento: ${dataFormatada}
                </div>
                <div style="font-size: 2.5rem; font-weight: 700;">
                    ${fmtMoeda(mercado.preco_atual)}
                </div>
                <div>Último preço real da PETR4.SA utilizado como base.</div>
            </div>

            <!-- 2. Macroeconomia -->
            <h3 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem; color: #1e3a8a;">
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
                    <div class="indicator-value">${fmtInteiro(mercado.macro.ibovespa)} pts</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">🏦 Taxa Selic (Anualizada)</div>
                    <div class="indicator-value">${fmtNum(mercado.macro.selic)}% a.a.</div>
                </div>
            </div>

            <!-- 3. Indicadores Técnicos -->
            <h3 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem; color: #1e3a8a;">
                📊 Indicadores Técnicos Calculados
            </h3>
            
            <!-- Linha 1 -->
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

            <!-- Linha 2 (NOVOS INDICADORES) -->
            <div class="indicators-grid" style="margin-top: 10px;">
                <div class="indicator-card">
                    <div class="indicator-title">Momentum (5d)</div>
                    <div class="indicator-value" style="color: ${momColor}">
                        ${momSinal}${fmtMoeda(mercado.tecnicos.momentum_5d)}
                    </div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">Bollinger (%B)</div>
                    <div class="indicator-value">${fmtNum(mercado.tecnicos.bb_posicao)}%</div>
                </div>
                <div class="indicator-card">
                    <div class="indicator-title">VWAP (Médio Pond.)</div>
                    <div class="indicator-value">${fmtMoeda(mercado.tecnicos.vwap)}</div>
                </div>
                 <!-- Card vazio para alinhar o grid (se for 4 colunas) -->
                <div class="indicator-card" style="visibility: hidden;"></div>
            </div>

            <!-- 4. Metodologia -->
            <div class="methodology-box">
                <h4 style="margin-top:0; color: #1e40af;">🧠 Entenda como a IA processou esses dados</h4>
                <div class="methodology-grid">
                    <div class="method-item">
                        <h5>📉 Retorno Logarítmico</h5>
                        <p>O modelo prevê o <em>logaritmo do retorno</em> diário para garantir estacionariedade matemática.</p>
                    </div>
                    <div class="method-item">
                        <h5>⏳ Janelas Móveis</h5>
                        <p>Médias de 20 e 200 dias capturam tendências. O VWAP pondera pelo volume.</p>
                    </div>
                    <div class="method-item">
                        <h5>⚡ Volatilidade</h5>
                        <p>Bandas de Bollinger e ATR indicam o risco. Momentum mede a velocidade.</p>
                    </div>
                </div>
            </div>

            <!-- 5. Tabela de Previsão -->
            <h3 class="section-title" style="font-size: 1.4rem; margin-top: 2rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; color: #1e3a8a;">
                🚀 Previsão do Modelo
            </h3>
            <table>
                <thead>
                    <tr>
                        <th>Data Futura</th>
                        <th>Preço Previsto</th>
                        <th>Tendência*</th>
                        <th>Confiança</th>
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
        
        const confPct = Math.round(previsao.confianca * 100);
        
        html += `
            <tr>
                <td>${previsao.data_previsao}</td>
                <td style="font-weight: bold; font-size: 1.1rem;">${fmtMoeda(previsao.preco_previsto)}</td>
                <td style="color: ${corVar}; font-weight: 600;">
                    ${icone} ${Math.abs(variacao).toFixed(2)}%
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <div style="width: 50px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
                            <div style="width: ${confPct}%; height: 100%; background: #2563eb;"></div>
                        </div>
                        <span style="font-size: 0.8rem;">${confPct}%</span>
                    </div>
                </td>
            </tr>
        `;
        precoAnterior = previsao.preco_previsto;
    });
    
    html += `
                </tbody>
            </table>
            <p style="font-size: 0.8rem; color: #94a3b8; text-align: center; margin-top: 1rem;">
                * A tendência é comparada em relação ao dia anterior. <br>
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
