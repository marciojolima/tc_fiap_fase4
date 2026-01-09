from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- SUB-MODELOS DE DADOS DE MERCADO ---

class MacroData(BaseModel):
    """Indicadores Macroeconômicos usados no modelo"""
    dolar: float = Field(..., description="Cotação atual do Dólar (USD/BRL)", example=5.52)
    brent: float = Field(..., description="Preço do Barril de Petróleo Brent", example=75.40)
    selic: float = Field(..., description="Taxa Selic atual (%)", example=11.25)
    ibovespa: float = Field(..., description="Pontuação do Índice Bovespa", example=128000.50)

class TecnicosData(BaseModel):
    """Indicadores de Análise Técnica calculados"""
    rsi: float = Field(..., description="Índice de Força Relativa (14 dias). >70: Sobrecompra, <30: Sobrevenda", ge=0, le=100, example=55.4)
    macd: float = Field(..., description="Convergência/Divergência de Médias Móveis", example=-0.05)
    volatilidade_atr: float = Field(..., description="Average True Range (Volatilidade média)", example=0.42)
    tendencia_sma200: str = Field(..., description="Tendência de longo prazo baseada na Média Móvel de 200 dias", example="Alta 🟢")

    # Novos campos devidamente tipados
    bb_posicao: float = Field(..., description="Posição do preço dentro das Bandas de Bollinger (%)", example=85.5)
    momentum_5d: float = Field(..., description="Variação do preço nos últimos 5 dias (R$)", example=1.25)
    vwap: float = Field(..., description="Preço Médio Ponderado por Volume", example=34.10)

class DisplayData(BaseModel):
    """Resumo dos dados de mercado utilizados para a previsão"""
    preco_atual: float = Field(..., description="Último preço de fechamento conhecido (R$)", example=34.50)
    data_referencia: str = Field(..., description="Data do último pregão considerado (YYYY-MM-DD)", example="2025-01-15")
    macro: MacroData
    tecnicos: TecnicosData

# --- MODELOS DE RESPOSTA PRINCIPAL ---

class PredictionItem(BaseModel):
    """Previsão individual por dia"""
    data_previsao: str = Field(..., description="Data alvo da previsão (DD/MM/YYYY)", example="16/01/2025")
    preco_previsto: float = Field(..., description="Preço de fechamento estimado (R$)", example=34.90)
    confianca: Optional[float] = Field(None, description="Grau de confiança estatística (0.0 a 1.0)", ge=0, le=1, example=0.89)

class PredictionResponse(BaseModel):
    """Objeto raiz de resposta da API"""
    modelo_usado: str = Field(..., description="Identificador do modelo utilizado", example="LSTM_PETR4_Final_v1")
    data_geracao: datetime = Field(..., description="Timestamp de quando a previsão foi calculada")
    dados_mercado: DisplayData = Field(..., description="Contexto de mercado utilizado como base")
    previsoes: List[PredictionItem] = Field(..., description="Lista de previsões para os próximos dias")

    # Exemplo atualizado para o Swagger UI
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "modelo_usado": "LSTM_PETR4_Final",
            "data_geracao": "2025-01-15T10:30:00",
            "dados_mercado": {
                "preco_atual": 34.50,
                "data_referencia": "2025-01-14",
                "macro": {
                    "dolar": 5.50,
                    "brent": 75.20,
                    "selic": 11.25,
                    "ibovespa": 128500
                },
                "tecnicos": {
                    "rsi": 45.2,
                    "macd": 0.12,
                    "volatilidade_atr": 0.55,
                    "tendencia_sma200": "Alta 🟢",
                    "bb_posicao": 85.5,
                    "momentum_5d": 1.25,
                    "vwap": 34.10
                }
            },
            "previsoes": [
                {"data_previsao": "15/01/2025", "preco_previsto": 34.80, "confianca": 0.92},
                {"data_previsao": "16/01/2025", "preco_previsto": 35.10, "confianca": 0.85}
            ]
        }
    })

# --- MODELO DE REQUISIÇÃO ---

class PredictionRequestSimple(BaseModel):
    """Parâmetros de entrada para solicitação de previsão"""
    dias: int = Field(
        default=3, 
        ge=1, 
        le=5, 
        description="Número de dias futuros para prever."
    )
