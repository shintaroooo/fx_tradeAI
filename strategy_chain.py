from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

def load_strategy_chain(api_key: str):
    prompt_template = """
あなたはプロのテクニカルトレーダーです。
以下のテクニカル指標に基づいて、{symbol} の今後1週間の戦略を生成してください：
・最新の指標データに基づいています
・ロングとショートの両戦略をそれぞれ提示してください

- MACD: {macd}
- RSI: {rsi}
- SMA: {sma}
- ボリンジャーバンド: {bb}
- ストキャスティクス: {stoch}

【出力フォーマット】
1. 現在のトレンド分析
2. 勝率の高いエントリータイミング
3. 利確と損切り目安
4. 注意点とアドバイス
"""

    prompt = ChatPromptTemplate.from_template(prompt_template)

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5, openai_api_key=api_key)

    return LLMChain(llm=llm, prompt=prompt, output_key="strategy")
