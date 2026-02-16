# Bybit 매매 알림 프로그램

Bybit Kline 데이터를 기반으로 아래 조건이 충족될 때 텔레그램 알림을 보내는 Streamlit 앱입니다.

## 감지 조건
1. 직전 구간에 **연속 양봉 5개 이상**
2. 현재(형성 중) 캔들이 **강한 음봉(꽉 채우는 음봉)**
3. 현재 캔들 저가가 **직전 두번째 양봉 저가 하향 이탈**
4. 현재 캔들 종가가 **MA5(5일선) 아래**
5. 캔들 마감까지 **60초 이내**인 경우에만 알림 전송

> "다시 말아올리면 안됨" 조건은 하단 꼬리가 매우 짧은 강한 음봉(몸통 비율 >= 80%)으로 반영했습니다.

## UI 기능
- Bybit API 주소 입력
- 텔레그램 Bot Token / Chat ID 입력
- 5 / 15 / 30 / 60분봉 선택
- 분석 중/대기 상태를 직관적으로 표시

## 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 참고
- 본 앱은 public kline endpoint만 사용하므로 Bybit API Key 없이도 동작합니다.
- 동일 캔들에 대해 중복 텔레그램 전송을 방지합니다.
