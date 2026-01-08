import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from prometheus_client import Histogram, Gauge, Counter

from src.api.schemas.prediction import PredictionRequestSimple, PredictionResponse, PredictionItem
from src.api.services.market_data import market_service
from src.api.services.feature_pipeline import pipeline
from src.api.config import MODEL_PATH, SCALER_X_PATH, SCALER_Y_PATH

router = APIRouter(tags=["Previsão"])

# --- MONITORAMENTO ---
PREDICTION_VALUE_HIST = Histogram('model_prediction_price_brl', 'Distribuição preços (R$)', buckets=[25, 30, 35, 40, 45])
CONFIDENCE_GAUGE = Gauge('model_last_confidence_score', 'Confiança')
DIRECTION_COUNTER = Counter('model_prediction_direction_total', 'Direção', ['direction'])
INPUT_PRICE_GAUGE = Gauge('model_input_current_price', 'Preço Input')

# --- CARREGAMENTO ML ---
lstm_model = None
scaler_x = None
scaler_y = None

def load_ml_artifacts():
    global lstm_model, scaler_x, scaler_y
    try:
        if os.path.exists(MODEL_PATH):
            lstm_model = tf.keras.models.load_model(MODEL_PATH)
            print(f"✅ LSTM Real carregada: {MODEL_PATH}")
        if os.path.exists(SCALER_X_PATH):
            scaler_x = joblib.load(SCALER_X_PATH)
        if os.path.exists(SCALER_Y_PATH):
            scaler_y = joblib.load(SCALER_Y_PATH)
    except Exception as e:
        print(f"❌ Erro ML: {e}")

load_ml_artifacts()

@router.post("/predict", response_model=PredictionResponse)
async def predict_future(request: PredictionRequestSimple):
    """Este endpoint:
    1. 📥 Recebe a quantidade de dias (máx 5).
    2. 🌍 **Baixa automaticamente** os dados mais recentes do mercado (Yahoo Finance).
    3. 🧠 Alimenta a Rede Neural LSTM.
    4. 📤 Retorna a projeção de preço e indicadores técnicos.
    """    
    try:
        # 1. Pipeline de Engenharia de Dados (REAL)
        features_df, preco_atual_real = pipeline.prepare_input_data()
        
        INPUT_PRICE_GAUGE.set(preco_atual_real)
        
        # Contexto para resposta
        contexto_visual = market_service.get_current_context()
        data_ref = datetime.strptime(contexto_visual['data_referencia'], '%Y-%m-%d')
        
        previsoes = []
        
        if lstm_model and scaler_x and scaler_y:
            try:
                # --- CORREÇÃO DO ESCALONAMENTO ---
                # O Scaler foi treinado apenas num subconjunto de colunas (as não cíclicas).
                # Precisamos escalar SÓ o que ele conhece e manter o resto igual.
                
                # 1. Descobrir quais colunas o scaler espera
                if hasattr(scaler_x, 'feature_names_in_'):
                    cols_to_scale = scaler_x.feature_names_in_
                else:
                    # Fallback se foi treinado sem nomes (raro com pandas)
                    cols_to_scale = features_df.columns 

                # 2. Criar uma cópia para não bagunçar o original
                X_final_df = features_df.copy()
                
                # 3. Filtrar apenas as colunas que existem no DF atual e no Scaler
                # Isso evita erro se faltar alguma coluna obscura
                valid_cols = [c for c in cols_to_scale if c in X_final_df.columns]
                
                if not valid_cols:
                    raise ValueError("Nenhuma coluna compatível encontrada entre Pipeline e Scaler.")

                # 4. Transformar APENAS essas colunas
                X_final_df[valid_cols] = scaler_x.transform(X_final_df[valid_cols])
                
                # Nota: As colunas que NÃO estavam em valid_cols (ex: DoW_sin) 
                # permanecem com seus valores originais no X_final_df, 
                # exatamente como feito no notebook (X_train_scaled[cols] = ...)

                # --- FIM DA CORREÇÃO ---

                # B. Reshape para LSTM
                # Garante que usamos TODAS as colunas na ordem que o Pipeline definiu (que deve bater com o treino)
                # O DataFrame X_final_df agora tem colunas mistas (escaladas e não escaladas)
                X_values = X_final_df.values
                X_input = X_values.reshape(1, 20, X_values.shape[1])
                
                # C. Inferência
                pred_scaled = lstm_model.predict(X_input, verbose=0)
                
                # D. Desescalar e Calcular
                log_return_pred = scaler_y.inverse_transform(pred_scaled)[0][0]
                price_d1 = preco_atual_real * np.exp(log_return_pred)
                
                # Projeção de Tendência para dias seguintes
                fator_tendencia = np.exp(log_return_pred)
                
                proj_price = preco_atual_real
                for i in range(1, request.dias + 1):
                    if i == 1:
                        proj_price = price_d1
                    else:
                        proj_price = proj_price * fator_tendencia
                    
                    confianca = max(0.40, 0.55 - ((i - 1) * 0.04))
                    next_date = data_ref + timedelta(days=i)
                    if next_date.weekday() >= 5: next_date += timedelta(days=2)
                    
                    PREDICTION_VALUE_HIST.observe(proj_price)
                    
                    previsoes.append(PredictionItem(
                        data_previsao=next_date.strftime('%d/%m/%Y'),
                        preco_previsto=round(float(proj_price), 2),
                        confianca=round(confianca, 2)
                    ))

            except Exception as ml_err:
                print(f"⚠️ Erro ML Detalhado: {ml_err}")
                # Re-lança para cair no catch global ou usar fallback se quisesse
                raise ml_err
        else:
            raise HTTPException(status_code=503, detail="Modelo ML não carregado.")

        # Atualiza métricas
        CONFIDENCE_GAUGE.set(previsoes[0].confianca)
        dir_str = "alta" if previsoes[0].preco_previsto > preco_atual_real else "baixa"
        DIRECTION_COUNTER.labels(direction=dir_str).inc()

        return PredictionResponse(
            modelo_usado="LSTM_PETR4_Prod_Real_v1",
            data_geracao=datetime.now(),
            dados_mercado=contexto_visual,
            previsoes=previsoes
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
