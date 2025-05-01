import streamlit as st
import pandas as pd
import os
from indicators import calculate_indicators
from strategy_chain import load_strategy_chain, load_summary_chain

# OpenAI APIキーの取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="📈 テクニカルトレードチャットボット", layout="wide")
st.title("📊 CFDトレーダー支援AI（複数銘柄対応）")

menu = st.sidebar.radio("メニューを選択", ["戦略チャットボット", "ポジションサイズ計算"])

# ===== 戦略チャットボット =====
if menu == "戦略チャットボット":
    symbol = st.text_input("銘柄名を入力（例：S&P500、日経225など）", value="S&P500")
    uploaded_file = st.file_uploader("📄 90日以上の株価CSVファイルをアップロード", type=["csv"])
    st.markdown('CSVファイルはこちらのサイトからダウンロードできます [investing.com](https://jp.investing.com/markets/)')  

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if len(df) < 90:
            st.error("⚠️ 90日以上のデータが必要です。")
        else:
            if st.button("📊 分析する"):
                with st.spinner("AIがデータを分析中..."):
                    df = calculate_indicators(df)
                    clean_df = df.dropna(subset=[
                        "RSI_14", "MACD", "MACD_Signal",
                        "BB_Lower", "Stoch_K_14_3", "Stoch_D_14_3"
                    ])
                    if clean_df.empty:
                        st.error("⚠️ 指標計算に必要なデータが足りません。")
                    else:
                        latest = clean_df.iloc[-1]

                        # 指標を整形して渡す
                        macd_text = f"MACD: {latest['MACD']:.2f}, Signal: {latest['MACD_Signal']:.2f}"
                        rsi_text = f"RSI14は{latest['RSI_14']:.1f}"
                        sma_text = f"SMA5({latest['SMA_5']:.2f}) vs SMA20({latest['SMA_20']:.2f})"
                        bb_text = f"価格({latest['Close']:.2f})はBB範囲 {latest['BB_Lower']:.2f}〜{latest['BB_Upper']:.2f}"
                        stoch_text = f"%K: {latest['Stoch_K_14_3']:.1f}, %D: {latest['Stoch_D_14_3']:.1f}"

                        chain = load_strategy_chain(api_key=OPENAI_API_KEY)
                        strategy = chain.run({
                            "symbol": symbol,
                            "macd": macd_text,
                            "rsi": rsi_text,
                            "sma": sma_text,
                            "bb": bb_text,
                            "stoch": stoch_text
                        })

                        st.chat_message("assistant").markdown(strategy)
                        if st.button("Xで共有する"):
                            with st.spinner("要約を生成中..."):
                                summary_chain = load_summary_chain(api_key=OPENAI_API_KEY)
                                summary = summary_chain.run({"strategy": strategy})

                            hashtags = "#テクニカル分析 #CFD #LazyTech"
                            tweet_text = f"{summary}\n{hashtags}"
                            tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"

                            st.markdown(f"[🕊 Xで投稿リンクを開く]({tweet_url})", unsafe_allow_html=True)


                        # 🔽 免責事項を明記
                        disclaimer = "\n\n---\n※本戦略はAIによるテクニカル分析結果に基づいて生成されたものであり、投資判断の最終決定はご自身の責任で行ってください。本サービスは投資助言ではありません。"
                        st.markdown(disclaimer)

                        # X共有ボタン
                        st.button("Xで共有する")
                        

# ===== ポジションサイズ計算 =====
elif menu == "ポジションサイズ計算":
    st.subheader("💰 ポジションサイズ自動計算")

    symbol = st.text_input("通貨ペア / 銘柄名（任意）", value="S&P500")
    equity = st.number_input("証拠金残高（円）", min_value=10000, step=1000, value=100000)
    risk_pct = st.slider("リスク許容率（％）", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
    stop_loss_pips = st.number_input("損切り幅（pips）", min_value=1.0, value=50.0)
    leverage = st.number_input("レバレッジ倍率", min_value=1.0, value=10.0)
    contract_size = st.number_input("取引単位（通貨数）", min_value=100.0, value=10000.0)
    pip_value = st.number_input("1pipsあたりの円換算額（手動入力）", min_value=0.01, value=1.0)

    if st.button("📊 ポジションサイズを計算"):
        risk_amount = equity * (risk_pct / 100)
        position_size = risk_amount / (stop_loss_pips * pip_value)
        notional_value = position_size * contract_size
        required_margin = notional_value / leverage

        st.success(f"✅ 推奨ロット数（{int(contract_size)}通貨単位）: **{round(position_size, 2)}ロット**")
        st.info(f"必要証拠金の目安: 約 **¥{round(required_margin):,}**")
