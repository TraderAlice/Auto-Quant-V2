# Official TWSE route

The official historical page is:

```text
https://www.twse.com.tw/en/trading/historical/stock-day.html
```

The narrow monthly JSON route used by this Skill is:

```text
https://www.twse.com.tw/rwd/en/afterTrading/STOCK_DAY
```

with `date=YYYYMM01`, `stockNo=<code>`, and `response=json`.

Expected fields include session date, trade volume, trade value, open, high,
low, close, change, and transaction count. The response often represents
dates in the Republic of China calendar. The Skill maps fields by normalized
field names and fails if required fields are absent.

TWSE's OpenAPI also advertises
`/v1/exchangeReport/STOCK_DAY_ALL`, but that route is a market-wide snapshot,
not a substitute for bounded individual-security history.

The official site can return an HTML security block for some hosts or
networks. That is a provider-access failure and must remain visible.
