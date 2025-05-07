import streamlit as st
import pandas as pd
import os
import urllib.parse
import yfinance as yf
import datetime
import plotly.graph_objects as go
from indicators import calculate_indicators
from strategy_chain import load_strategy_chain
from summary_chain import load_summary_chain

# APIキー取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="📈 AIテクニカルトレードボット", layout="wide")
st.title("📈AIテクニカルトレードボット")

# Google Analyticsの埋め込み
st.markdown(
    """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-M0N2JB9TD2"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-M0N2JB9TD2');
    </script>
    """,
    unsafe_allow_html=True
)

# # --- 保存用ロジック ---
# if "strategy_history" not in st.session_state:
#     st.session_state.strategy_history = {}

# def save_strategy_result(name: str, strategy_text: str):
#     if name and strategy_text:
#         st.session_state.strategy_history[name] = strategy_text
#         st.success(f"✅ '{name}' として保存しました。")

# def select_saved_strategy():
#     if st.session_state.strategy_history:
#         selected_name = st.sidebar.selectbox("📂 保存済み分析結果", list(st.session_state.strategy_history.keys()))
#         if selected_name:
#             st.sidebar.markdown("⬇️ 分析結果")
#             st.sidebar.markdown(st.session_state.strategy_history[selected_name])
#     else:
#         st.sidebar.info("保存された分析結果はまだありません。")


menu = st.sidebar.radio("メニューを選択", ["戦略チャットボット"])
with st.sidebar:
    st.markdown("---")
    st.subheader("📁 過去の分析履歴")
    select_saved_strategy()

