import React, { useEffect, useState } from 'react';

interface SkinMetricData {
  key: string;
  display_name: string;
  percentage: number;
  level: string;
  interpretation: string;
  reference_note: string;
}

interface SkinMetricsPanelProps {
  metrics: SkinMetricData[];
}

// Inverted metrics: lower is better
const INVERTED_METRICS = new Set(['erythema', 'texture', 'oiliness']);

function getBarColor(level: string, key: string): string {
  const isInverted = INVERTED_METRICS.has(key);

  switch (level) {
    case 'low':
      return isInverted ? '#22c55e' : '#ef4444'; // green if inverted (low = good), red otherwise
    case 'normal':
      return '#6C63FF'; // brand purple
    case 'elevated':
      return '#f59e0b'; // amber
    case 'high':
      return isInverted ? '#ef4444' : '#22c55e'; // red if inverted (high = bad), green otherwise
    default:
      return '#6C63FF';
  }
}

const SkinMetricsPanel: React.FC<SkinMetricsPanelProps> = ({ metrics }) => {
  const [animatedWidths, setAnimatedWidths] = useState<Record<string, number>>({});

  useEffect(() => {
    // Animate bars from 0 to target width on mount
    const timer = setTimeout(() => {
      const widths: Record<string, number> = {};
      metrics.forEach(m => { widths[m.key] = m.percentage; });
      setAnimatedWidths(widths);
    }, 100);
    return () => clearTimeout(timer);
  }, [metrics]);

  return (
    <div
      style={{
        background: 'rgba(26,26,46,0.8)',
        border: '1px solid rgba(255,255,255,0.1)',
        backdropFilter: 'blur(12px)',
        borderRadius: '20px',
        padding: '28px 24px',
      }}
      id="skin-metrics-panel"
    >
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{
          color: 'white',
          fontSize: '1.1rem',
          fontWeight: 700,
          marginBottom: '4px',
        }}>
          📊 Skin Analysis Metrics
        </h3>
        <p style={{
          color: 'rgba(255,255,255,0.4)',
          fontSize: '0.8rem',
          lineHeight: 1.5,
        }}>
          Based on image analysis — not a clinical measurement
        </p>
      </div>

      {/* Metrics */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {metrics.map((metric) => {
          const barColor = getBarColor(metric.level, metric.key);
          const width = animatedWidths[metric.key] ?? 0;

          return (
            <div key={metric.key}>
              {/* Label + percentage row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '6px',
              }}>
                <span style={{
                  color: 'white',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                }}>
                  {metric.display_name}
                </span>
                <span style={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  minWidth: '40px',
                  textAlign: 'right',
                }}>
                  {metric.percentage}%
                </span>
              </div>

              {/* Progress bar */}
              <div style={{
                width: '100%',
                height: '8px',
                borderRadius: '999px',
                background: 'rgba(255,255,255,0.08)',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  borderRadius: '999px',
                  background: barColor,
                  width: `${width}%`,
                  transition: 'width 700ms cubic-bezier(0.4,0,0.2,1)',
                }} />
              </div>

              {/* Interpretation */}
              <p style={{
                color: 'rgba(255,255,255,0.45)',
                fontSize: '0.78rem',
                marginTop: '5px',
                lineHeight: 1.4,
              }}>
                {metric.interpretation}
              </p>
            </div>
          );
        })}
      </div>

      {/* Disclaimer */}
      <p style={{
        color: 'rgba(255,255,255,0.3)',
        fontSize: '0.72rem',
        marginTop: '20px',
        lineHeight: 1.6,
        borderTop: '1px solid rgba(255,255,255,0.06)',
        paddingTop: '14px',
      }}>
        These metrics are estimated from photo analysis only. They are not clinical measurements.
      </p>
    </div>
  );
};

export default SkinMetricsPanel;
