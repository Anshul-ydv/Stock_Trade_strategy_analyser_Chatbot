import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

export const ChartComponent = ({ data, colors = {} }) => {
  const chartContainerRef = useRef();

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: colors.backgroundColor || '#151924' },
        textColor: colors.textColor || '#d1d5db',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#334155',
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      crosshair: {
        mode: 0,
        vertLine: { color: '#6366f1', width: 1, style: 2 },
        horzLine: { color: '#6366f1', width: 1, style: 2 },
      },
    });

    // ── Candlestick series ─────────────────────────────
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });
    candleSeries.setData(data);

    // ── Volume histogram ──────────────────────────────
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    const volumeData = data.map(d => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)',
    }));
    volumeSeries.setData(volumeData);

    // ── EMA 9 overlay ─────────────────────────────────
    const ema9Series = chart.addLineSeries({
      color: '#38bdf8', // Light blue
      lineWidth: 2,
      title: 'EMA 9',
      crosshairMarkerVisible: false,
    });
    const ema9Data = data
      .filter(d => d.ema_9)
      .map(d => ({ time: d.time, value: d.ema_9 }));
    ema9Series.setData(ema9Data);

    // ── EMA 21 overlay ────────────────────────────────
    const emaSeries = chart.addLineSeries({
      color: '#fbbf24',
      lineWidth: 2,
      title: 'EMA 21',
      crosshairMarkerVisible: false,
    });
    const emaData = data
      .filter(d => d.ema_21)
      .map(d => ({ time: d.time, value: d.ema_21 }));
    emaSeries.setData(emaData);

    // ── Support (green dashed) ────────────────────────
    const supportSeries = chart.addLineSeries({
      color: '#4ade80',
      lineWidth: 1,
      lineStyle: 2,
      title: 'Support',
      crosshairMarkerVisible: false,
    });
    const supportData = data
      .filter(d => d.support)
      .map(d => ({ time: d.time, value: d.support }));
    supportSeries.setData(supportData);

    // ── Resistance (red dashed) ───────────────────────
    const resistanceSeries = chart.addLineSeries({
      color: '#f87171',
      lineWidth: 1,
      lineStyle: 2,
      title: 'Resistance',
      crosshairMarkerVisible: false,
    });
    const resistanceData = data
      .filter(d => d.resistance)
      .map(d => ({ time: d.time, value: d.resistance }));
    resistanceSeries.setData(resistanceData);

    chart.timeScale().fitContent();

    // ── Resize handling ───────────────────────────────
    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [data, colors]);

  return (
    <div
      ref={chartContainerRef}
      className="w-full h-full"
    />
  );
};
