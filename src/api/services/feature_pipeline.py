import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import requests

class FeaturePipeline:
    def __init__(self):
        # LISTA EXATA DE 34 COLUNAS (Matemática corrigida para o Modelo)
        # Removemos: Close, High, Low, Open, Volume, SMA_20, SMA_200
        self.TARGET_COLUMNS = [
            # 1. Macro Lagged
            'USDBRL_t-1', 'Brent_t-1', 'Ibovespa_t-1', 'Selic_t-1', 
            'Ibov_Return_t-1', 'Brent_Return_t-1', 'USD_Return_t-1', 
            
            # 2. Returns
            'return_1', 'return_5', 'return_20', 
            
            # 3. Momentum
            'Dist_SMA200', # Apenas a distância relativa
            'Momentum_5', 'Momentum_10', 'Momentum_20', 
            'RSI_21', 
            'MACD', 'MACD_Signal', 
            
            # 4. Volatilidade
            'ATR_14', 
            'BB_Middle', 'BB_Std', 'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_Position', 
            'STD_20', 'Parkinson_Vol', 'Range_High_Low',
            
            # 5. Volume
            'OBV', 'Volume_Ratio', 'VWAP', 
            
            # 6. Temporal
            'DoW_sin', 'DoW_cos', 'Month_sin', 'Month_cos'
        ]

    def _get_selic(self):
        try:
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=2)
            if r.status_code == 200:
                return float(r.json()[-1]['valor'])
        except:
            pass
        return 11.25

    def _calculate_rsi(self, series, period=21):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def prepare_input_data(self):
        tickers = ["PETR4.SA", "BRL=X", "BZ=F", "^BVSP"]
        print("📥 Pipeline: Baixando dados brutos (2y)...")
        df_all = yf.download(tickers, period="2y", progress=False)
        
        if isinstance(df_all.columns, pd.MultiIndex):
            try:
                closes = df_all['Close'].ffill()
                highs = df_all['High'].ffill()
                lows = df_all['Low'].ffill()
                opens = df_all['Open'].ffill()
                vols = df_all['Volume'].ffill()
            except:
                closes = df_all.xs('Close', axis=1, level=0).ffill()
                highs = df_all.xs('High', axis=1, level=0).ffill()
                lows = df_all.xs('Low', axis=1, level=0).ffill()
                opens = df_all.xs('Open', axis=1, level=0).ffill()
                vols = df_all.xs('Volume', axis=1, level=0).ffill()
        else:
            closes = df_all
        
        df = pd.DataFrame(index=closes.index)
        
        # Atalhos
        p_close = closes['PETR4.SA']
        p_high = highs['PETR4.SA']
        p_low = lows['PETR4.SA']
        p_vol = vols['PETR4.SA']

        # --- ENGENHARIA DE FEATURES ---
        
        # Macro
        df['USDBRL_t-1'] = closes['BRL=X'].shift(1)
        df['Brent_t-1'] = closes['BZ=F'].shift(1)
        df['Ibovespa_t-1'] = closes['^BVSP'].shift(1)
        df['Selic_t-1'] = self._get_selic()
        
        df['Ibov_Return_t-1'] = closes['^BVSP'].pct_change().shift(1)
        df['Brent_Return_t-1'] = closes['BZ=F'].pct_change().shift(1)
        df['USD_Return_t-1'] = closes['BRL=X'].pct_change().shift(1)

        # Returns
        df['return_1'] = p_close.pct_change()
        df['return_5'] = p_close.pct_change(5)
        df['return_20'] = p_close.pct_change(20)

        # Momentum
        # Calculamos SMA mas não exportamos
        sma200 = p_close.rolling(200).mean()
        df['Dist_SMA200'] = (p_close / sma200) - 1
        
        df['Momentum_5'] = p_close - p_close.shift(5)
        df['Momentum_10'] = p_close - p_close.shift(10)
        df['Momentum_20'] = p_close - p_close.shift(20)
        
        df['RSI_21'] = self._calculate_rsi(p_close, 21)

        ema12 = p_close.ewm(span=12, adjust=False).mean()
        ema26 = p_close.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Volatilidade
        tr1 = p_high - p_low
        tr2 = (p_high - p_close.shift()).abs()
        tr3 = (p_low - p_close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR_14'] = tr.rolling(14).mean()

        df['BB_Middle'] = p_close.rolling(20).mean()
        df['BB_Std'] = p_close.rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        
        bb_width_denom = df['BB_Middle'].replace(0, np.nan)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / bb_width_denom
        
        bb_pos_denom = (df['BB_Upper'] - df['BB_Lower']).replace(0, np.nan)
        df['BB_Position'] = (p_close - df['BB_Lower']) / bb_pos_denom
        
        df['STD_20'] = df['BB_Std']
        
        high_low_ratio = (p_high / p_low.replace(0, np.nan))
        df['Parkinson_Vol'] = np.sqrt(1/(4*np.log(2)) * (np.log(high_low_ratio)**2))
        
        df['Range_High_Low'] = (p_high - p_low) / p_close

        # Volume
        df['OBV'] = (np.sign(p_close.diff()) * p_vol).fillna(0).cumsum()
        vol_sma20 = p_vol.rolling(20).mean()
        df['Volume_Ratio'] = p_vol / vol_sma20.replace(0, np.nan)
        
        cum_vol = p_vol.cumsum()
        cum_vol_price = (p_vol * (p_high + p_low + p_close) / 3).cumsum()
        df['VWAP'] = cum_vol_price / cum_vol.replace(0, np.nan)

        # Temporal
        dow = df.index.dayofweek
        month = df.index.month
        df['DoW_sin'] = np.sin(2 * np.pi * dow / 5)
        df['DoW_cos'] = np.cos(2 * np.pi * dow / 5)
        df['Month_sin'] = np.sin(2 * np.pi * month / 12)
        df['Month_cos'] = np.cos(2 * np.pi * month / 12)

        # FINALIZAÇÃO
        # Seleciona exatamente as 34 colunas na ordem correta
        final_df = df[self.TARGET_COLUMNS].copy()
        
        final_df = final_df.ffill().fillna(0)
        
        return final_df.iloc[-20:], p_close.iloc[-1]

pipeline = FeaturePipeline()
