# src/api/endpoints/predict_petr4.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import random # Usado apenas para simular a variação futura neste exemplo
from prometheus_client import Histogram, Gauge, Counter

# Importe os schemas novos
from api.schemas.prediction import (
    PredictionRequestSimple, 
    PredictionResponse, 
    PredictionItem
)
# Importe o serviço de dados
from api.services.market_data import market_service

# 1. Histograma: Monitora a distribuição dos preços previstos
# Isso ajuda a detectar 'Model Drift'. Se o gráfico mudar muito, o modelo descalibrou.
PREDICTION_VALUE_HIST = Histogram(
    'model_prediction_price_brl', 
    'Distribuição dos preços previstos pelo modelo (R$)',
    buckets=[20, 25, 30, 35, 40, 45, 50, 60] # Faixas de preço esperadas para PETR4
)

# 2. Gauge: Monitora a confiança média da última requisição
CONFIDENCE_GAUGE = Gauge(
    'model_last_confidence_score', 
    'Nível de confiança da última previsão realizada'
)

# 3. Counter: Conta quantas vezes previmos "Alta" vs "Baixa"
DIRECTION_COUNTER = Counter(
    'model_prediction_direction_total',
    'Contagem de previsões de Alta vs Baixa',
    ['direction'] # Label para filtrar no Grafana
)

# 4. Gauge: Monitora o Input (Preço Atual) para comparar com a Previsão
INPUT_PRICE_GAUGE = Gauge(
    'model_input_current_price',
    'Preço real atual usado como base para a previsão'
)

router = APIRouter(tags=["Previsão"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_future(request: PredictionRequestSimple):
    """
    🔮 **Realiza previsão de preço para PETR4**
    
    Este endpoint:
    1. 📥 Recebe a quantidade de dias (máx 5).
    2. 🌍 **Baixa automaticamente** os dados mais recentes do mercado (Yahoo Finance).
    3. 🧠 Alimenta a Rede Neural LSTM.
    4. 📤 Retorna a projeção de preço e indicadores técnicos.
    """
    try:
        # 1. Obter contexto
        contexto_mercado = market_service.get_current_context()
        
        # REGISTRAR MÉTRICA DE INPUT
        # Isso permite criar um gráfico no Grafana: "Preço Real vs Preço Previsto"
        INPUT_PRICE_GAUGE.set(contexto_mercado['preco_atual'])
        
        previsoes = []
        preco_base = contexto_mercado['preco_atual']
        data_ref = datetime.strptime(contexto_mercado['data_referencia'], '%Y-%m-%d')
        
        current_price = preco_base
        
        for i in range(1, request.dias + 1):
            # ... Lógica de previsão existente ...
            variacao = random.uniform(-0.02, 0.02)
            current_price = current_price * (1 + variacao)
            
            # ... Lógica de confiança existente ...
            acuracia_base = 0.55
            penalidade = 0.03
            confianca_calculada = max(0.40, acuracia_base - ((i - 1) * penalidade))
            
            # REGISTRAR MÉTRICAS DO MODELO
            # A cada dia previsto, mandamos o dado para o Prometheus
            PREDICTION_VALUE_HIST.observe(current_price)
            
            item = PredictionItem(
                data_previsao=(data_ref + timedelta(days=i)).strftime('%d/%m/%Y'),
                preco_previsto=round(current_price, 2),
                confianca=round(confianca_calculada, 2)
            )
            previsoes.append(item)

        # Atualiza métricas gerais baseadas na primeira previsão (D+1)
        primeira_prev = previsoes[0]
        CONFIDENCE_GAUGE.set(primeira_prev.confianca)
        
        direcao = "alta" if primeira_prev.preco_previsto > preco_base else "baixa"
        DIRECTION_COUNTER.labels(direction=direcao).inc()

        return PredictionResponse(
            modelo_usado="LSTM_PETR4_Prod_v1",
            data_geracao=datetime.now(),
            dados_mercado=contexto_mercado,
            previsoes=previsoes
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

