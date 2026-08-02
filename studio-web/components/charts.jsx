"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramSeries,
  LineSeries,
} from "lightweight-charts";
import { candles, factorSignal } from "@/lib/data";

const START_TIME = Date.parse("2024-02-23T09:30:00+08:00") / 1000;
const EMPTY_EVENTS = [];
const timeFormatter = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function formatChartTime(time) {
  return timeFormatter.format(new Date(Number(time) * 1000));
}

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

function chartData(cursorRatio) {
  const visibleCount = Math.max(2, Math.round(2 + cursorRatio * (candles.length - 2)));
  const times = candles.map((_, index) => START_TIME + index * 300);
  return {
    times,
    visibleCount,
    candles: candles.slice(0, visibleCount).map(([open, high, low, close], index) => ({
      time: times[index],
      open,
      high,
      low,
      close,
    })),
    volume: candles.slice(0, visibleCount).map(([open, high, low, close], index) => ({
      time: times[index],
      value: 46 + ((high - low) * 7) + ((index * 17) % 31),
      color: close >= open ? "rgba(82, 199, 217, 0.48)" : "rgba(114, 129, 152, 0.45)",
    })),
    signal: factorSignal.slice(0, visibleCount).map((value, index) => ({ time: times[index], value })),
  };
}

function nearestTime(timestamp, times, visibleCount) {
  const available = times.slice(0, visibleCount);
  return available.reduce((best, time) => (
    Math.abs(time - timestamp) < Math.abs(best - timestamp) ? time : best
  ), available[0]);
}

export function EvidenceChart({ cursorRatio = 0.55, compact = false, events = EMPTY_EVENTS }) {
  const containerRef = useRef(null);
  const data = useMemo(() => chartData(cursorRatio), [cursorRatio]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const height = compact ? 260 : 360;
    const chart = createChart(container, {
      width: container.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0d151d" },
        textColor: "#8795a8",
        attributionLogo: true,
        panes: {
          separatorColor: "#273544",
          separatorHoverColor: "#52c7d9",
          enableResize: true,
        },
      },
      grid: {
        vertLines: { color: "#1b2732" },
        horzLines: { color: "#1b2732" },
      },
      crosshair: {
        vertLine: { color: "#52c7d9", labelBackgroundColor: "#16333f" },
        horzLine: { color: "#526172", labelBackgroundColor: "#273544" },
      },
      rightPriceScale: { borderColor: "#273544" },
      localization: { timeFormatter: formatChartTime },
      timeScale: {
        borderColor: "#273544",
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: formatChartTime,
      },
      handleScale: compact ? false : undefined,
      handleScroll: compact ? false : undefined,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#5d7f8d",
      downColor: "#4a596c",
      wickUpColor: "#afbdcb",
      wickDownColor: "#728198",
      borderUpColor: "#afbdcb",
      borderDownColor: "#728198",
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceLineVisible: false,
      lastValueVisible: false,
    }, 1);
    const signalSeries = chart.addSeries(LineSeries, {
      color: "#f1b35c",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      title: "Factor signal",
    }, 2);

    candleSeries.setData(data.candles);
    volumeSeries.setData(data.volume);
    signalSeries.setData(data.signal);
    chart.panes()[0]?.setStretchFactor(5);
    chart.panes()[1]?.setStretchFactor(1.35);
    chart.panes()[2]?.setStretchFactor(1.65);

    const eventMarkers = events.map((event, index) => ({
      time: nearestTime(Date.parse(event.availableAt) / 1000, data.times, data.visibleCount),
      position: "aboveBar",
      color: event.evidence === "missing" ? "#d87575" : "#f1b35c",
      shape: index % 2 ? "circle" : "arrowDown",
      text: event.adapter === "A股公告" ? "公告" : event.adapter === "财经新闻" ? "新闻" : "链上",
    }));
    createSeriesMarkers(candleSeries, [
      ...eventMarkers,
      {
        time: data.candles.at(-1).time,
        position: "belowBar",
        color: "#52c7d9",
        shape: "circle",
        text: "VISIBLE T",
      },
    ].sort((a, b) => a.time - b.time));

    chart.timeScale().fitContent();
    const resize = new ResizeObserver(([entry]) => {
      chart.applyOptions({ width: Math.floor(entry.contentRect.width) });
    });
    resize.observe(container);

    return () => {
      resize.disconnect();
      chart.remove();
    };
  }, [compact, data, events]);

  return (
    <div className={`chart-shell lightweight ${compact ? "compact" : ""}`}>
      <div
        ref={containerRef}
        className="lightweight-chart"
        role="img"
        aria-label={`K 线、成交量与因子信号。当前显示 ${data.visibleCount} 根可见 K 线，未来数据不进入图表。`}
      />
      <span className="chart-axis-label top">K 线 / 成交量 / 因子信号</span>
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
