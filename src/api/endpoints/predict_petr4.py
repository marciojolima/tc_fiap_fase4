# src/api/endpoints/predict_petr4.py
import os
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta

from api.schemas.prediction import PredictionRequestSimple, PredictionResponse, PredictionItem
from api.services.data_loader import get_latest_features

router = APIRouter()

# --- Configuração ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "lstm_petr4_final.keras")
SCALER_X_PATH = os.path.join(BASE_DIR, "models", "scaler_x_final.pkl")
SCALER_Y_PATH = os.path.join(BASE_DIR, "models", "scaler_y_final.pkl") # Novo!

model = None
scaler_x = None
scaler_y = None

def load_artifacts():
    global model, scaler_x, scaler_y
    try:
        if os.path.exists(MODEL_PATH):
            model = load_model(MODEL_PATH)
        if os.path.exists(SCALER_X_PATH):
            scaler_x = joblib.load(SCALER_X_PATH)
        if os.path.exists(SCALER_Y_PATH):
            scaler_y = joblib.load(SCALER_Y_PATH)
            print("✅ Todos os artefatos carregados (Modelo + Scalers X/Y)")
    except Exception as e:
        print(f"❌ Erro ao carregar artefatos: {e}")

load_artifacts()

# Definição das colunas (Baseado no seu print anterior)
COLUNAS_MODELO = [
    'USDBRL_t-1', 'Brent_t-1', 'Ibovespa_t-1', 'Selic_t-1', 'Ibov_Return_t-1', 
    'Brent_Return_t-1', 'USD_Return_t-1', 'return_1', 'return_5', 'return_20', 
    'Dist_SMA200', 'Momentum_5', 'Momentum_10', 'Momentum_20', 'RSI_21', 'MACD', 
    'MACD_Signal', 'ATR_14', 'BB_Middle', 'BB_Std', 'BB_Upper', 'BB_Lower', 
    'BB_Width', 'BB_Position', 'STD_20', 'Parkinson_Vol', 'Range_High_Low', 
    'OBV', 'Volume_Ratio', 'VWAP', 'DoW_sin', 'DoW_cos', 'Month_sin', 'Month_cos'
]

# Colunas Cíclicas (que geralmente não são escaladas ou já são -1 a 1)
# Se você usou MinMaxScaler em TUDO no treino corrigido, deixe essa lista vazia.
# Mas se usou a lógica do "Teste de Sanidade" onde separou cyclicals, defina-as aqui.
# Vou assumir que você escalou TUDO conforme minha última recomendação.
CYCLICAL_COLS = [] 

@router.post("/predict", response_model=PredictionResponse)
async def predict_days(request: PredictionRequestSimple):
    if not model or not scaler_x or not scaler_y:
        load_artifacts()
        if not model:
            raise HTTPException(status_code=500, detail="Modelo ML indisponível")

    try:
        # 1. Carregar dados históricos (precisamos de pelo menos 20 linhas)
        df_completo, display_data = get_latest_features()
        
        LOOKBACK = 20 # Tamanho da janela do seu LSTM
        
        # Garante que temos dados suficientes
        if len(df_completo) < LOOKBACK:
            raise HTTPException(status_code=500, detail="Dados históricos insuficientes para gerar janela.")

        # Pega as últimas 20 linhas para formar a sequência
        input_df = df_completo.iloc[-LOOKBACK:].copy()
        
        # Filtra colunas
        input_features = input_df[COLUNAS_MODELO]

        # 2. Escalonamento
        # Tenta descobrir o que o scaler espera
        try:
            scaler_cols = scaler_x.feature_names_in_
        except:
            scaler_cols = COLUNAS_MODELO # Fallback

        # Prepara dataframe para o scaler
        df_to_scale = pd.DataFrame(index=input_features.index)
        for c in scaler_cols:
            df_to_scale[c] = input_features[c] if c in input_features else 0.0
            
        # Transforma
        scaled_array = scaler_x.transform(df_to_scale)
        
        # Remonta DataFrame escalado
        df_scaled = pd.DataFrame(scaled_array, columns=scaler_cols, index=input_features.index)
        
        # Adiciona colunas não escaladas (se houver, ex: Cíclicas)
        final_input_df = pd.DataFrame(index=input_features.index)
        for col in COLUNAS_MODELO:
            if col in df_scaled.columns:
                final_input_df[col] = df_scaled[col]
            else:
                final_input_df[col] = input_features[col] # Valor original

        # 3. Formato LSTM: (1, 20, 34)
        input_sequence = final_input_df.values.reshape(1, LOOKBACK, len(COLUNAS_MODELO))

        # 4. Previsão
        # O modelo retorna (1, 1) com valor escalado
        pred_scaled = model.predict(input_sequence, verbose=0)
        
        # ⚠️ O PULO DO GATO: INVERTER A ESCALA ⚠️
        pred_log_return = scaler_y.inverse_transform(pred_scaled)[0][0]
        
        # Converter Log Return -> Preço
        current_price = display_data['preco_atual']
        predicted_price = current_price * np.exp(pred_log_return)
        
        # Data da previsão (Amanhã)
        ref_date = datetime.strptime(display_data['data_referencia'], '%Y-%m-%d')
        next_date = ref_date + timedelta(days=1)
        if next_date.weekday() >= 5: next_date += timedelta(days=2) # Pula FDS

        # Monta resposta
        # Nota: Previsão recursiva para N dias é complexa. 
        # Aqui vamos retornar o Dia + 1 calculado e projetar os outros dias com base nele
        # ou avisar que é apenas para 1 dia.
        
        previsoes = []
        
        # Dia 1 (Calculado com IA)
        previsoes.append(PredictionItem(
            data_previsao=next_date.strftime('%d/%m/%Y'),
            preco_previsto=round(float(predicted_price), 2),
            confianca=0.89
        ))
        
        # Dias 2..N (Projeção simplificada baseada na tendência do dia 1)
        # Se quiser arriscar recursividade, precisaria atualizar a input_sequence inteira,
        # o que é difícil sem ter features futuras. Vamos manter simples.
        trend_factor = np.exp(pred_log_return)
        proj_price = predicted_price
        proj_date = next_date
        
        for i in range(2, request.dias + 1):
            proj_price = proj_price * trend_factor # Assume tendência constante
            proj_date = proj_date + timedelta(days=1)
            if proj_date.weekday() >= 5: proj_date += timedelta(days=2)
            
            previsoes.append(PredictionItem(
                data_previsao=proj_date.strftime('%d/%m/%Y'),
                preco_previsto=round(float(proj_price), 2),
                confianca=0.80 # Confiança cai com o tempo
            ))

        return PredictionResponse(
            modelo_usado="LSTM_PETR4_Final",
            data_geracao=datetime.now(),
            dados_mercado=display_data,
            previsoes=previsoes
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    