import pandas as pd

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 列名の前後スペースを除去（念のため）
    df.columns = df.columns.str.strip()

    # 日付をdatetime型に変換してソート
    df['日付'] = pd.to_datetime(df['日付'])
    df = df.sort_values('日付')

    # 数値列を安全にfloat型へ変換（エラーはNaN）
    for col in ['終値', '始値', '高値', '安値']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            raise KeyError(f"列 '{col}' がDataFrameに存在しません。")

    # 単純移動平均
    df['SMA_5'] = df['終値'].rolling(window=5).mean()
    df['SMA_20'] = df['終値'].rolling(window=20).mean()

    # RSI（14期間）
    delta = df['終値'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['終値'].ewm(span=12, adjust=False).mean()
    ema26 = df['終値'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # ボリンジャーバンド
    mid = df['終値'].rolling(window=20).mean()
    std = df['終値'].rolling(window=20).std()
    df['BB_Middle'] = mid
    df['BB_Upper'] = mid + 2 * std
    df['BB_Lower'] = mid - 2 * std

    # ストキャスティクス（%K と %D）
    low14 = df['安値'].rolling(window=14).min()
    high14 = df['高値'].rolling(window=14).max()
    df['Stoch_K_14_3'] = 100 * (df['終値'] - low14) / (high14 - low14)
    df['Stoch_D_14_3'] = df['Stoch_K_14_3'].rolling(window=3).mean()

    return df
