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
        # Secretsに登録したAPP_PASSWORDと比較
        if st.session_state["password_input"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # セキュリティのため入力値を消去
        else:
            st.session_state["password_correct"] = False

    # すでに認証済みの場合はTrueを返す
    if st.session_state.get("password_correct", False):
        return True

    # ログイン画面を表示
    st.title("🔒 認証が必要です")
    st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password_input")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 パスワードが違います")
    
    return False

# 💡 パスワードが通るまで、ここから下のコードは一切実行されません
if not check_password():
    st.stop()

# ---------------------------------------------------------
# 認証成功後にのみ実行される設定
# ---------------------------------------------------------
api_key = st.secrets["GEMINI_API_KEY"]
# ---------------------------------------------------------

# --- これ以降にfetch_all_data()やメインのUIコードを続けてください ---

CATEGORIES = ["食費", "外食", "日用品", "交通費", "電気", "ガス", "水道", "インターネット", "スマホ", "家賃", "衣服", "美容", "医療費", "交際費", "趣味", "教育費", "車関連", "税金", "その他"]

st.set_page_config(page_title="Finance OS", page_icon="✨", layout="centered")

# --- データの読み込み関数（これがないとエラーになります） ---
def fetch_all_data():
    asset_df = dm.load_data(dm.ASSET_FILE, pd.DataFrame([{"項目": "現金", "金額": 0}]))
    budget_df = dm.load_data(dm.BUDGET_FILE, pd.DataFrame([{"月予算": 100000}]))
    df_all = dm.load_kakeibo()
    return asset_df, budget_df, df_all

# CSS スタイル設定
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    div[data-testid="stMetric"] { background: #f8f9fa; border-radius: 16px; padding: 15px 20px !important; }
    .stButton>button[kind="primary"] { width: 100%; border-radius: 12px; height: 3.5em; background-color: #0071e3; color: white; border: none; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# データの取得を実行
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

# ここに当初の希望だった「内訳表示」を安全な形で追加しています
c1, c2, c3 = st.columns(3)
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
# --- AI家計診断セクション ---
st.subheader("🤖 AI家計診断")
if st.button("AIにアドバイスをもらう", type="secondary"):
    with st.spinner("AIが家計を分析中..."):
        try:
            # 支出のサマリーを作成
            if not this_month_df.empty:
                cat_summary = this_month_df.groupby('category')['price'].sum().to_dict()
            else:
                cat_summary = "今月の支出データなし"
                
            # AIからアドバイスを取得
            advice = ai.get_ai_advice(api_key, total_assets, this_month_spent, monthly_budget, cat_summary)
            
            # アドバイスをオシャレな枠で表示
            st.info(advice)
            st.caption("※Geminiによる自動生成アドバイスです")
        except Exception as e:
            st.error(f"診断に失敗しました: {e}")
st.markdown("---")

# --- 2. 分析セクション（円グラフなど） ---
if not this_month_df.empty:
    st.subheader("🥧 カテゴリ別の支出分析")
    col_chart, col_list = st.columns([1.2, 1])
    with col_chart:
        donut = alt.Chart(this_month_df).mark_arc(innerRadius=60, cornerRadius=8).encode(
            theta=alt.Theta("price:Q"),
            color=alt.Color("category:N", scale=alt.Scale(scheme='tableau20'), legend=None),
            tooltip=['category', 'price']
        ).properties(height=300)
        st.altair_chart(donut, use_container_width=True)
    with col_list:
        cat_summary = this_month_df.groupby('category')['price'].sum().sort_values(ascending=False).reset_index()
        cat_summary['金額'] = cat_summary['price'].map(lambda x: f"¥{x:,}")
        st.dataframe(cat_summary[['category', '金額']], hide_index=True, use_container_width=True)
else:
    st.info("今月の記録はまだありません。")

# --- 3. 入力セクション（AIスキャン・手入力） ---
st.subheader("➕ 支出を追加する")
entry_tab1, entry_tab2 = st.tabs(["📸 AIスキャン", "✍️ 手入力"])

with entry_tab1:
    uploaded_file = st.file_uploader("レシートをアップロード", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        if st.button("AI分析を実行", type="primary"):
            with st.spinner("Analyzing..."):
                try:
                    data = ai.analyze_receipt(api_key, uploaded_file.getvalue(), CATEGORIES)
                    # 1. 家計簿履歴に保存
                    dm.save_csv(pd.DataFrame([data]), dm.KAKEIBO_FILE, mode='a', header=not os.path.exists(dm.KAKEIBO_FILE))
                    
                    # 2. 【追加】現金を金額分だけ減らす
                    dm.update_asset("現金", -int(data["price"])) 
                    
                    st.toast("記録完了＆現金を更新しました", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"エラー: {e}")

with entry_tab2:
    with st.form("manual_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        m_date = c1.date_input("日付")
        m_price = c2.number_input("金額", min_value=0)
        m_cat = st.selectbox("カテゴリー", CATEGORIES)
        m_store = st.text_input("支払先")
        if st.form_submit_button("記録する"):
            # 1. データを準備して保存
            data = {"date": m_date.strftime("%Y/%m/%d"), "store": m_store if m_store else "手入力", "item": "手入力", "price": m_price, "category": m_cat}
            dm.save_csv(pd.DataFrame([data]), dm.KAKEIBO_FILE, mode='a', header=not os.path.exists(dm.KAKEIBO_FILE))
            
            # 2. 【追加】現金を金額分だけ減らす
            dm.update_asset("現金", -int(m_price))
            
            st.toast("記録しました", icon="✅")
            st.cache_data.clear()
            st.rerun()

# --- 4. 管理セクション（履歴編集） ---
with st.expander("⚙️ 履歴の編集・資産予算設定"):
    st.markdown("#### 📋 履歴の編集")
    if not df_all.empty:
        edited_kakeibo = st.data_editor(df_all.sort_values("date", ascending=False), num_rows="dynamic", use_container_width=True, key="editor_history")
        if st.button("履歴を保存"):
            dm.save_csv(edited_kakeibo, dm.KAKEIBO_FILE)
            st.cache_data.clear()
            st.success("保存しました")

            st.rerun()
