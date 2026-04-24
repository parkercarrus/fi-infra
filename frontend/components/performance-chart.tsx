"use client";

import { useDeferredValue, useState } from "react";

import {
  formatCurrency,
  formatDate,
  formatPercent,
  formatSignedCurrency,
  formatSignedPercent,
} from "@/lib/format";
import { CurvePoint } from "@/lib/types";

type PerformanceChartProps = {
  points: CurvePoint[];
  title: string;
  mode?: "portfolio_value" | "drawdown";
};

const RANGE_OPTIONS = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
  { label: "ALL", days: null },
];

function filterPoints(points: CurvePoint[], rangeLabel: string) {
  const selectedRange = RANGE_OPTIONS.find((option) => option.label === rangeLabel);
  if (!selectedRange || selectedRange.days === null || points.length === 0) {
    return points;
  }

  const latestDate = new Date(points[points.length - 1].date);
  const threshold = new Date(latestDate);
  threshold.setDate(latestDate.getDate() - selectedRange.days);

  const filtered = points.filter((point) => new Date(point.date) >= threshold);
  return filtered.length > 1 ? filtered : points;
}

function metricValue(point: CurvePoint, mode: "portfolio_value" | "drawdown") {
  return mode === "drawdown" ? point.drawdown : point.portfolio_value;
}

function buildPath(points: CurvePoint[], mode: "portfolio_value" | "drawdown", width: number, height: number) {
  const paddingLeft = 28;
  const paddingRight = 24;
  const paddingTop = 20;
  const paddingBottom = 30;
  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;
  const values = points.map((point) => metricValue(point, mode));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const span = maxValue - minValue || 1;

  const coordinates = points.map((point, index) => {
    const x =
      paddingLeft +
      (points.length === 1 ? 0 : (index / (points.length - 1)) * chartWidth);
    const value = metricValue(point, mode);
    const normalized = (value - minValue) / span;
    const y = paddingTop + chartHeight - normalized * chartHeight;
    return { x, y };
  });

  const linePath = coordinates
    .map((coordinate, index) =>
      `${index === 0 ? "M" : "L"} ${coordinate.x.toFixed(2)} ${coordinate.y.toFixed(2)}`,
    )
    .join(" ");

  const areaPath = `${linePath} L ${coordinates[coordinates.length - 1].x.toFixed(2)} ${(height - paddingBottom).toFixed(2)} L ${coordinates[0].x.toFixed(2)} ${(height - paddingBottom).toFixed(2)} Z`;

  return {
    areaPath,
    linePath,
    minValue,
    maxValue,
    gridValues: [0, 0.33, 0.66, 1].map((value) => minValue + span * value),
    paddingLeft,
    paddingRight,
    paddingTop,
    paddingBottom,
    chartHeight,
    chartWidth,
    coordinates,
  };
}

export function PerformanceChart({
  points,
  title,
  mode = "portfolio_value",
}: PerformanceChartProps) {
  const [selectedRange, setSelectedRange] = useState("ALL");
  const deferredRange = useDeferredValue(selectedRange);
  const filteredPoints = filterPoints(points, deferredRange);
  if (filteredPoints.length === 0) {
    return (
      <section className="rounded-[2.2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-[var(--broker-text-muted)]">
          {title}
        </p>
        <div className="mt-6 rounded-[1.5rem] border border-dashed border-white/10 bg-white/[0.02] px-4 py-12 text-center text-sm uppercase tracking-[0.2em] text-[var(--broker-text-muted)]">
          Portfolio history unavailable
        </div>
      </section>
    );
  }
  const latestPoint = filteredPoints[filteredPoints.length - 1];
  const firstPoint = filteredPoints[0];
  const deltaValue =
    mode === "drawdown"
      ? latestPoint?.drawdown ?? 0
      : (latestPoint?.portfolio_value ?? 0) - (firstPoint?.portfolio_value ?? 0);
  const deltaPercent =
    mode === "drawdown" || !firstPoint?.portfolio_value
      ? latestPoint?.drawdown ?? 0
      : deltaValue / firstPoint.portfolio_value;

  const svgWidth = Math.max(960, filteredPoints.length * 12);
  const svgHeight = 360;
  const {
    areaPath,
    linePath,
    gridValues,
    paddingLeft,
    paddingRight,
    paddingTop,
    chartHeight,
  } = buildPath(filteredPoints, mode, svgWidth, svgHeight);

  return (
    <section className="rounded-[2.2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
      <div className="flex flex-col gap-4 border-b border-white/6 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-[var(--broker-text-muted)]">
            {title}
          </p>
          <div className="mt-3 flex flex-wrap items-end gap-4">
            <p className="text-4xl font-semibold tracking-[-0.08em] text-white">
              {mode === "drawdown"
                ? formatSignedPercent(latestPoint?.drawdown ?? 0)
                : formatCurrency(latestPoint?.portfolio_value ?? 0, true)}
            </p>
            <p
              className={`pb-1 text-sm font-medium ${
                deltaValue >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {mode === "drawdown"
                ? formatSignedPercent(deltaValue)
                : `${formatSignedCurrency(deltaValue)} · ${formatSignedPercent(deltaPercent)}`}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {RANGE_OPTIONS.map((option) => (
            <button
              key={option.label}
              type="button"
              onClick={() => setSelectedRange(option.label)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold tracking-[0.18em] transition ${
                deferredRange === option.label
                  ? "bg-[var(--broker-accent)] text-[var(--broker-bg)]"
                  : "bg-white/6 text-[var(--broker-text-muted)] hover:bg-white/10 hover:text-white"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-5 overflow-x-auto">
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="min-w-full"
        >
          <defs>
            <linearGradient id={`fill-${mode}`} x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor={mode === "drawdown" ? "rgba(244,63,94,0.32)" : "rgba(34,211,238,0.34)"}
              />
              <stop
                offset="100%"
                stopColor={mode === "drawdown" ? "rgba(244,63,94,0.02)" : "rgba(34,211,238,0.02)"}
              />
            </linearGradient>
          </defs>

          {gridValues.map((value) => {
            const normalized =
              (value - gridValues[0]) / ((gridValues[gridValues.length - 1] - gridValues[0]) || 1);
            const y = paddingTop + chartHeight - normalized * chartHeight;

            return (
              <g key={value}>
                <line
                  x1={paddingLeft}
                  x2={svgWidth - paddingRight}
                  y1={y}
                  y2={y}
                  stroke="rgba(255,255,255,0.08)"
                  strokeDasharray="4 6"
                />
                <text
                  x={paddingLeft}
                  y={y - 8}
                  fill="rgba(148,163,184,0.8)"
                  fontSize="11"
                >
                  {mode === "drawdown" ? formatPercent(value) : formatCurrency(value, true)}
                </text>
              </g>
            );
          })}

          <path d={areaPath} fill={`url(#fill-${mode})`} />
          <path
            d={linePath}
            fill="none"
            stroke={mode === "drawdown" ? "#fb7185" : "#22d3ee"}
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-[var(--broker-text-muted)]">
        <span>{formatDate(firstPoint?.date ?? null)}</span>
        <span>{formatDate(latestPoint?.date ?? null)}</span>
      </div>
    </section>
  );
}
