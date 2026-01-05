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
        Calcula indicadores técnicos com tratamento anti-erro (NaN).
        """
        # 1. Download de 1 ANO
        tickers = ["PETR4.SA", "BRL=X", "BZ=F", "^BVSP"]
        df_all = yf.download(tickers, period="1y", progress=False)
        closes = df_all['Close']

        # Função auxiliar para pegar último valor válido
        def get_last(symbol):
            try:
                # ffill preenche buracos com o valor anterior
                series = closes[symbol].ffill() 
                val = series.iloc[-1]
                return self._sanitize_float(val)
            except:
                return 0.0

        # --- CÁLCULOS TÉCNICOS (PETR4) ---
        petr_close = closes['PETR4.SA'].ffill().dropna()
        
        # A. RSI
        delta = petr_close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_real = rsi_series.iloc[-1] if not rsi_series.empty else 50.0

        # B. MACD
        ema12 = petr_close.ewm(span=12, adjust=False).mean()
        ema26 = petr_close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_real = macd_line.iloc[-1] if not macd_line.empty else 0.0

        # C. Tendência SMA 200
        window = 200 if len(petr_close) >= 200 else len(petr_close)
        if window > 0:
            sma200 = petr_close.rolling(window=window).mean().iloc[-1]
            last_price = petr_close.iloc[-1]
            # Proteção contra NaN na comparação
            if self._sanitize_float(last_price) > self._sanitize_float(sma200):
                tendencia_str = "Alta 🟢"
            else:
                tendencia_str = "Baixa 🔴"
        else:
            tendencia_str = "Indefinida ⚪"

        # D. ATR
        try:
            # Acessando dados corrigidos (ffill)
            high = df_all['High']['PETR4.SA'].ffill()
            low = df_all['Low']['PETR4.SA'].ffill()
            close = df_all['Close']['PETR4.SA'].ffill()
            
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_real = tr.rolling(14).mean().iloc[-1]
        except:
            atr_real = 0.0

        # --- RETORNO COM SANITIZAÇÃO ---
        # Passamos todos os números pelo _sanitize_float antes de devolver
        
        return {
            "preco_atual": round(self._sanitize_float(get_last('PETR4.SA')), 2),
            "data_referencia": datetime.now().strftime('%Y-%m-%d'),
            "macro": {
                "dolar": round(self._sanitize_float(get_last('BRL=X')), 2),
                "brent": round(self._sanitize_float(get_last('BZ=F')), 2),
                "selic": self._sanitize_float(self._get_selic_real()),
                "ibovespa": round(self._sanitize_float(get_last('^BVSP')), 2)
            },
            "tecnicos": {
                "rsi": round(self._sanitize_float(rsi_real, 50.0), 2),
                "macd": round(self._sanitize_float(macd_real), 2),
                "volatilidade_atr": round(self._sanitize_float(atr_real), 2),
                "tendencia_sma200": tendencia_str
            }
        }

market_service = MarketDataService()
