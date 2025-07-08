import os
from openai import AsyncOpenAI

from config import ConfigManager
from analyzer import TextAnalyzer
from ui import ModerationApp


def main():
    config = ConfigManager()
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if client.api_key is None:
        raise ValueError("OpenAI APIキーが設定されていません。環境変数 'OPENAI_API_KEY' を設定してください。")
    analyzer = TextAnalyzer(client)
    app = ModerationApp(analyzer, config)
    app.mainloop()


if __name__ == "__main__":
    main()