if menu == "戦略チャットボット":
    symbol_options = {
        "S&P500（米国）": "^GSPC",
        "日経平均（日本）": "^N225",
        "NASDAQ100（米国）": "^NDX",
        "USD/JPY（ドル円）": "JPY=X",
        "EUR/USD（ユーロドル）": "EURUSD=X"
    }
    symbol_label = st.selectbox("銘柄を選択（または直接入力も可能）", list(symbol_options.keys()))
    default_symbol = symbol_options[symbol_label]
    symbol = st.text_input("銘柄コード（Yahoo Finance形式）", value=default_symbol)
    use_yfinance = st.checkbox("📡 Yahoo Financeから自動取得する", value=True)

    if use_yfinance:
        start_date = st.date_input("開始日", pd.to_datetime("2023-01-01"))
        end_date = st.date_input("終了日", pd.to_datetime(datetime.date.today()))

        if st.button("📊 データ取得 & 分析する", key="analyze_yf"):
            with st.spinner("データ取得中..."):
                data = yf.download(symbol, start=start_date, end=end_date)

                if data.empty:
                    st.error("⚠️ データが取得できませんでした。銘柄コードまたは日付範囲を見直してください。")
                    st.stop()

                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                data = data.reset_index()
                data.rename(columns={
                    "Date": "日付", "Open": "始値", "High": "高値", "Low": "安値", "Close": "終値"
                }, inplace=True)

                st.success(f"✅ データ取得完了：{symbol}")
                st.dataframe(data.tail())

            with st.spinner("AIがデータを分析中..."):
                df = calculate_indicators(data)
                clean_df = df.dropna(subset=[
                    "RSI_14", "MACD", "MACD_Signal",
                    "BB_Lower", "Stoch_K_14_3", "Stoch_D_14_3"
                ])

                if clean_df.empty:
                    st.error("⚠️ 指標計算に必要なデータが不足しています。")
                else:
                    latest = clean_df.iloc[-1]

                    macd_text = f"MACD: {latest['MACD']:.2f}, Signal: {latest['MACD_Signal']:.2f}"
                    rsi_text = f"RSI14は{latest['RSI_14']:.1f}"
                    sma_text = f"SMA5({latest['SMA_5']:.2f}) vs SMA20({latest['SMA_20']:.2f})"
                    bb_text = f"価格({latest['終値']:.2f})はBB範囲 {latest['BB_Lower']:.2f}〜{latest['BB_Upper']:.2f}"
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

                    save_name = st.text_input("分析結果に名前を付けて保存", value=f"{symbol}_{datetime.date.today()}")
                    if st.button("保存する"):
                        save_strategy_result(save_name, strategy)
                        # サイドバーの履歴を即時更新
                        st.experimental_rerun()

                    st.markdown("\n\n---\n※本戦略はAIによるテクニカル分析に基づいて自動生成された参考情報であり、投資判断はご自身の責任でお願いします。本サービスは投資助言ではありません。")

                    # チャート表示
                    st.subheader("📊 テクニカルチャート")
                    tab1, tab2, tab3 = st.tabs(["📈 ローソク足＋SMA", "📉 MACD", "💹 RSI"])

                    with tab1:
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=df["日付"],
                            open=df["始値"],
                            high=df["高値"],
                            low=df["安値"],
                            close=df["終値"],
                            name="価格"
                        ))
                        fig.add_trace(go.Scatter(x=df["日付"], y=df["SMA_5"], mode="lines", name="SMA 5"))
                        fig.add_trace(go.Scatter(x=df["日付"], y=df["SMA_20"], mode="lines", name="SMA 20"))
                        fig.update_layout(title="ローソク足＋移動平均線", xaxis_title="日付", yaxis_title="価格")
                        st.plotly_chart(fig, use_container_width=True)

                    with tab2:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df["日付"], y=df["MACD"], mode="lines", name="MACD"))
                        fig.add_trace(go.Scatter(x=df["日付"], y=df["MACD_Signal"], mode="lines", name="Signal", line=dict(dash="dot")))
                        fig.update_layout(title="MACD", xaxis_title="日付", yaxis_title="値")
                        st.plotly_chart(fig, use_container_width=True)

                    with tab3:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df["日付"], y=df["RSI_14"], mode="lines", name="RSI"))
                        fig.add_shape(type="line", x0=df["日付"].min(), x1=df["日付"].max(), y0=70, y1=70, line=dict(color="red", dash="dash"))
                        fig.add_shape(type="line", x0=df["日付"].min(), x1=df["日付"].max(), y0=30, y1=30, line=dict(color="green", dash="dash"))
                        fig.update_layout(title="RSI", xaxis_title="日付", yaxis_title="RSI")
                        st.plotly_chart(fig, use_container_width=True)

                        # st.markdown("\n\n---\n※本戦略はAIによるテクニカル分析に基づいて自動生成された参考情報であり、投資判断はご自身の責任でお願いします。本サービスは投資助言ではありません。")

                    # if st.button("Xで共有する", key="x_share_button_yf"):
                    #     with st.spinner("要約を生成中..."):
                    #     with st.spinner("要約を生成中..."):
                    #         summary_chain = load_summary_chain(api_key=OPENAI_API_KEY)
                    #         summary = summary_chain.run({"strategy": strategy})

                    #     hashtags = "#テクニカル分析 #CFD #LazyTech"
                    #     tweet_text = urllib.parse.quote(f"{summary}\n{hashtags}")
                    #     tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"

                    #     st.markdown(
                    #         f'<a href="{tweet_url}" target="_blank">'
                    #         f'<button style="background:#1DA1F2;color:white;border:none;padding:0.5em 1em;border-radius:5px;cursor:pointer;">🕊 Xで投稿</button></a>',
                    #         unsafe_allow_html=True
                    #     )
    # else:
    #     uploaded_file = st.file_uploader("📄 90日以上の株価CSVファイルをアップロード", type=["csv"])
    #     st.markdown('CSVファイルはこちらのサイトからダウンロードできます [investing.com](https://jp.investing.com/markets/)')  

    #     if uploaded_file:
    #         df = pd.read_csv(uploaded_file)
    #         if len(df) < 90:
    #             st.error("⚠️ 90日以上のデータが必要です。")
    #         else:
    #             if st.button("📊 分析する", key="analyze_csv"):
    #                 with st.spinner("AIがデータを分析中..."):
    #                     df = calculate_indicators(df)
                        
    #                     # dfがNoneの場合のエラーハンドリング
    #                     if df is None:
    #                         st.error("⚠️ 指標計算に失敗しました。データを確認してください。")
    #                         st.stop()

    #                     clean_df = df.dropna(subset=[
    #                         "RSI_14", "MACD", "MACD_Signal",
    #                         "BB_Lower", "Stoch_K_14_3", "Stoch_D_14_3"
    #                     ])
    #                     if clean_df.empty:
    #                         st.error("⚠️ 指標計算に必要なデータが不足しています。")
    #                     else:
    #                         latest = clean_df.iloc[-1]

    #                         macd_text = f"MACD: {latest['MACD']:.2f}, Signal: {latest['MACD_Signal']:.2f}"
    #                         rsi_text = f"RSI14は{latest['RSI_14']:.1f}"
    #                         sma_text = f"SMA5({latest['SMA_5']:.2f}) vs SMA20({latest['SMA_20']:.2f})"
    #                         bb_text = f"価格({latest['終値']:.2f})はBB範囲 {latest['BB_Lower']:.2f}〜{latest['BB_Upper']:.2f}"
    #                         stoch_text = f"%K: {latest['Stoch_K_14_3']:.1f}, %D: {latest['Stoch_D_14_3']:.1f}"

    #                         chain = load_strategy_chain(api_key=OPENAI_API_KEY)
    #                         strategy = chain.run({
    #                             "symbol": symbol,
    #                             "macd": macd_text,
    #                             "rsi": rsi_text,
    #                             "sma": sma_text,
    #                             "bb": bb_text,
    #                             "stoch": stoch_text
    #                         })

    #                         st.chat_message("assistant").markdown(strategy)
    #                         st.markdown("\n\n---\n※本戦略はAIによるテクニカル分析に基づいて自動生成された参考情報であり、投資判断はご自身の責任でお願いします。本サービスは投資助言ではありません。")

                            # if st.button("Xで共有する", key="x_share_button_csv"):
                            #     with st.spinner("要約を生成中..."):
                            #         summary_chain = load_summary_chain(api_key=OPENAI_API_KEY)
                            #         summary = summary_chain.run({"strategy": strategy})

                            #     hashtags = "#テクニカル分析 #CFD #LazyTech"
                            #     tweet_text = urllib.parse.quote(f"{summary}\n{hashtags}")
                            #     tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"

                            #     st.markdown(f'<a href="{tweet_url}" target="_blank"><button style="background:#1DA1F2;color:white;border:none;padding:0.5em 1em;border-radius:5px;cursor:pointer;">🕊 Xで投稿</button></a>', unsafe_allow_html=True)

# # ===== ポジションサイズ計算 =====
# elif menu == "ポジションサイズ計算":
#     st.subheader("💰 ポジションサイズ自動計算")

#     symbol = st.text_input("通貨ペア / 銘柄名（任意）", value="S&P500")
#     equity = st.number_input("証拠金残高（円）", min_value=10000, step=1000, value=100000)
#     risk_pct = st.slider("リスク許容率（％）", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
#     stop_loss_pips = st.number_input("損切り幅（pips）", min_value=1.0, value=50.0)
#     leverage = st.number_input("レバレッジ倍率", min_value=1.0, value=10.0)
#     contract_size = st.number_input("取引単位（通貨数）", min_value=100.0, value=10000.0)
#     pip_value = st.number_input("1pipsあたりの円換算額（手動入力）", min_value=0.01, value=1.0)

#     if st.button("📊 ポジションサイズを計算"):
#         risk_amount = equity * (risk_pct / 100)
#         position_size = risk_amount / (stop_loss_pips * pip_value)
#         notional_value = position_size * contract_size
#         required_margin = notional_value / leverage
#         st.info(f"必要証拠金の目安: 約 **¥{round(required_margin):,}**")
