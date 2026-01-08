import pandas as pd
import numpy as np
import yfinance as yf
import requests
import warnings

# Suprime warnings do pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

class FeaturePipeline:
    def __init__(self):
        self.TARGET_COLUMNS = [
            'USDBRL_t-1', 'Brent_t-1', 'Ibovespa_t-1', 'Selic_t-1', 
            'Ibov_Return_t-1', 'Brent_Return_t-1', 'USD_Return_t-1', 
            'return_1', 'return_5', 'return_20', 
            'Dist_SMA200', 
            'Momentum_5', 'Momentum_10', 'Momentum_20', 
            'RSI_21', 
            'MACD', 'MACD_Signal', 
            'ATR_14', 
            'BB_Middle', 'BB_Std', 'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_Position', 
            'STD_20', 'Parkinson_Vol', 'Range_High_Low',
            'OBV', 'Volume_Ratio', 'VWAP', 
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
        
        # Tenta baixar. Se falhar (lock), tenta de novo sem thread
        try:
            df_all = yf.download(tickers, period="2y", progress=False, threads=False)
        except Exception as e:
            print(f"⚠️ Erro no yfinance: {e}. Retornando dados zerados de emergência.")
            # Retorna estrutura vazia mas válida para não crashar a API
            return self._create_empty_fallback()

        # Verifica se baixou algo útil
        if df_all.empty or 'Close' not in df_all.columns:
             print("⚠️ Dados vazios do Yahoo Finance.")
             return self._create_empty_fallback()

        # Tratamento MultiIndex
        if isinstance(df_all.columns, pd.MultiIndex):
            try:
                # Usa ffill() ANTES de separar para propagar dados
                df_all = df_all.ffill()
                closes = df_all.xs('Close', axis=1, level=0)
                highs = df_all.xs('High', axis=1, level=0)
                lows = df_all.xs('Low', axis=1, level=0)
                vols = df_all.xs('Volume', axis=1, level=0)
            except:
                return self._create_empty_fallback()
        else:
            closes = df_all
        
        # Garante que temos PETR4
        if 'PETR4.SA' not in closes.columns:
             return self._create_empty_fallback()

        df = pd.DataFrame(index=closes.index)
        
        # Atalhos com ffill garantido
        p_close = closes['PETR4.SA'].ffill()
        p_high = highs['PETR4.SA'].ffill()
        p_low = lows['PETR4.SA'].ffill()
        p_vol = vols['PETR4.SA'].ffill()

        # Se depois do ffill ainda tiver NaN (começo da série), preenche com 0
        p_close = p_close.fillna(0)
        
        # --- ENGENHARIA ---
        # Usa fill_method=None para evitar warnings em versões novas do Pandas
        
        # Macro
        df['USDBRL_t-1'] = closes['BRL=X'].shift(1)
        df['Brent_t-1'] = closes['BZ=F'].shift(1)
        df['Ibovespa_t-1'] = closes['^BVSP'].shift(1)
        df['Selic_t-1'] = self._get_selic()
        
        df['Ibov_Return_t-1'] = closes['^BVSP'].pct_change(fill_method=None).shift(1)
        df['Brent_Return_t-1'] = closes['BZ=F'].pct_change(fill_method=None).shift(1)
        df['USD_Return_t-1'] = closes['BRL=X'].pct_change(fill_method=None).shift(1)

        # Returns
        df['return_1'] = p_close.pct_change(fill_method=None)
        df['return_5'] = p_close.pct_change(5, fill_method=None)
        df['return_20'] = p_close.pct_change(20, fill_method=None)

        # Momentum
        sma200 = p_close.rolling(200).mean()
        # Evita divisão por zero
        df['Dist_SMA200'] = (p_close / sma200.replace(0, np.nan)) - 1
        
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
        
        df['Range_High_Low'] = (p_high - p_low) / p_close.replace(0, np.nan)

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
        final_df = df[self.TARGET_COLUMNS].copy()
        
        # Preenchimento Final Agressivo (Remove qualquer NaN restante)
        final_df = final_df.ffill().fillna(0)
        
        # Se tiver menos de 50 linhas, preenche com zeros no começo
        if len(final_df) < 50:
            missing = 50 - len(final_df)
            zeros = pd.DataFrame(0, index=range(missing), columns=final_df.columns)
            final_df = pd.concat([zeros, final_df])
            p_close = pd.concat([pd.Series([0]*missing), p_close])

        return final_df.iloc[-50:], p_close.iloc[-50:]

    def _create_empty_fallback(self):
        """Cria dados fake zerados para API não morrer se download falhar"""
        print("⚠️ Usando dados de fallback zerados.")
        # Cria 50 linhas de zeros
        df = pd.DataFrame(0.0, index=range(50), columns=self.TARGET_COLUMNS)
        p_close = pd.Series([30.0] * 50) # Preço dummy de 30 reais
        return df, p_close

pipeline = FeaturePipeline()
