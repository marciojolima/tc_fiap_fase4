import yfinance as yf
import pandas as pd
import numpy as np
import requests
import math
from datetime import datetime, timedelta

class MarketDataService:
    
    def _get_selic_real(self):
        """Busca a taxa Selic atualizada"""
        try:
            hoje = datetime.now()
            inicio = hoje - timedelta(days=15)
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial={inicio.strftime('%d/%m/%Y')}&dataFinal={hoje.strftime('%d/%m/%Y')}"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                val = float(response.json()[-1]['valor'])
                return val
        except:
            pass
        return 15.0 # Fallback

    def _sanitize_float(self, value, default=0.0):
        """
        Remove NaNs e Infinitos que quebram o JSON.
        """
        if value is None:
            return default
        try:
            val_float = float(value)
            if math.isnan(val_float) or math.isinf(val_float):
                return default
            return val_float
        except:
            return default

    def get_current_context(self):
        """
        Calcula indicadores técnicos expandidos para exibição no Frontend.
        """
        tickers = ["PETR4.SA", "BRL=X", "BZ=F", "^BVSP"]
        # Baixamos um pouco mais de histórico para garantir precisão das médias longas
        df_all = yf.download(tickers, period="2y", progress=False)
        closes = df_all['Close']

        def get_last(symbol):
            try:
                return self._sanitize_float(closes[symbol].ffill().iloc[-1])
            except:
                return 0.0

        # --- CÁLCULOS TÉCNICOS ---
        petr = closes['PETR4.SA'].ffill().dropna()
        
        # 1. RSI
        delta = petr.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 2. MACD
        ema12 = petr.ewm(span=12, adjust=False).mean()
        ema26 = petr.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        
        # 3. Bollinger Bands (Novo)
        sma20 = petr.rolling(20).mean()
        std20 = petr.rolling(20).std()
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        # Posição % dentro da banda (0 = fundo, 1 = topo, >1 = estourou pra cima)
        bb_pos = (petr - bb_lower) / (bb_upper - bb_lower)

        # 4. Momentum 5 Dias (Novo)
        momentum5 = petr - petr.shift(5)

        # 5. VWAP (Novo - Simplificado 1 mês para display)
        # Nota: O modelo usa histórico longo, mas para display curto prazo faz mais sentido
        try:
            petr_vol = df_all['Volume']['PETR4.SA'].ffill()
            petr_high = df_all['High']['PETR4.SA'].ffill()
            petr_low = df_all['Low']['PETR4.SA'].ffill()
            
            # VWAP Simplificada (Típico do dia)
            typ_price = (petr_high + petr_low + petr) / 3
            cum_vol = petr_vol.tail(20).cumsum() # Últimos 20 dias
            cum_vol_price = (typ_price * petr_vol).tail(20).cumsum()
            vwap = cum_vol_price / cum_vol
            vwap_val = vwap.iloc[-1]
        except:
            vwap_val = 0.0

        # 6. ATR e Tendência
        # (Mantendo lógica simplificada de display para não pesar)
        tr = (petr_high - petr_low).rolling(14).mean() # Simplificado
        sma200 = petr.rolling(200).mean()
        
        last_price = petr.iloc[-1]
        tendencia = "Alta 🟢" if last_price > sma200.iloc[-1] else "Baixa 🔴"

        # --- RETORNO ---
        return {
            "preco_atual": float(round(self._sanitize_float(last_price), 2)),
            "data_referencia": datetime.now().strftime('%Y-%m-%d'),
            "macro": {
                "dolar": float(round(self._sanitize_float(get_last('BRL=X')), 2)),
                "brent": float(round(self._sanitize_float(get_last('BZ=F')), 2)),
                "selic": float(self._sanitize_float(self._get_selic_real())),
                "ibovespa": float(round(self._sanitize_float(get_last('^BVSP')), 2))
            },
            "tecnicos": {
                "rsi": float(round(self._sanitize_float(rsi.iloc[-1]), 2)),
                "macd": float(round(self._sanitize_float(macd.iloc[-1]), 2)),
                "volatilidade_atr": float(round(self._sanitize_float(tr.iloc[-1]), 2)),
                "tendencia_sma200": tendencia,
                
                # NOVOS CAMPOS (Garantindo que existam)
                "bb_posicao": float(round(self._sanitize_float(bb_pos.iloc[-1]) * 100, 1)),
                "momentum_5d": float(round(self._sanitize_float(momentum5.iloc[-1]), 2)),
                "vwap": float(round(self._sanitize_float(vwap_val), 2))
            }
        }

market_service = MarketDataService()
