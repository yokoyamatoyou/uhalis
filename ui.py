import asyncio
import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

from analyzer import TextAnalyzer
from config import ConfigManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModerationApp(ctk.CTk):
    """GUI application for running text moderation."""

    def __init__(self, analyzer: TextAnalyzer, config: ConfigManager):
        """Create the application and build the UI."""
        super().__init__()
        self.analyzer = analyzer
        self.config = config
        self.df = None
        self.temperature = config.get_temperature()
        self.top_p = config.get_top_p()
        self.weights = config.data.get("weights", {})
        self.updating_weights = False
        self.create_ui()

    def create_ui(self):
        """Initialize all widgets for both tabs."""
        self.title("テキストモデレーションツール")
        self.geometry("800x600")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        self.main_tab = self.tabview.add("メイン")
        self.settings_tab = self.tabview.add("設定")

        # main tab widgets
        self.status_label = ctk.CTkLabel(self.main_tab, text="ファイルを選択してください")
        self.status_label.pack(pady=10)

        self.upload_button = ctk.CTkButton(self.main_tab, text="ファイルを選択", command=self.load_excel_file)
        self.upload_button.pack(pady=5)

        self.column_combo = ctk.CTkComboBox(self.main_tab, values=[])
        self.column_combo.pack(pady=5)

        self.analyze_button = ctk.CTkButton(self.main_tab, text="分析開始", state="disabled", command=self.start_analysis)
        self.analyze_button.pack(pady=5)

        self.save_button = ctk.CTkButton(self.main_tab, text="結果を保存", state="disabled", command=self.save_results)
        self.save_button.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.main_tab, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # settings tab widgets
        param_frame = ctk.CTkFrame(self.settings_tab)
        param_frame.pack(pady=10)

        ctk.CTkLabel(param_frame, text="Temperature").grid(row=0, column=0, padx=10, pady=5)
        self.temp_entry = ctk.CTkEntry(param_frame, width=60)
        self.temp_entry.grid(row=0, column=1, padx=10)
        self.temp_entry.insert(0, str(self.temperature))

        ctk.CTkLabel(param_frame, text="Top-p").grid(row=0, column=2, padx=10)
        self.top_p_entry = ctk.CTkEntry(param_frame, width=60)
        self.top_p_entry.grid(row=0, column=3, padx=10)
        self.top_p_entry.insert(0, str(self.top_p))

        self.weight_frame = ctk.CTkFrame(self.settings_tab)
        self.weight_frame.pack(pady=10, fill="x")
        self.weight_sliders = {}
        for i, (key, val) in enumerate(self.weights.items()):
            ctk.CTkLabel(self.weight_frame, text=key).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            slider = ctk.CTkSlider(
                self.weight_frame,
                from_=0,
                to=2.0,
                number_of_steps=100,
                command=lambda v, k=key: self.on_weight_change(k, v),
            )
            slider.set(val)
            slider.grid(row=i, column=1, padx=10, pady=5)
            self.weight_sliders[key] = slider

        self.remaining_weight_label = ctk.CTkLabel(self.settings_tab, text="未分配の重み: 0.0")
        self.remaining_weight_label.pack(pady=5)
        self.update_weight_info()

    def load_excel_file(self):
        """Open an Excel file and populate the column selector."""
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        try:
            self.df = pd.read_excel(file_path, sheet_name=0)
            self.column_combo.configure(values=list(self.df.columns))
            if self.df.columns:
                self.column_combo.set(self.df.columns[0])
            self.status_label.configure(text=f"ファイルを読み込みました: {len(self.df)}件")
            self.update_weight_info()
        except Exception as e:
            self.status_label.configure(text="ファイルの読み込みに失敗", text_color="red")
            messagebox.showerror("読み込みエラー", str(e))

    def validate_parameters(self):
        """Validate temperature and top-p entries.

        Returns
        -------
        bool
            ``True`` if both values can be converted to ``float``.
        """
        try:
            self.temperature = float(self.temp_entry.get())
            self.top_p = float(self.top_p_entry.get())
            self.config.set_temperature(self.temperature)
            self.config.set_top_p(self.top_p)
            return True
        except ValueError:
            messagebox.showerror("エラー", "数値を入力してください")
            return False

    def on_weight_change(self, key: str, value: float):
        """Redistribute weights so that the total remains 1.0."""
        if self.updating_weights:
            return
        self.updating_weights = True
        try:
            others = {k: s for k, s in self.weight_sliders.items() if k != key}
            leftover = max(1.0 - value, 0.0)
            others_sum = sum(s.get() for s in others.values())
            if others:
                if others_sum == 0:
                    share = leftover / len(others)
                    for s in others.values():
                        s.set(share)
                else:
                    for s in others.values():
                        s.set(s.get() / others_sum * leftover)
        finally:
            self.updating_weights = False
            self.update_weight_info()

    def update_weight_info(self):
        """Update remaining-weight display and button states."""
        total = sum(slider.get() for slider in self.weight_sliders.values())
        remaining = 1.0 - total
        self.remaining_weight_label.configure(text=f"未分配の重み: {remaining:.2f}")
        if remaining < 0:
            self.remaining_weight_label.configure(text_color="red")
            self.analyze_button.configure(state="disabled")
        else:
            self.remaining_weight_label.configure(text_color="white")
            if self.df is not None:
                self.analyze_button.configure(state="normal")

    def start_analysis(self):
        """Begin analysis of the loaded file in a worker thread."""
        if not self.validate_parameters():
            return
        self.analyze_button.configure(state="disabled")
        self.upload_button.configure(state="disabled")
        threading.Thread(target=lambda: asyncio.run(self.analyze_file_async())).start()

    async def analyze_file_async(self):
        """Run moderation on each row of ``self.df`` asynchronously."""
        column = self.column_combo.get()
        category_names = ["hate", "hate/threatening", "self-harm", "sexual",
                          "sexual/minors", "violence", "violence/graphic"]
        category_flags = {name: [] for name in category_names}
        category_scores = {name: [] for name in category_names}
        ag_scores = []
        ag_reasons = []
        total_rows = len(self.df)

        for idx, row in self.df.iterrows():
            text = row[column]
            cats, scores = await self.analyzer.moderate_text(text)
            if cats is None or scores is None:
                for name in category_names:
                    category_flags[name].append(False)
                    category_scores[name].append(0.0)
            else:
                for name in category_names:
                    category_flags[name].append(getattr(cats, name.replace("/", "_"), False))
                    category_scores[name].append(getattr(scores, name.replace("/", "_"), 0.0))
            score, reason = await self.analyzer.get_aggressiveness_score(text, self.temperature, self.top_p)
            ag_scores.append(score)
            ag_reasons.append(reason)

            progress = (idx + 1) / total_rows
            self.progress_bar.set(progress)
            self.status_label.configure(text=f"分析中... {idx + 1}/{total_rows}")

        for name in category_names:
            self.df[f"{name}_flag"] = category_flags[name]
            self.df[f"{name}_score"] = category_scores[name]
        self.df["aggressiveness_score"] = ag_scores
        self.df["aggressiveness_reason"] = ag_reasons

        weights = {k: slider.get() for k, slider in self.weight_sliders.items()}
        self.config.data["weights"] = weights
        self.config.set_temperature(self.temperature)
        self.config.set_top_p(self.top_p)
        self.config.save()
        self.apply_total_score(weights)
        self.status_label.configure(text="分析が完了しました", text_color="green")
        self.save_button.configure(state="normal")
        self.upload_button.configure(state="normal")
        self.analyze_button.configure(state="normal")

    def apply_total_score(self, weights):
        """Calculate a weighted aggression score for each row."""
        def calc(row):
            val = 0.0
            val += weights.get("hate_score", 0) * row.get("hate_score", 0)
            val += weights.get("hate/threatening_score", 0) * row.get("hate/threatening_score", 0)
            val += weights.get("violence_score", 0) * row.get("violence_score", 0)
            val += weights.get("sexual_score", 0) * row.get("sexual_score", 0)
            val += weights.get("sexual/minors_score", 0) * row.get("sexual/minors_score", 0)
            ag = row.get("aggressiveness_score") or 0
            val += weights.get("aggressiveness_score", 0) * ag
            val += weights.get("flag_hate", 0) * (1 if row.get("hate_flag") else 0)
            val += weights.get("flag_hate/threatening", 0) * (1 if row.get("hate/threatening_flag") else 0)
            val += weights.get("flag_violence", 0) * (1 if row.get("violence_flag") else 0)
            val += weights.get("flag_sexual", 0) * (1 if row.get("sexual_flag") else 0)
            return val

        self.df["total_aggression"] = self.df.apply(calc, axis=1)

    def save_results(self):
        """Save the processed DataFrame to a new Excel file."""
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not save_path:
            return
        try:
            self.df.to_excel(save_path, index=False)
            self.status_label.configure(text="結果を保存しました", text_color="green")
        except Exception as e:
            self.status_label.configure(text="保存に失敗しました", text_color="red")
            messagebox.showerror("保存エラー", str(e))

