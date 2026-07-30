# Naver Finance route

The observable route is:

```text
https://api.finance.naver.com/siseJson.naver
```

with a six-digit `symbol`, `requestType=1`, `startTime=YYYYMMDD`,
`endTime=YYYYMMDD`, and `timeframe=day`.

The response is a Python/JavaScript-style array rather than strict JSON. The
Skill parses it as literals only and requires the first six headers to be:

```text
날짜, 시가, 고가, 저가, 종가, 거래량
```

Exact response text is retained because this is observable behavior, not a
versioned public API contract.
