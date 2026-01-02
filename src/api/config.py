import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminho onde ficam os artefatos (.keras, .pkl)
# Ajuste conforme sua estrutura real, ex: ../models
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_FILENAME = "lstm_petr4_final.keras"
SCALER_X_FILENAME = "scaler_x_final.pkl"
SCALER_Y_FILENAME = "scaler_y_final.pkl"

MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILENAME)
SCALER_X_PATH = os.path.join(MODELS_DIR, SCALER_X_FILENAME)
SCALER_Y_PATH = os.path.join(MODELS_DIR, SCALER_Y_FILENAME)

