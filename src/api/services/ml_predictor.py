import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from api.config import MODEL_PATH, SCALER_X_PATH, SCALER_Y_PATH
from api.schemas.prediction import PredictionRequest, PredictionResponse
from datetime import datetime, timedelta

class Petr4Predictor:
    def __init__(self):
        self.model = None
        self.scaler_x = None
        self.scaler_y = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Carrega modelo e scalers na memória"""
        try:
            print(f"Loading ML artifacts from {MODEL_PATH}...")
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.scaler_x = joblib.load(SCALER_X_PATH)
            self.scaler_y = joblib.load(SCALER_Y_PATH)
            print("✅ ML Artifacts loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load ML artifacts: {e}")
            self.model = None # Flag de erro

    def predict_next_day(self, request: PredictionRequest) -> PredictionResponse:
        """
        Executa todo o pipeline de previsão:
        Dados Brutos -> DataFrame -> Normalização -> Predição -> Desnormalização -> Resposta
        """
        if not self.model:
            raise RuntimeError("Model is not loaded properly.")

        # 1. Converter entrada para DataFrame
        input_data = [d.features for d in request.historico]
        df_input = pd.DataFrame(input_data)

        # 2. Validação de Shape
        expected_features = self.scaler_x.n_features_in_
        if df_input.shape[1] != expected_features:
            raise ValueError(f"Feature mismatch. Expected {expected_features}, got {df_input.shape[1]}")

        # 3. Escalonamento (Normalização)
        X_scaled = self.scaler_x.transform(df_input)

        # 4. Reshape para LSTM (1, 20, N)
        X_final = X_scaled.reshape(1, 20, X_scaled.shape[1])

        # 5. Inferência
        y_pred_scaled = self.model.predict(X_final, verbose=0)

        # 6. Pós-processamento (Inverter escala)
        log_return_pred = self.scaler_y.inverse_transform(y_pred_scaled)[0][0]

        # 7. Cálculo Financeiro
        preco_previsto = request.ultimo_preco_fechamento * np.exp(log_return_pred)
        direcao = "ALTA" if log_return_pred > 0 else "BAIXA"

        return PredictionResponse(
            simbolo="PETR4.SA",
            data_previsao=datetime.now() + timedelta(days=1),
            preco_previsto=round(float(preco_previsto), 2),
            log_return_previsto=float(log_return_pred),
            direcao=direcao
        )

# Instância Global (Singleton)
# Ao importar este arquivo, o Python instância a classe e carrega o modelo na RAM
predictor_service = Petr4Predictor()
