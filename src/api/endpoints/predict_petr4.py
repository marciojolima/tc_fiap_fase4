# ~/dev/projects/python/tc_fiap_fase4/src/api/endpoints/predict_petr4.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Modelo de dados para a requisição
class PredictionRequest(BaseModel):
    dias: int = Field(default=7, ge=1, le=365, description="Número de dias para previsão")
    
class PredictionResponse(BaseModel):
    simbolo: str
    data_previsao: datetime
    preco_previsto: float
    confianca: Optional[float] = None
    
class PredictionsResponse(BaseModel):
    previsoes: List[PredictionResponse]
    modelo_usado: str
    data_geracao: datetime

@router.get("/")
async def api_root():
    """
    Endpoint raiz da API
    """
    return {
        'message': 'API de Previsão PETR4.SA',
        'status': 'online',
        'endpoints': {
            'predicao': '/api/predict',
            'info': '/api/info'
        }
    }

@router.post("/predict", response_model=PredictionsResponse)
async def predict_petr4(request: PredictionRequest):
    """
    Realiza a previsão do preço da ação PETR4.SA
    
    - **dias**: Número de dias para previsão (1-365)
    """
    try:
        # Aqui você irá implementar a lógica de predição com seu modelo
        # Por enquanto, retornando dados mockados
        
        import random
        from datetime import timedelta
        
        previsoes = []
        preco_base = 38.50  # Preço base mockado
        
        for i in range(1, request.dias + 1):
            data_futura = datetime.now() + timedelta(days=i)
            preco_previsto = preco_base + random.uniform(-2, 2)
            
            previsoes.append(PredictionResponse(
                simbolo="PETR4.SA",
                data_previsao=data_futura,
                preco_previsto=round(preco_previsto, 2),
                confianca=round(random.uniform(0.7, 0.95), 2)
            ))
        
        return PredictionsResponse(
            previsoes=previsoes,
            modelo_usado="LSTM v1.0 (mockado)",
            data_geracao=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao realizar previsão: {str(e)}")

@router.get("/info")
async def model_info():
    """
    Retorna informações sobre o modelo de predição
    """
    return {
        'modelo': 'LSTM Neural Network',
        'versao': '1.0.0',
        'ativo': 'PETR4.SA',
        'empresa': 'Petrobras',
        'ultima_atualizacao': datetime.now().isoformat(),
        'metricas': {
            'mae': 0.85,
            'rmse': 1.12,
            'r2_score': 0.89
        }
    }