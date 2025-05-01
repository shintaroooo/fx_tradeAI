import pandas as pd

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 日本語列名の補正（必要な場合）
    rename_map = {
        '日付': 'Date',
        '日付け': 'Date',
        '終値': 'Close',
        '始値': 'Open',
        '高値': 'High',
        '安値': 'Low',
        '出来高': 'Volume',
        '変化率 %': 'Change %'
    }
    df.rename(columns={col: rename_map.get(col, col) for col in df.columns}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    for col in ['Close', 'Open', 'High', 'Low']:
        df[col] = df[col].astype(str).str.replace(',', '').astype(float)

    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    mid = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_Middle'] = mid
    df['BB_Upper'] = mid + 2 * std
    df['BB_Lower'] = mid - 2 * std

    low14 = df['Low'].rolling(window=14).min()
    high14 = df['High'].rolling(window=14).max()
    df['Stoch_K_14_3'] = 100 * (df['Close'] - low14) / (high14 - low14)
    df['Stoch_D_14_3'] = df['Stoch_K_14_3'].rolling(window=3).mean()

    return df
