# src/api/services/data_loader.py
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_latest_features():
    # Parâmetros
    ticker = 'PETR4.SA'
    today = datetime.now()
    # Baixa 2 anos para garantir indicadores longos (SMA200)
    start_date = (today - relativedelta(years=2)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    print(f"🔄 Baixando dados de {start_date} a {end_date}...")

    # 1. Coleta
    core = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(core.columns, pd.MultiIndex):
        core.columns = core.columns.droplevel(1)
    core = core.dropna()

    if core.empty:
        raise Exception("Erro ao baixar dados do Yahoo Finance")

    macro = pd.DataFrame(index=core.index)
    
    # Download de dados Macroeconômicos
    macro['USDBRL'] = yf.download('BRL=X', start=start_date, end=end_date, progress=False)['Close']
    macro['Brent'] = yf.download('BZ=F', start=start_date, end=end_date, progress=False)['Close']
    macro['Ibovespa'] = yf.download('^BVSP', start=start_date, end=end_date, progress=False)['Close']

    # SELIC
    try:
        def fmt_data(d): return datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y')
        url_selic = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={fmt_data(start_date)}&dataFinal={fmt_data(end_date)}'
        resp = requests.get(url_selic, timeout=3)
        if resp.ok:
            selic_data = pd.DataFrame(resp.json())
            selic_data['data'] = pd.to_datetime(selic_data['data'], format='%d/%m/%Y').dt.tz_localize(None)
            selic_data.set_index('data', inplace=True)
            selic_data['valor'] = pd.to_numeric(selic_data['valor'])
            macro['Selic'] = selic_data['valor'].reindex(macro.index).ffill()
        else:
            raise Exception("API BCB offline")
    except Exception as e:
        print(f"⚠️ Aviso Selic: {e}")
        macro['Selic'] = 13.25

    # Fills e Lags (Correção do warning)
    macro = macro.ffill()
    macro['Ibov_Return'] = macro['Ibovespa'].pct_change()
    macro['Brent_Return'] = macro['Brent'].pct_change()
    macro['USD_Return'] = macro['USDBRL'].pct_change()

    macro_lagged = macro.copy()
    for col in ['USDBRL', 'Brent', 'Ibovespa', 'Selic', 'Ibov_Return', 'Brent_Return', 'USD_Return']:
        macro_lagged[f'{col}_t-1'] = macro_lagged[col].shift(1)
    
    macro_lagged = macro_lagged.drop(columns=['USDBRL', 'Brent', 'Ibovespa', 'Selic', 'Ibov_Return', 'Brent_Return', 'USD_Return'])

    # 2. Indicadores Técnicos
    df_calc = pd.DataFrame(index=core.index)
    
    df_calc['return_1'] = core['Close'].pct_change()
    df_calc['return_5'] = core['Close'].pct_change(periods=5)
    df_calc['return_20'] = core['Close'].pct_change(periods=20)
    
    # Adicionando colunas que seu modelo pode precisar implicitamente para cálculo
    df_calc['SMA_20'] = core['Close'].rolling(window=20).mean()
    df_calc['SMA_200'] = core['Close'].rolling(window=200).mean()
    
    df_calc['Dist_SMA200'] = (core['Close'] / core['Close'].rolling(200).mean()) - 1
    df_calc['Momentum_5'] = core['Close'] - core['Close'].shift(5)
    df_calc['Momentum_10'] = core['Close'] - core['Close'].shift(10)
    df_calc['Momentum_20'] = core['Close'] - core['Close'].shift(20)

    # RSI
    delta = core['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=21).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=21).mean()
    rs = gain / loss
    df_calc['RSI_21'] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = core['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = core['Close'].ewm(span=26, adjust=False).mean()
    df_calc['MACD'] = ema_12 - ema_26
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, adjust=False).mean()

    # Volatilidade
    df_calc['ATR_14'] = (core['High'] - core['Low']).rolling(14).mean()
    df_calc['BB_Middle'] = core['Close'].rolling(window=20).mean()
    df_calc['BB_Std'] = core['Close'].rolling(window=20).std()
    df_calc['BB_Upper'] = df_calc['BB_Middle'] + (df_calc['BB_Std'] * 2)
    df_calc['BB_Lower'] = df_calc['BB_Middle'] - (df_calc['BB_Std'] * 2)
    df_calc['BB_Width'] = (df_calc['BB_Upper'] - df_calc['BB_Lower']) / df_calc['BB_Middle']
    df_calc['BB_Position'] = (core['Close'] - df_calc['BB_Lower']) / (df_calc['BB_Upper'] - df_calc['BB_Lower'])
    df_calc['STD_20'] = df_calc['BB_Std']
    
    df_calc['Parkinson_Vol'] = np.sqrt(1/(4*np.log(2)) * (np.log(core['High']/core['Low'])**2))
    df_calc['Range_High_Low'] = (core['High'] - core['Low']) / core['Close']

    # Volume
    df_calc['OBV'] = (np.sign(core['Close'].diff()) * core['Volume']).fillna(0).cumsum()
    df_calc['Volume_Ratio'] = core['Volume'] / core['Volume'].rolling(20).mean()
    df_calc['VWAP'] = (core['Volume'] * (core['High'] + core['Low'] + core['Close']) / 3).cumsum() / core['Volume'].cumsum()

    # Temporal
    dow = core.index.dayofweek
    month = core.index.month
    df_calc['DoW_sin'] = np.sin(2 * np.pi * dow / 5)
    df_calc['DoW_cos'] = np.cos(2 * np.pi * dow / 5)
    df_calc['Month_sin'] = np.sin(2 * np.pi * month / 12)
    df_calc['Month_cos'] = np.cos(2 * np.pi * month / 12)

    df_final = pd.concat([core, macro_lagged, df_calc], axis=1)
    df_final = df_final.dropna()

    # --- Prepara dados para exibição (Display) ---
    last_row = df_final.iloc[-1]
    
    # TRATAMENTO ESPECIAL DA SELIC (Diária -> Anual)
    selic_diaria = float(macro['Selic'].iloc[-1])
    # Fórmula: ((1 + taxa_diaria/100) ^ 252 dias úteis) - 1
    selic_anualizada = ((1 + selic_diaria/100) ** 252 - 1) * 100
    
    display_data = {
        "preco_atual": float(last_row['Close']),
        "data_referencia": df_final.index[-1].strftime('%Y-%m-%d'),
        "macro": {
            "dolar": float(macro['USDBRL'].iloc[-1]),
            "brent": float(macro['Brent'].iloc[-1]),
            # Passamos a Selic calculada para anual
            "selic": round(selic_anualizada, 2), 
            "ibovespa": float(macro['Ibovespa'].iloc[-1])
        },
        "tecnicos": {
            "rsi": float(last_row['RSI_21']),
            "macd": float(last_row['MACD']),
            "volatilidade_atr": float(last_row['ATR_14']),
            "tendencia_sma200": "Alta 🟢" if last_row['Close'] > last_row['Close']/(1+last_row['Dist_SMA200']) else "Baixa 🔴"
        }
    }

    return df_final, display_data
