# uhalis

This project provides a text moderation tool that evaluates the aggressiveness of social media posts. The application uses OpenAI's GPT models and presents a customtkinter based GUI.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key in the `OPENAI_API_KEY` environment variable.
3. Run the application:
   ```bash
   python main.py
   ```

The UI allows you to load an Excel file, select the column to analyze, and start moderation. You can adjust parameters and weight settings in the **設定** tab. Results can be saved back to an Excel file. Configuration values—including temperature, top-p, and the weight settings—are saved to `config.json`. The default weights sum to `1.0`, so you can start analyzing without tweaking them first.
