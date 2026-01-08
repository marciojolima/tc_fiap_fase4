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

# --- MONITORAMENTO DE NEGÓCIO (Existente) ---
PREDICTION_VALUE_HIST = Histogram('model_prediction_price_brl', 'Distribuição preços (R$)', buckets=[25, 30, 35, 40, 45])
CONFIDENCE_GAUGE = Gauge('model_last_confidence_score', 'Confiança')
DIRECTION_COUNTER = Counter('model_prediction_direction_total', 'Direção', ['direction'])
INPUT_PRICE_GAUGE = Gauge('model_input_current_price', 'Preço Input')

# --- NOVO: MONITORAMENTO DE PERFORMANCE REAL (Shadow Test) ---
REAL_ERROR_GAUGE = Gauge('model_real_error_abs', 'Erro Real Instantâneo (R$): Preço Hoje - Previsão Shadow')
REAL_ACCURACY_HIST = Histogram('model_real_accuracy_percentage', 'Erro Percentual Real (%)', buckets=[0.01, 0.02, 0.05, 0.10])

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
        # 1. Pipeline (Agora retorna 50 linhas)
        features_full_df, p_close_full_series = pipeline.prepare_input_data()
        
        # Preço Atual Real (Último fechamento conhecido)
        preco_atual_real = p_close_full_series.iloc[-1]
        INPUT_PRICE_GAUGE.set(preco_atual_real)
        
        previsoes = []
        
        if lstm_model and scaler_x and scaler_y:
            try:
                # --- PREPARAÇÃO DOS DADOS ---
                # Precisamos escalar tudo de uma vez para ser eficiente
                if hasattr(scaler_x, 'feature_names_in_'):
                    cols_to_scale = scaler_x.feature_names_in_
                else:
                    cols_to_scale = features_full_df.columns

                X_full_df = features_full_df.copy()
                valid_cols = [c for c in cols_to_scale if c in X_full_df.columns]
                X_full_df[valid_cols] = scaler_x.transform(X_full_df[valid_cols])
                X_values = X_full_df.values

                # --- A. SHADOW TESTING (Avaliação em Tempo Real) ---
                # Objetivo: Prever o preço de HOJE usando os dados de ONTEM para trás.
                # Recorte: Linhas -21 até -1 (20 dias anteriores ao atual)
                # Alvo: Preço Atual Real
                try:
                    X_shadow = X_values[-21:-1].reshape(1, 20, X_values.shape[1])
                    
                    # Inferência Shadow
                    pred_shadow_scaled = lstm_model.predict(X_shadow, verbose=0)
                    log_ret_shadow = scaler_y.inverse_transform(pred_shadow_scaled)[0][0]
                    
                    # Preço Base para a sombra = Preço de Ontem (iloc[-2])
                    price_yesterday = p_close_full_series.iloc[-2]
                    price_shadow_prediction = price_yesterday * np.exp(log_ret_shadow)
                    
                    # CÁLCULO DO ERRO REAL
                    erro_reais = preco_atual_real - price_shadow_prediction
                    erro_percentual = abs(erro_reais / preco_atual_real)
                    
                    # Log no Prometheus
                    REAL_ERROR_GAUGE.set(erro_reais)
                    REAL_ACCURACY_HIST.observe(erro_percentual)
                    
                    # (Opcional) Print no log para você ver acontecendo
                    # print(f"🔍 Shadow Test: Real={preco_atual_real:.2f} | Previsto={price_shadow_prediction:.2f} | Erro={erro_reais:.2f}")
                    
                except Exception as shadow_e:
                    print(f"⚠️ Erro no Shadow Test (não afeta usuário): {shadow_e}")

                # --- B. PREVISÃO OFICIAL (Para o Usuário) ---
                # Objetivo: Prever AMANHÃ usando dados até HOJE.
                # Recorte: Últimas 20 linhas (-20 até fim)
                X_user = X_values[-20:].reshape(1, 20, X_values.shape[1])
                
                pred_user_scaled = lstm_model.predict(X_user, verbose=0)
                log_ret_user = scaler_y.inverse_transform(pred_user_scaled)[0][0]
                price_d1 = preco_atual_real * np.exp(log_ret_user)
                
                # --- PROJEÇÃO DIAS SEGUINTES ---
                fator_tendencia = np.exp(log_ret_user)
                
                contexto_visual = market_service.get_current_context()
                data_ref = datetime.strptime(contexto_visual['data_referencia'], '%Y-%m-%d')
                
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
                print(f"⚠️ Erro ML Crítico: {ml_err}")
                raise ml_err
        else:
            raise HTTPException(status_code=503, detail="Modelo ML não carregado.")

        # Métricas Finais
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
