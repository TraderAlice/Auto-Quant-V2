import { candles, factorSignal } from "@/lib/data";

function linePath(values, width, height, padding = 18) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  return values
    .map((value, index) => {
      const x = padding + (index / (values.length - 1)) * (width - padding * 2);
      const y = height - padding - ((value - min) / Math.max(1, max - min)) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function EvidenceChart({ cursorRatio = 0.55, compact = false }) {
  const width = 820;
  const height = compact ? 210 : 260;
  const candleWidth = 13;
  const gap = (width - 54) / candles.length;
  const cursorX = 28 + cursorRatio * (width - 56);
  const signalPath = linePath(factorSignal, width, height, 28);

  return (
    <div className="chart-shell">
      <span className="chart-axis-label top">标准化价格 / 因子信号</span>
      <span className="chart-axis-label bottom">5m · CST</span>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="evidence-chart-title evidence-chart-desc">
        <title id="evidence-chart-title">K 线、因子信号与回放时点</title>
        <desc id="evidence-chart-desc">价格整体上行，因子信号在上午十点后增强。青色竖线表示当前回放可见时点。</desc>
        <g aria-hidden="true">
          {candles.map(([open, high, low, close], index) => {
            const x = 28 + index * gap;
            const y = (value) => height - 24 - (value / 105) * (height - 44);
            const rising = close >= open;
            return (
              <g key={index} opacity={x <= cursorX ? 0.95 : 0.22}>
                <line x1={x} x2={x} y1={y(high)} y2={y(low)} stroke={rising ? "#afbdcb" : "#728198"} strokeWidth="1" />
                <rect
                  x={x - candleWidth / 2}
                  y={Math.min(y(open), y(close))}
                  width={candleWidth}
                  height={Math.max(3, Math.abs(y(open) - y(close)))}
                  fill={rising ? "#5d7f8d" : "#4a596c"}
                  stroke={rising ? "#afbdcb" : "#728198"}
                  strokeWidth="1"
                />
              </g>
            );
          })}
          <path d={signalPath} fill="none" stroke="#f1b35c" strokeWidth="2" opacity="0.9" />
          <path d={`${signalPath} L792,${height - 22} L28,${height - 22} Z`} fill="url(#signal-fill)" opacity="0.17" />
          <defs>
            <linearGradient id="signal-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#f1b35c" />
              <stop offset="1" stopColor="#f1b35c" stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1={cursorX} x2={cursorX} y1="0" y2={height} stroke="#52c7d9" strokeWidth="1.5" />
          <rect x={cursorX + 5} y="30" width="58" height="19" fill="#142b36" stroke="#52c7d9" />
          <text x={cursorX + 34} y="43" fill="#91e4ef" fontFamily="Cascadia Mono, monospace" fontSize="9" textAnchor="middle">VISIBLE T</text>
        </g>
      </svg>
    </div>
  );
}
export function PerformanceChart() {
  const strategy = [0, 3, 2, 7, 10, 9, 15, 18, 17, 23, 27, 31, 29, 36, 39, 43, 47, 45, 51, 56, 59, 64, 68, 72];
  const benchmark = [0, 1, 0, 2, 4, 3, 6, 8, 7, 9, 12, 11, 13, 16, 15, 19, 21, 20, 24, 27, 26, 29, 31, 32];
  return (
    <div className="chart-shell">
      <span className="chart-axis-label top">累计收益，%</span>
      <span className="chart-axis-label bottom">2021-01 至 2025-12</span>
      <svg viewBox="0 0 820 260" role="img" aria-labelledby="performance-title performance-desc">
        <title id="performance-title">因子组合与基准累计收益</title>
        <desc id="performance-desc">示例因子组合累计收益约 72%，同期基准约 32%。</desc>
        <path d={linePath(benchmark, 820, 260, 28)} fill="none" stroke="#728198" strokeWidth="2" />
        <path d={linePath(strategy, 820, 260, 28)} fill="none" stroke="#52c7d9" strokeWidth="2.5" />
        <g fontFamily="Segoe UI, sans-serif" fontSize="10">
          <text x="675" y="45" fill="#52c7d9">因子组合</text>
          <text x="675" y="63" fill="#afbdcb">中证全指</text>
        </g>
      </svg>
    </div>
  );
}
