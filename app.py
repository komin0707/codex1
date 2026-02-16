import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st


BYBIT_KLINE_PATH = "/v5/market/kline"


@dataclass
class SignalResult:
    matched: bool
    reason: str
    candle_start_ms: int
    candle_close_ms: int


def timeframe_to_seconds(tf: str) -> int:
    return int(tf) * 60


def fetch_klines(base_url: str, symbol: str, interval: str, limit: int = 50) -> pd.DataFrame:
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    response = requests.get(f"{base_url.rstrip('/')}{BYBIT_KLINE_PATH}", params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()

    if payload.get("retCode") != 0:
        raise RuntimeError(f"Bybit API 에러: {payload.get('retMsg', 'unknown')} ({payload.get('retCode')})")

    rows = payload["result"]["list"]
    if not rows:
        raise RuntimeError("캔들 데이터를 가져오지 못했습니다.")

    df = pd.DataFrame(
        rows,
        columns=[
            "start_ms",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
        ],
    )
    numeric_cols = ["open", "high", "low", "close", "volume", "turnover"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["start_ms"] = pd.to_numeric(df["start_ms"], errors="coerce")
    df = df.dropna().sort_values("start_ms").reset_index(drop=True)
    return df


def is_strong_bearish(candle: pd.Series) -> bool:
    total_range = candle["high"] - candle["low"]
    if total_range <= 0:
        return False

    body = abs(candle["open"] - candle["close"])
    upper_wick = candle["high"] - candle["open"]
    lower_wick = candle["close"] - candle["low"]

    if candle["close"] >= candle["open"]:
        return False

    body_ratio = body / total_range
    wick_ratio = (upper_wick + lower_wick) / total_range

    return body_ratio >= 0.8 and wick_ratio <= 0.2 and lower_wick / total_range <= 0.05


def count_consecutive_bullish(df: pd.DataFrame, end_idx_exclusive: int) -> int:
    count = 0
    for i in range(end_idx_exclusive - 1, -1, -1):
        if df.loc[i, "close"] > df.loc[i, "open"]:
            count += 1
        else:
            break
    return count


def evaluate_signal(df: pd.DataFrame, interval: str) -> SignalResult:
    if len(df) < 12:
        return SignalResult(False, "데이터 부족", 0, 0)

    df = df.copy()
    df["ma5"] = df["close"].rolling(5).mean()

    target = df.iloc[-1]
    prev = df.iloc[:-1]

    bullish_streak = count_consecutive_bullish(prev, len(prev))
    if bullish_streak < 5:
        return SignalResult(False, f"연속 양봉 부족 ({bullish_streak})", int(target["start_ms"]), 0)

    if len(prev) < 2:
        return SignalResult(False, "기준 양봉 확인 불가", int(target["start_ms"]), 0)

    second_prev_bull = prev.iloc[-2]
    if second_prev_bull["close"] <= second_prev_bull["open"]:
        return SignalResult(False, "직전 두번째 캔들이 양봉이 아님", int(target["start_ms"]), 0)

    if pd.isna(target["ma5"]):
        return SignalResult(False, "MA5 계산 불가", int(target["start_ms"]), 0)

    if not is_strong_bearish(target):
        return SignalResult(False, "꽉 채우는 음봉 조건 미충족", int(target["start_ms"]), 0)

    if not (target["low"] < second_prev_bull["low"] and target["close"] < target["ma5"]):
        return SignalResult(False, "저가/5일선 하향 이탈 미충족", int(target["start_ms"]), 0)

    interval_sec = timeframe_to_seconds(interval)
    candle_close_ms = int(target["start_ms"] + interval_sec * 1000)

    return SignalResult(True, "조건 충족", int(target["start_ms"]), candle_close_ms)


def remaining_seconds_to_close(candle_close_ms: int) -> float:
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    return (candle_close_ms - now_ms) / 1000


def send_telegram(bot_token: str, chat_id: str, text: str) -> Tuple[bool, str]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    if resp.status_code != 200:
        return False, f"텔레그램 전송 실패: HTTP {resp.status_code}"

    body = resp.json()
    if not body.get("ok"):
        return False, f"텔레그램 API 실패: {body}"

    return True, "전송 성공"


def analyze_once(config: Dict[str, str], intervals: List[str]) -> List[str]:
    notices: List[str] = []

    for interval in intervals:
        try:
            df = fetch_klines(config["base_url"], config["symbol"], interval)
            result = evaluate_signal(df, interval)

            if not result.matched:
                notices.append(f"[{interval}분봉] 미충족 - {result.reason}")
                continue

            remaining = remaining_seconds_to_close(result.candle_close_ms)
            alert_key = f"{config['symbol']}:{interval}:{result.candle_start_ms}"

            if 0 < remaining <= 60:
                if alert_key not in st.session_state["alerted_keys"]:
                    kst_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    message = (
                        f"[매매 알림] {config['symbol']} {interval}분봉 조건 감지\n"
                        f"- 연속 양봉 5개 이상 후 강한 음봉\n"
                        f"- 직전 두번째 양봉 저가 및 MA5 하향 이탈\n"
                        f"- 캔들 마감 1분 이내 (남은 {remaining:.1f}초)\n"
                        f"- 감지 시각: {kst_now}"
                    )
                    ok, msg = send_telegram(config["telegram_token"], config["telegram_chat_id"], message)
                    if ok:
                        st.session_state["alerted_keys"].add(alert_key)
                    notices.append(f"[{interval}분봉] {msg}")
                else:
                    notices.append(f"[{interval}분봉] 이미 알림 전송됨")
            else:
                notices.append(f"[{interval}분봉] 조건 충족, 마감 1분 전 구간 아님 (남은 {remaining:.1f}초)")

        except Exception as exc:
            notices.append(f"[{interval}분봉] 오류 - {exc}")

    return notices


def main() -> None:
    st.set_page_config(page_title="Bybit 캔들 알림", page_icon="📈", layout="wide")
    st.title("📈 Bybit 조건 알림 프로그램")

    st.caption("연속 양봉 후 조건형 음봉이 발생하고 캔들 마감 1분 전일 때 텔레그램으로 알림")

    if "running" not in st.session_state:
        st.session_state["running"] = False
    if "alerted_keys" not in st.session_state:
        st.session_state["alerted_keys"] = set()

    with st.sidebar:
        st.header("설정")
        base_url = st.text_input("Bybit API 주소", value="https://api.bybit.com")
        symbol = st.text_input("심볼", value="BTCUSDT")
        bybit_api_key = st.text_input("Bybit API Key (선택)", type="password")
        _ = bybit_api_key  # 추후 private endpoint 확장 대비

        st.subheader("텔레그램")
        telegram_token = st.text_input("Bot Token", type="password")
        telegram_chat_id = st.text_input("Chat ID")

        st.subheader("분석 봉")
        selected_intervals = st.multiselect(
            "분석할 분봉 선택",
            options=["5", "15", "30", "60"],
            default=["5", "15", "30", "60"],
        )

        refresh_sec = st.slider("분석 주기(초)", min_value=5, max_value=60, value=10, step=5)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶ 분석 시작", use_container_width=True):
            st.session_state["running"] = True
    with c2:
        if st.button("⏹ 분석 중지", use_container_width=True):
            st.session_state["running"] = False
    with c3:
        if st.button("🔄 알림 이력 초기화", use_container_width=True):
            st.session_state["alerted_keys"] = set()

    status_placeholder = st.empty()
    log_placeholder = st.empty()

    if st.session_state["running"]:
        if not selected_intervals:
            status_placeholder.error("분석할 분봉을 최소 1개 이상 선택하세요.")
        elif not telegram_token or not telegram_chat_id:
            status_placeholder.error("텔레그램 Bot Token과 Chat ID를 입력하세요.")
        else:
            status_placeholder.success("🟢 분석 중... (자동 갱신)")
            with st.spinner("시장 데이터 분석 중"):
                logs = analyze_once(
                    {
                        "base_url": base_url,
                        "symbol": symbol.upper(),
                        "telegram_token": telegram_token,
                        "telegram_chat_id": telegram_chat_id,
                    },
                    selected_intervals,
                )

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_placeholder.code(f"[{now}]\n" + "\n".join(logs), language="text")
            time.sleep(refresh_sec)
            st.rerun()
    else:
        status_placeholder.info("⚪ 대기 중 - '분석 시작' 버튼을 누르세요.")


if __name__ == "__main__":
    main()
