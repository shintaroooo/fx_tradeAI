from langchain.chat_models import ChatOpenAI
from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain


def load_summary_chain(api_key: str):
    examples = [
        {
            "strategy": "MACDがデッドクロス、RSIが30以下、ストキャスも下落中で弱気相場。",
            "summary": "テクニカル指標は全体的に弱気。売り優勢の展開。"
        },
        {
            "strategy": "SMAがゴールデンクロス、RSIは50を上抜け、MACDも好転中。",
            "summary": "上昇トレンド形成中。押し目買い戦略が有効。"
        }
    ]

    example_prompt = PromptTemplate(
        input_variables=["strategy"],
        template="戦略: {strategy}\n要約: "
    )

    prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        suffix="戦略: {strategy}\n要約: ",
        input_variables=["strategy"]
    )

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5, openai_api_key=api_key)

    return LLMChain(llm=llm, prompt=prompt, output_key="summary")


def load_strategy_chain(api_key: str):
    prompt_template = """
あなたはプロのテクニカルトレーダーです。
以下のテクニカル指標に基づいて、{symbol} の今後1週間の戦略を生成してください：
尚、指標は最新のものを使用し、ショート・ロングの両方の戦略を考慮してください。

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

    llm = ChatOpenAI(
        openai_api_key=api_key,
        model_name="gpt-4o-mini",
        temperature=0.5
    )

    return LLMChain(llm=llm, prompt=prompt, output_key="strategy")
