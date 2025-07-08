import asyncio
from openai import AsyncOpenAI
from config import MODEL_NAME

class TextAnalyzer:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def moderate_text(self, text: str):
        resp = await self.client.moderations.create(
            input=text,
            model="omni-moderation-latest",
        )
        cats = resp.results[0].categories
        scores = resp.results[0].category_scores
        return cats, scores

    async def get_aggressiveness_score(
        self,
        text: str,
        temperature: float = 1.0,
        top_p: float = 0.9,
        max_retries: int = 3,
    ):
        prompt = f"""
あなたソーシャルメディアの投稿を分析し、その攻撃性を評価する専門家です。
以下の評価基準と例を参考に、与えられた文章の攻撃性スコアを0から9の整数で決定し、
その理由を40〜60文字で簡潔に説明してください。

# 評価基準:
- 0: 攻撃性なし。中立的で誰に対しても敵意が感じられない。
- 1-2: 非常に軽度の攻撃性。配慮に欠ける表現だが、攻撃意図が明確ではない。
- 3-4: 軽度の攻撃性。間接的な批判や皮肉が含まれている。
- 5-6: 中程度の攻撃性。明確な批判や侮辱的な表現が見られる。
- 7-8: 高度の攻撃性。強い侮辱や敵意を伴う表現。
- 9: 極度の攻撃性。暴力的な脅迫や人権侵害を伴うような非常に攻撃的な内容。

# 評価例:
---
- 文章: "この映画、正直言って時間の無駄だったな。"
- スコア: 3
- 理由: 個人的な感想だが、作品を否定するやや強い表現が使われているため。
---
- 文章: "新製品の発表会、楽しみにしてます！応援してます！"
- スコア: 0
- 理由: 攻撃的な要素はなく、ポジティブで応援する内容であるため。
---
- 文章: "あいつのせいで全部台無しだ。絶対に許さない。"
- スコア: 8
- 理由: 特定の個人への強い敵意と攻撃的な言葉が明確に含まれているため。
---

# 分析対象の文章:
{text}

# 回答形式:
スコア: [0-9の整数]
理由: [40-60文字での具体的な理由]
"""
        for _ in range(max_retries):
            try:
                resp = await self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You analyze text and rate aggressiveness."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    top_p=top_p,
                )
                content = resp.choices[0].message.content.strip()
                score = None
                reason = None
                for line in content.split("\n"):
                    if line.startswith("スコア"):
                        val = line.split(":", 1)[1].strip()
                        if val.isdigit():
                            score = int(val)
                    elif line.startswith("理由"):
                        reason = line.split(":", 1)[1].strip()
                if score is not None and reason:
                    return score, reason
            except Exception:
                await asyncio.sleep(1)
        return None, None
