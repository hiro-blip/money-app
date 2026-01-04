import streamlit as st
import pandas as pd
import datetime
import altair as alt
import os

# 自作モジュールの読み込み
import data_manager as dm
import ai_analyzer as ai

# --- パスワード認証機能 ---
def check_password():
    """パスワードが正しいかチェックし、結果をTrue/Falseで返す"""
    def password_entered():
        if st.session_state["password_input"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 認証が必要です")
    st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password_input")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 パスワードが違います")
    
    return False

if not check_password():
    st.stop()

# --- 初期設定 ---
api_key = st.secrets["GEMINI_API_KEY"]
CATEGORIES = ["食費", "外食", "日用品", "交通費", "電気", "ガス", "水道", "インターネット", "スマホ", "家賃", "衣服", "美容", "医療費", "交際費", "趣味", "教育費", "車関連", "税金", "その他"]

st.set_page_config(page_title="Finance OS", page_icon="✨", layout="centered")

def fetch_all_data():
    asset_df = dm.load_data(dm.ASSET_FILE, pd.DataFrame([{"項目": "現金", "金額": 0}]))
    budget_df = dm.load_data(dm.BUDGET_FILE, pd.DataFrame([{"月予算": 100000}]))
    df_all = dm.load_kakeibo()
    # 金額カラムを確実に数値型にする
    asset_df["金額"] = pd.to_numeric(asset_df["金額"], errors='coerce').fillna(0).astype(int)
    return asset_df, budget_df, df_all

