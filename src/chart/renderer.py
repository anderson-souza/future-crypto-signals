import io
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from src.chart.exceptions import ChartRenderError
from src.chart.models import ChartConfig, ChartData
from src.exceptions import InsufficientDataError
from src.indicators.rsi import calculate_rsi_series
from src.indicators.sma import calculate_sma_series
from src.indicators.supertrend import calculate_supertrend_series
from src.indicators.utils import candles_to_df
from src.signals.models import SignalDirection


def render_chart(data: ChartData, config: ChartConfig | None = None) -> bytes:
    if config is None:
        config = ChartConfig.from_env()

    window_candles = data.candles[-config.window :]
    if not window_candles:
        raise InsufficientDataError(required=1, got=0)

    df = candles_to_df(window_candles)

    rsi = calculate_rsi_series(window_candles, data.config.rsi_period)
    sma_short = calculate_sma_series(window_candles, data.config.sma_short_period)
    sma_long = calculate_sma_series(window_candles, data.config.sma_long_period)
    st_value, st_dir = calculate_supertrend_series(
        window_candles, data.config.supertrend_period, data.config.supertrend_multiplier
    )

    st_bullish = st_value.where(st_dir == 1)
    st_bearish = st_value.where(st_dir == -1)

    buy_markers = pd.Series(float("nan"), index=df.index)
    sell_markers = pd.Series(float("nan"), index=df.index)

    for signal in data.signals:
        if signal.timestamp not in df.index:
            continue
        if signal.direction == SignalDirection.BUY:
            buy_markers.loc[signal.timestamp] = df.loc[signal.timestamp, "high"] * 1.002
        elif signal.direction == SignalDirection.SELL:
            sell_markers.loc[signal.timestamp] = df.loc[signal.timestamp, "low"] * 0.998

    addplots = [
        mpf.make_addplot(sma_short, color="#f5a623", width=1.2),
        mpf.make_addplot(sma_long, color="#4a9eff", width=1.2),
        mpf.make_addplot(rsi, panel=1, color="#b39ddb", ylabel="RSI", secondary_y=False),
        mpf.make_addplot(
            pd.Series(50.0, index=df.index),
            panel=1,
            color="#555555",
            linestyle="--",
            width=0.8,
            secondary_y=False,
        ),
    ]

    if st_bullish.notna().any():
        addplots.append(mpf.make_addplot(st_bullish, color="#26a69a", width=1.5))
    if st_bearish.notna().any():
        addplots.append(mpf.make_addplot(st_bearish, color="#ef5350", width=1.5))
    if buy_markers.notna().any():
        addplots.append(
            mpf.make_addplot(buy_markers, type="scatter", markersize=120, marker="^", color="#26a69a")
        )
    if sell_markers.notna().any():
        addplots.append(
            mpf.make_addplot(sell_markers, type="scatter", markersize=120, marker="v", color="#ef5350")
        )

    first = data.signals[0] if data.signals else None
    symbol = first.symbol if first else "—"
    timeframe = first.timeframe if first else "—"
    n_buy = sum(1 for s in data.signals if s.direction == SignalDirection.BUY)
    n_sell = sum(1 for s in data.signals if s.direction == SignalDirection.SELL)
    title = f"{symbol} • {timeframe} • {n_buy} BUY  {n_sell} SELL"

    fig = None
    try:
        fig, _ = mpf.plot(
            df,
            type="candle",
            style="nightclouds",
            addplot=addplots,
            title=title,
            panel_ratios=(3, 1),
            returnfig=True,
            figsize=(14, 8),
            tight_layout=True,
        )
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        return buf.getvalue()
    finally:
        if fig is not None:
            plt.close(fig)
