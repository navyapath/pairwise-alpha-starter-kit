import pandas as pd
import numpy as np

def generate_signals(candles_target: pd.DataFrame, candles_anchor: pd.DataFrame) -> pd.DataFrame:
    """
    Strategy: Generate BUY if BTC or ETH had a return >2% exactly 4 hours ago.
              Alternatively, use combined lagged returns to decide BUY/SELL/HOLD.

    Inputs:
    - candles_target: OHLCV for LDO (1H)
    - candles_anchor: Merged OHLCV with columns 'close_BTC' and 'close_ETH' (1H)

    Output:
    - DataFrame with ['timestamp', 'signal']
    """
    try:
        df = pd.merge(
            candles_target[['timestamp', 'close']],
            candles_anchor[['timestamp', 'close_BTC', 'close_ETH']],
            on='timestamp',
            how='inner'
        )

        # Compute lagged returns (4 hours ago)
        df['btc_return_4h_ago'] = df['close_BTC'].pct_change().shift(4)
        df['eth_return_4h_ago'] = df['close_ETH'].pct_change().shift(4)

        # Add current returns for correlation-based strategy
        df['ret_target'] = df['close'].pct_change()
        df['ret_btc'] = df['close_BTC'].pct_change().shift(1)
        df['ret_eth'] = df['close_ETH'].pct_change().shift(1)
        df['anchor_signal'] = df['ret_btc'] + df['ret_eth']

        # Signal logic
        signals = []
        for i in range(len(df)):
            btc_pump = df['btc_return_4h_ago'].iloc[i] > 0.02
            eth_pump = df['eth_return_4h_ago'].iloc[i] > 0.02
            anchor_momentum = df['anchor_signal'].iloc[i]

            if btc_pump or eth_pump or anchor_momentum > 0.015:
                signals.append('BUY')
            elif anchor_momentum < -0.015:
                signals.append('SELL')
            else:
                signals.append('HOLD')

        df['signal'] = signals
        return df[['timestamp', 'signal']].dropna().reset_index(drop=True)

    except Exception as e:
        raise RuntimeError(f"Error in generate_signals: {e}")


def get_coin_metadata() -> dict:
    """
    Specifies the target and anchor coins used in this strategy.

    Returns:
    {
        "target": {"symbol": "LDO", "timeframe": "1H"},
        "anchors": [
            {"symbol": "BTC", "timeframe": "1H"},
            {"symbol": "ETH", "timeframe": "1H"}
        ]
    }
    """
    return {
        "target": {
            "symbol": "LDO",
            "timeframe": "1H"
        },
        "anchors": [
            {"symbol": "BTC", "timeframe": "1H"},
            {"symbol": "ETH", "timeframe": "1H"}
        ]
    }
