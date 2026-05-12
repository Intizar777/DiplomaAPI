/**
 * Frontend React Examples
 * Common patterns for consuming the Production Analytics API
 */

import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_BASE = 'http://localhost:3000/api/production';

// ============ Utilities ============

const getAuthHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
});

async function apiCall(
  endpoint: string,
  token: string,
  options?: RequestInit
) {
  const response = await fetch(API_BASE + endpoint, {
    headers: getAuthHeaders(token),
    ...options
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============ Custom Hooks ============

/**
 * Hook для загрузки KPI с трендом
 */
function useKPI(fromDate: string, toDate: string, token: string) {
  const [kpi, setKpi] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiCall(
      `/kpi?from_date=${fromDate}&to_date=${toDate}&granularity=day`,
      token
    )
      .then(setKpi)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [fromDate, toDate, token]);

  return { kpi, loading, error };
}

/**
 * Hook для загрузки маржи по продуктам
 */
function useSalesMargin(fromDate: string, toDate: string, token: string) {
  const [margins, setMargins] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiCall(
      `/sales/margin?from_date=${fromDate}&to_date=${toDate}&limit=50`,
      token
    )
      .then(setMargins)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [fromDate, toDate, token]);

  return { margins, loading, error };
}

/**
 * Hook для загрузки простоев
 */
function useDowntime(fromDate: string, toDate: string, token: string) {
  const [downtime, setDowntime] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiCall(
      `/downtime-events/summary?from_date=${fromDate}&to_date=${toDate}`,
      token
    )
      .then(setDowntime)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [fromDate, toDate, token]);

  return { downtime, loading, error };
}

// ============ Components ============

/**
 * KPI Card с цветовой индикацией
 */
function KPICard({
  label,
  value,
  unit = '',
  status,
  target,
  min,
  max
}: {
  label: string;
  value: number | string;
  unit?: string;
  status: 'ok' | 'warning' | 'critical';
  target?: number;
  min?: number;
  max?: number;
}) {
  const statusColors = {
    ok: { bg: '#e8f5e9', border: '#4caf50', text: '#2e7d32' },
    warning: { bg: '#fff3e0', border: '#ff9800', text: '#e65100' },
    critical: { bg: '#ffebee', border: '#f44336', text: '#c62828' }
  };

  const colors = statusColors[status];

  return (
    <div
      style={{
        borderLeft: `4px solid ${colors.border}`,
        backgroundColor: colors.bg,
        padding: '16px',
        borderRadius: '4px',
        flex: 1,
        minWidth: '200px'
      }}
    >
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
        {label}
      </div>
      <div
        style={{
          fontSize: '28px',
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: '8px'
        }}
      >
        {value}
        {unit && <span style={{ fontSize: '16px', marginLeft: '4px' }}>{unit}</span>}
      </div>
      {target && (
        <div style={{ fontSize: '12px', color: '#999' }}>
          Target: {target}
          {min && max && ` (${min}–${max})`}
        </div>
      )}
    </div>
  );
}

/**
 * KPI Dashboard — полный набор метрик
 */
