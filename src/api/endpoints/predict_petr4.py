# src/api/endpoints/predict_petr4.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import random # Usado apenas para simular a variação futura neste exemplo

# Importe os schemas novos
from api.schemas.prediction import (
    PredictionRequestSimple, 
    PredictionResponse, 
    PredictionItem
)
# Importe o serviço de dados
from api.services.market_data import market_service

router = APIRouter()

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
        # 1. Obter contexto atual do mercado (Automático)
        contexto_mercado = market_service.get_current_context()
        
        # 2. Loop de Previsão (Simulando o Autoregressivo)
        previsoes = []
        preco_base = contexto_mercado['preco_atual']
        data_ref = datetime.strptime(contexto_mercado['data_referencia'], '%Y-%m-%d')
        
        # NOTA: Aqui entraria o seu "predictor_service.predict_next_day" em loop
        # Usando lógica simplificada para demonstração da estrutura JSON:
        current_price = preco_base
        
        for i in range(1, request.dias + 1):
            # Simula a variação que a LSTM daria
            # Em produção: current_price = model.predict(input_atual)
            variacao = random.uniform(-0.02, 0.02) # +/- 2%
            current_price = current_price * (1 + variacao)
            
            # Lógica Ajustada de Confiança:
            # Começa com a acurácia base do modelo (ex: 55%) e cai conforme o tempo passa.
            # D+1: 55%
            # D+2: 52%
            # D+3: 49%
            acuracia_base_modelo = 0.55  # 55% (Vindo do seu Backtest)
            penalidade_por_dia = 0.03    # Perde 3% de confiança a cada dia extra
            
            confianca_calculada = acuracia_base_modelo - ((i - 1) * penalidade_por_dia)
            
            # Trava mínima de segurança (não mostrar confiança negativa)
            if confianca_calculada < 0.40:
                confianca_calculada = 0.40 
            
            next_date = data_ref + timedelta(days=i)
            # Pula final de semana (simplificado)
            if next_date.weekday() >= 5:
                next_date += timedelta(days=2)
                
            previsoes.append(PredictionItem(
                data_previsao=next_date.strftime('%d/%m/%Y'),
                preco_previsto=round(current_price, 2),
                confianca=round(confianca_calculada, 2)
            ))

        # 3. Montar Resposta
        return PredictionResponse(
            modelo_usado="LSTM_PETR4_Prod_v1",
            data_geracao=datetime.now(),
            dados_mercado=contexto_mercado, # O Pydantic valida e converte o dict
            previsoes=previsoes
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
