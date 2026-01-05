from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PredictionRequestSimple(BaseModel):
    dias: int = Field(default=7, ge=1, le=30, description="Dias para prever")

class PredictionItem(BaseModel):
    data_previsao: str
    preco_previsto: float
    confianca: Optional[float] = None

class MacroData(BaseModel):
    dolar: float
    brent: float
    selic: float
    ibovespa: float

class TecnicosData(BaseModel):
    rsi: float
    macd: float
    volatilidade_atr: float
    tendencia_sma200: str

class DisplayData(BaseModel):
    preco_atual: float
    data_referencia: str
    macro: MacroData
    tecnicos: TecnicosData

class PredictionResponse(BaseModel):
    modelo_usado: str
    data_geracao: datetime
    dados_mercado: DisplayData
    previsoes: List[PredictionItem]