function KPIDashboard({ token }: { token: string }) {
  const [period, setPeriod] = useState({
    fromDate: new Date(new Date().setDate(new Date().getDate() - 30))
      .toISOString()
      .split('T')[0],
    toDate: new Date().toISOString().split('T')[0]
  });

  const { kpi, loading: kpiLoading } = useKPI(
    period.fromDate,
    period.toDate,
    token
  );
  const { downtime, loading: downtimeLoading } = useDowntime(
    period.fromDate,
    period.toDate,
    token
  );

  if (kpiLoading || downtimeLoading) {
    return <div>Загрузка...</div>;
  }

  if (!kpi) {
    return <div>Ошибка загрузки данных</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Аналитика производства</h1>

      {/* Date Range Picker */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <div>
          <label>От:</label>
          <input
            type="date"
            value={period.fromDate}
            onChange={(e) =>
              setPeriod({ ...period, fromDate: e.target.value })
            }
          />
        </div>
        <div>
          <label>До:</label>
          <input
            type="date"
            value={period.toDate}
            onChange={(e) => setPeriod({ ...period, toDate: e.target.value })}
          />
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ marginBottom: '30px' }}>
        <h2>Основные показатели</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <KPICard
            label="OEE (Эффективность)"
            value={(kpi.oee_estimate * 100).toFixed(1)}
            unit="%"
            status={kpi.targets.oee_estimate.status}
            target={(kpi.targets.oee_estimate.target * 100).toFixed(0)}
          />
          <KPICard
            label="Брак"
            value={(kpi.defect_rate * 100).toFixed(2)}
            unit="%"
            status={kpi.targets.defect_rate.status}
            target={(kpi.targets.defect_rate.target * 100).toFixed(2)}
          />
          <KPICard
            label="OTIF"
            value={(kpi.targets.otif_rate.target * 100).toFixed(1)}
            unit="%"
            status={kpi.targets.otif_rate.status}
          />
          <KPICard
            label="Выпуск"
            value={kpi.total_output.toFixed(1)}
            unit="т"
            status="ok"
          />
        </div>
      </div>

      {/* Trend Chart */}
      <div style={{ marginBottom: '30px' }}>
        <h2>Тренд OEE</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={kpi.trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="oee_estimate"
              stroke="#8884d8"
              name="OEE"
            />
            <Line
              type="monotone"
              dataKey="total_output"
              stroke="#82ca9d"
              name="Выпуск (т)"
              yAxisId="right"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Downtime Summary */}
      {downtime && (
        <div style={{ marginBottom: '30px' }}>
          <h2>Распределение простоев</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={downtime.items}
                  dataKey="total_minutes"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ category, total_minutes }) =>
                    `${category}: ${Math.round(total_minutes / 60)}ч`
                  }
                >
                  {downtime.items.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'][index % 5]}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            <div>
              <h3>Сводка</h3>
              <div style={{ padding: '10px' }}>
                <p>
                  <strong>Всего простоев:</strong> {downtime.total_events}
                </p>
                <p>
                  <strong>Общее время:</strong> {Math.round(downtime.total_downtime_minutes / 60)}ч{' '}
                  {downtime.total_downtime_minutes % 60}м
                </p>
                <ul>
                  {downtime.items.map((item: any) => (
                    <li key={item.category}>
                      {translateCategory(item.category)}: {item.count} event
                      (ов) — {Math.round(item.total_minutes / 60)}ч
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Таблица маржинальности
 */
function SalesMarginTable({ token }: { token: string }) {
  const [period, setPeriod] = useState({
    fromDate: new Date(new Date().setDate(new Date().getDate() - 30))
      .toISOString()
      .split('T')[0],
    toDate: new Date().toISOString().split('T')[0]
  });

  const { margins, loading } = useSalesMargin(
    period.fromDate,
    period.toDate,
    token
  );

  if (loading) return <div>Загрузка маржи...</div>;
  if (!margins) return <div>Нет данных</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Маржинальность</h1>

      {/* Date Range */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <div>
          <label>От:</label>
          <input
            type="date"
            value={period.fromDate}
            onChange={(e) =>
              setPeriod({ ...period, fromDate: e.target.value })
            }
          />
        </div>
        <div>
          <label>До:</label>
          <input
            type="date"
            value={period.toDate}
            onChange={(e) => setPeriod({ ...period, toDate: e.target.value })}
          />
        </div>
      </div>

      {/* Aggregated Summary */}
      <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
        <h3>Итого за период</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>Выручка</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
              ₽ {margins.aggregated.total_revenue.toLocaleString()}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>Себестоимость</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
              ₽ {margins.aggregated.total_cost.toLocaleString()}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>Маржа</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
              ₽ {margins.aggregated.total_margin.toLocaleString()}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>Средняя маржа</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4caf50' }}>
              {margins.aggregated.avg_margin_percent.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Products Table */}
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px'
        }}
      >
        <thead>
          <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
            <th style={{ padding: '12px', textAlign: 'left' }}>Продукт</th>
            <th style={{ padding: '12px', textAlign: 'right' }}>Кол-во</th>
            <th style={{ padding: '12px', textAlign: 'right' }}>Выручка</th>
            <th style={{ padding: '12px', textAlign: 'right' }}>Маржа</th>
            <th style={{ padding: '12px', textAlign: 'right' }}>Маржа %</th>
          </tr>
        </thead>
        <tbody>
          {margins.margins.map((item: any) => (
            <tr
              key={item.product_id}
              style={{
                borderBottom: '1px solid #eee',
                backgroundColor: item.margin_percent < 40 ? '#fffacd' : 'white'
              }}
            >
              <td style={{ padding: '12px' }}>
                <strong>{item.product_name}</strong>
                <br />
                <span style={{ fontSize: '12px', color: '#999' }}>
                  {item.product_code}
                </span>
              </td>
              <td style={{ padding: '12px', textAlign: 'right' }}>
                {item.total_quantity}
              </td>
              <td style={{ padding: '12px', textAlign: 'right' }}>
                ₽ {item.total_revenue.toLocaleString()}
              </td>
              <td style={{ padding: '12px', textAlign: 'right' }}>
                ₽ {item.total_margin.toLocaleString()}
              </td>
              <td
                style={{
                  padding: '12px',
                  textAlign: 'right',
                  color: item.margin_percent > 50 ? '#4caf50' : '#ff9800',
                  fontWeight: 'bold'
                }}
              >
                {item.margin_percent.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Карточка эффективности промо-акции
 */
function CampaignEffectiveness({
  campaignId,
  token
}: {
  campaignId: string;
  token: string;
}) {
  const [effectiveness, setEffectiveness] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall(
      `/promo-campaigns/${campaignId}/effectiveness`,
      token
    )
      .then(setEffectiveness)
      .finally(() => setLoading(false));
  }, [campaignId, token]);

  if (loading) return <div>Загрузка...</div>;
  if (!effectiveness) return <div>Нет данных</div>;

  const roiStatus =
    effectiveness.roi_percent >= 100
      ? 'ok'
      : effectiveness.roi_percent >= 50
      ? 'warning'
      : 'critical';

  return (
    <div
      style={{
        padding: '16px',
        border: '1px solid #ddd',
        borderRadius: '4px',
        maxWidth: '400px'
      }}
    >
      <h3>{effectiveness.campaign_name}</h3>

      <div
        style={{
          marginBottom: '16px',
          padding: '12px',
          backgroundColor:
            roiStatus === 'ok'
              ? '#e8f5e9'
              : roiStatus === 'warning'
              ? '#fff3e0'
              : '#ffebee',
          borderRadius: '4px',
          textAlign: 'center'
        }}
      >
        <div style={{ fontSize: '12px', color: '#666' }}>ROI</div>
        <div
          style={{
            fontSize: '32px',
            fontWeight: 'bold',
            color:
              roiStatus === 'ok'
                ? '#4caf50'
                : roiStatus === 'warning'
                ? '#ff9800'
                : '#f44336'
          }}
        >
          {effectiveness.roi_percent.toFixed(0)}%
        </div>
      </div>

      <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
        <div>
          <span style={{ color: '#666' }}>Бюджет:</span>
          <span style={{ fontWeight: 'bold', float: 'right' }}>
            ₽ {effectiveness.budget.toLocaleString()}
          </span>
        </div>
        <div>
          <span style={{ color: '#666' }}>Базовые продажи:</span>
          <span style={{ fontWeight: 'bold', float: 'right' }}>
            ₽ {effectiveness.baseline_sales.toLocaleString()}
          </span>
        </div>
        <div>
          <span style={{ color: '#666' }}>Продажи в период:</span>
          <span style={{ fontWeight: 'bold', float: 'right' }}>
            ₽ {effectiveness.sales_during_campaign.toLocaleString()}
          </span>
        </div>
        <div style={{ borderTop: '1px solid #ddd', paddingTop: '8px', marginTop: '8px' }}>
          <span style={{ color: '#4caf50', fontWeight: 'bold' }}>Uplift:</span>
          <span style={{ fontWeight: 'bold', float: 'right', color: '#4caf50' }}>
            ₽ {effectiveness.uplift.toLocaleString()}
          </span>
        </div>
        <div>
          <span style={{ color: '#999' }}>Cost/Uplift unit:</span>
          <span style={{ fontWeight: 'bold', float: 'right' }}>
            ₽ {effectiveness.cost_per_uplift_unit.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}

// ============ Utilities ============

function translateCategory(category: string): string {
  const map: Record<string, string> = {
    UNPLANNED_BREAKDOWN: 'Аварийный отказ',
    PLANNED_MAINTENANCE: 'Плановое ТО',
    QUALITY_ISSUE: 'Проблемы качества',
    MATERIAL_SHORTAGE: 'Нехватка материала',
    OTHER: 'Прочее'
  };
  return map[category] || category;
}

// ============ Exports ============

export {
  useKPI,
  useSalesMargin,
  useDowntime,
  KPICard,
  KPIDashboard,
  SalesMarginTable,
  CampaignEffectiveness,
  apiCall
};
