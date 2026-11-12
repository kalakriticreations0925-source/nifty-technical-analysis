"""
Signal Notifier and Report Generator.
Formats signals into CLI tables, Markdown reports, JSON feeds, and Telegram/Discord webhooks.
"""
import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from src.data.types import Signal, SignalType, BacktestResult


class SignalNotifier:
    """
    Handles formatting and dispatching generated trading signals.
    """
    @staticmethod
    def format_terminal_table(signals: List[Signal]) -> str:
        """Formats signals into a clean ANSI colored ASCII table."""
        if not signals:
            return "No signals generated."

        # ANSI Colors
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        headers = ["Symbol", "Timestamp", "Signal", "Price (₹)", "Stop Loss", "Target", "R:R", "Conf.", "Strategy"]
        col_widths = [12, 12, 8, 12, 12, 12, 6, 8, 22]

        border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_str = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"

        lines = [border, header_str, border]

        for s in signals:
            sig_color = GREEN if s.signal_type == SignalType.BUY else (RED if s.signal_type == SignalType.SELL else YELLOW)
            sig_text = f"{sig_color}{BOLD}{s.signal_type.value.ljust(col_widths[2])}{RESET}"

            row = [
                s.symbol.ljust(col_widths[0]),
                s.timestamp.ljust(col_widths[1]),
                sig_text,
                f"₹{s.price:,.2f}".rjust(col_widths[3]),
                f"₹{s.stop_loss:,.2f}".rjust(col_widths[4]),
                f"₹{s.target:,.2f}".rjust(col_widths[5]),
                f"{s.risk_reward_ratio:.1f}".rjust(col_widths[6]),
                f"{int(s.confidence * 100)}%".rjust(col_widths[7]),
                s.strategy_name.ljust(col_widths[8])
            ]
            lines.append("| " + " | ".join(row) + " |")

        lines.append(border)
        return "\n".join(lines)

    @staticmethod
    def generate_markdown_report(signals: List[Signal], backtest: Optional[BacktestResult] = None) -> str:
        """Generates a complete GitHub Markdown report with tables and analysis."""
        lines = [
            "# 📈 Nifty Technical Analysis & Trading Signals Report",
            f"**Generated at:** Automated Pipeline",
            "",
            "## 🚨 Latest Signals",
            "",
            "| Symbol | Signal | Price (₹) | Stop Loss (₹) | Target (₹) | Risk/Reward | Confidence | Strategy | Rationale |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |"
        ]

        for s in signals:
            icon = "🟢 **BUY**" if s.signal_type == SignalType.BUY else ("🔴 **SELL**" if s.signal_type == SignalType.SELL else "⚪ HOLD")
            lines.append(
                f"| `{s.symbol}` | {icon} | ₹{s.price:,.2f} | ₹{s.stop_loss:,.2f} | ₹{s.target:,.2f} | 1:{s.risk_reward_ratio} | {int(s.confidence * 100)}% | {s.strategy_name} | {s.rationale} |"
            )

        if backtest:
            lines.extend([
                "",
                "## 📊 Backtest Performance Summary",
                "",
                "| Metric | Value |",
                "| :--- | :--- |",
                f"| **Strategy** | `{backtest.strategy_name}` |",
                f"| **Symbol** | `{backtest.symbol}` |",
                f"| **Initial Capital** | ₹{backtest.initial_capital:,.2f} |",
                f"| **Final Capital** | ₹{backtest.final_equity:,.2f} |",
                f"| **Total Return** | **{backtest.total_return_pct:.2f}%** |",
                f"| **CAGR** | {backtest.cagr_pct:.2f}% |",
                f"| **Sharpe Ratio** | {backtest.sharpe_ratio:.2f} |",
                f"| **Max Drawdown** | {backtest.max_drawdown_pct:.2f}% |",
                f"| **Win Rate** | {backtest.win_rate_pct:.1f}% ({backtest.winning_trades}/{backtest.total_trades} trades) |",
                f"| **Profit Factor** | {backtest.profit_factor:.2f} |"
            ])

        lines.extend([
            "",
            "> **Disclaimer:** *This analysis is generated using algorithmic technical analysis indicators and is intended for informational and educational purposes only. Not financial or investment advice. Always manage your risk.*"
        ])

        return "\n".join(lines)

    @staticmethod
    def save_json(signals: List[Signal], output_path: str):
        """Saves signals list to JSON."""
        data = [s.to_dict() for s in signals]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def send_webhook(webhook_url: str, content: str) -> bool:
        """Sends payload to Discord/Telegram/Slack webhook URL."""
        if not webhook_url:
            return False
        payload = json.dumps({"content": content, "text": content}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "NiftySignalNotifier/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in (200, 204)
        except Exception:
            return False
