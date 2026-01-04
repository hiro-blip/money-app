import pandas as pd
import os
import datetime

KAKEIBO_FILE = "kakeibo.csv"
ASSET_FILE = "assets.csv"
BUDGET_FILE = "budget.csv"

def load_data(file, default_df):
    if os.path.exists(file):
        return pd.read_csv(file)
    return default_df

def save_csv(df, file, mode='w', header=True):
    df.to_csv(file, mode=mode, header=header, index=False, encoding='utf-8-sig')

def get_this_month_data(df):
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    now = datetime.datetime.now()
    return df[(df['date'].dt.year == now.year) & (df['date'].dt.month == now.month)]

# data_manager.py に以下を追加・修正してください

def load_kakeibo():
    if os.path.exists(KAKEIBO_FILE):
        # 毎回最新のファイルを読み込む
        return pd.read_csv(KAKEIBO_FILE, encoding='utf-8-sig')
    return pd.DataFrame(columns=["date", "store", "item", "price", "category"])