# CSS スタイル
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    div[data-testid="stMetric"] { background: #f8f9fa; border-radius: 16px; padding: 15px 20px !important; }
    .stButton>button[kind="primary"] { width: 100%; border-radius: 12px; height: 3.5em; background-color: #0071e3; color: white; border: none; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# データの取得
asset_df, budget_df, df_all = fetch_all_data()
monthly_budget = int(budget_df.iloc[0]["月予算"])

# --- 1. サマリーセクション ---
st.title("✨ Finance Overview")
total_assets = int(asset_df['金額'].sum())
this_month_df = dm.get_this_month_data(df_all)
this_month_spent = int(this_month_df['price'].sum()) if not this_month_df.empty else 0

m1, m2, m3 = st.columns(3)
m1.metric("総資産額", f"¥{total_assets:,}")
m2.metric("今月の支出", f"¥{this_month_spent:,}", delta=f"予算差: ¥{monthly_budget - this_month_spent:,}")
m3.metric("自由に使えるお金", f"¥{total_assets - this_month_spent:,}")

c1, c2 = st.columns(2)
with c1:
    with st.expander("🏦 資産の内訳"):
        for _, row in asset_df.iterrows():
            st.write(f"{row['項目']}: **¥{int(row['金額']):,}**")
with c2:
    with st.expander("💸 支出の内訳"):
        if not this_month_df.empty:
            cat_sum = this_month_df.groupby('category')['price'].sum().sort_values(ascending=False).reset_index()
            for _, row in cat_sum.iterrows():
                st.write(f"{row['category']}: **¥{int(row['price']):,}**")

# --- AI家計診断 ---
st.subheader("🤖 AI家計診断")
if st.button("AIにアドバイスをもらう"):
    with st.spinner("AIが分析中..."):
        try:
            cat_summary = this_month_df.groupby('category')['price'].sum().to_dict() if not this_month_df.empty else "データなし"
            advice = ai.get_ai_advice(api_key, total_assets, this_month_spent, monthly_budget, cat_summary)
            st.info(advice)
        except Exception as e:
            st.error(f"診断エラー: {e}")

st.markdown("---")

# --- 2. 分析セクション ---
if not this_month_df.empty:
    st.subheader("🥧 カテゴリ別の支出分析")
    donut = alt.Chart(this_month_df).mark_arc(innerRadius=60, cornerRadius=8).encode(
        theta=alt.Theta("price:Q"),
        color=alt.Color("category:N", scale=alt.Scale(scheme='tableau20'), legend=None),
        tooltip=['category', 'price']
    ).properties(height=300)
    st.altair_chart(donut, use_container_width=True)

# --- 3. 入力セクション ---
st.subheader("➕ 支出を追加する")
entry_tab1, entry_tab2 = st.tabs(["📸 AIスキャン", "✍️ 手入力"])

with entry_tab1:
    uploaded_file = st.file_uploader("レシートをアップロード", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        if st.button("AI分析を実行", type="primary"):
            with st.spinner("Analyzing..."):
                try:
                    st.session_state["ai_result"] = ai.analyze_receipt(api_key, uploaded_file.getvalue(), CATEGORIES)
                except Exception as e:
                    st.error(f"分析エラー: {e}")

        if "ai_result" in st.session_state:
            st.markdown("##### 📝 解析結果の確認・修正")
            with st.form("ai_fix_form"):
                f_date = st.text_input("日付", st.session_state["ai_result"]["date"])
                f_store = st.text_input("店名", st.session_state["ai_result"]["store"])
                f_price = st.number_input("金額", value=int(st.session_state["ai_result"]["price"]))
                f_cat = st.selectbox("カテゴリー", CATEGORIES, index=CATEGORIES.index(st.session_state["ai_result"]["category"]) if st.session_state["ai_result"]["category"] in CATEGORIES else 0)
                asset_names = asset_df["項目"].unique().tolist()
                f_payment = st.selectbox("支払い元", asset_names)
                
                if st.form_submit_button("この内容で確定保存"):
                    final_data = {"date": f_date, "store": f_store, "item": "AIスキャン", "price": int(f_price), "category": f_cat}
                    dm.save_csv(pd.DataFrame([final_data]), dm.KAKEIBO_FILE, mode='a', header=not os.path.exists(dm.KAKEIBO_FILE))
                    dm.update_asset(f_payment, -int(f_price)) 
                    del st.session_state["ai_result"]
                    st.cache_data.clear()
                    st.success(f"保存完了！")
                    st.rerun()

with entry_tab2:
    with st.form("manual_entry", clear_on_submit=True):
        m_date = st.date_input("日付")
        m_price = st.number_input("金額", min_value=0)
        m_cat = st.selectbox("カテゴリー", CATEGORIES)
        m_store = st.text_input("支払先")
        asset_names = asset_df["項目"].unique().tolist()
        m_payment = st.selectbox("支払い元", asset_names)
        
        if st.form_submit_button("記録する"):
            data = {"date": m_date.strftime("%Y/%m/%d"), "store": m_store if m_store else "手入力", "item": "手入力", "price": int(m_price), "category": m_cat}
            dm.save_csv(pd.DataFrame([data]), dm.KAKEIBO_FILE, mode='a', header=not os.path.exists(dm.KAKEIBO_FILE))
            dm.update_asset(m_payment, -int(m_price))
            st.cache_data.clear()
            st.success("保存完了！")
            st.rerun()

# --- 4. 管理セクション ---
with st.expander("⚙️ 履歴の編集・資産予算設定"):
    st.markdown("#### 🏦 資産の編集")
    # 数値をきれいに整えて表示
    display_asset_df = asset_df.copy()
    display_asset_df["金額"] = pd.to_numeric(display_asset_df["金額"], errors='coerce').fillna(0).astype(int)
    
    edited_assets = st.data_editor(display_asset_df, num_rows="dynamic", use_container_width=True, key="editor_assets_final")
    if st.button("資産状況を保存"):
        dm.save_csv(edited_assets, dm.ASSET_FILE)
        st.cache_data.clear()
        st.success("更新しました")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 履歴の編集")
    if not df_all.empty:
        edited_kakeibo = st.data_editor(df_all.sort_values("date", ascending=False), num_rows="dynamic", use_container_width=True, key="editor_history_final")
        if st.button("履歴を保存"):
            dm.save_csv(edited_kakeibo, dm.KAKEIBO_FILE)
            st.cache_data.clear()
            st.success("保存しました")
            st.rerun()
