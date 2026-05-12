/**
 * TypeScript Types for Production Analytics API
 * Auto-generated from API schemas
 */

// ============ Common Types ============

export interface ApiError {
  detail: string;
  status: number;
}

// ============ KPI Types ============

export interface KPITarget {
  target: number;
  min: number;
  max: number;
  status: 'ok' | 'warning' | 'critical';
}

export interface KPITargets {
  oee_estimate?: KPITarget;
  defect_rate?: KPITarget;
  otif_rate?: KPITarget;
}

export interface KPITrendPoint {
  period: string; // YYYY-MM-DD
  total_output: number;
  defect_rate: number;
  oee_estimate?: number;
}

export interface KPIResponse {
  total_output: number;
  defect_rate: number;
  completed_orders: number;
  total_orders: number;
  availability: number;
  performance: number;
  oee_estimate: number;
  line_throughput: number;
  targets: KPITargets;
  trend: KPITrendPoint[];
  change_percent?: Record<string, number>;
}

// ============ OTIF Types ============

export interface OTIFResponse {
  otif_rate: number;
  on_time_orders: number;
  in_full_quantity_orders: number;
  otif_orders: number;
  total_orders: number;
}

// ============ KPI Breakdown Types ============

export interface KPIBreakdownItem {
  group_key: string;
  value: number;
  target?: number;
  status: 'ok' | 'warning' | 'critical';
  deviation?: number;
}

export interface KPIBreakdownResponse {
  items: KPIBreakdownItem[];
  total: number;
}

// ============ Sales Types ============

export interface SalesMarginItem {
  product_id: string;
  product_code: string;
  product_name: string;
  total_quantity: number;
  total_revenue: number;
  total_cost: number;
  total_margin: number;
  margin_percent: number;
  margin_per_unit: number;
}

export interface SalesMarginAggregated {
  total_revenue: number;
  total_cost: number;
  total_margin: number;
  avg_margin_percent: number;
}

export interface SalesMarginResponse {
  margins: SalesMarginItem[];
  total: number;
  aggregated: SalesMarginAggregated;
}

// ============ Batch Input Types ============

export interface BatchInputCreate {
  order_id?: string;
  product_id?: string;
  quantity: number;
  input_date: string; // ISO 8601 datetime
}

export interface BatchInputResponse {
  id: string;
  order_id?: string;
  product_id?: string;
  quantity: number;
  input_date: string;
  created_at: string;
  updated_at: string;
}

export interface BatchInputListResponse {
  items: BatchInputResponse[];
  total: number;
}

export interface YieldResponse {
  order_id: string;
  total_input: number;
  total_output: number;
  yield_percent: number;
  target: number;
}

// ============ Downtime Types ============

export type DowntimeCategory =
  | 'PLANNED_MAINTENANCE'
  | 'UNPLANNED_BREAKDOWN'
  | 'QUALITY_ISSUE'
  | 'MATERIAL_SHORTAGE'
  | 'OTHER';

export interface DowntimeEventCreate {
  production_line_id?: string;
  reason: string;
  category: DowntimeCategory;
  started_at: string; // ISO 8601 datetime
  ended_at?: string;
  duration_minutes?: number;
}

export interface DowntimeEventResponse {
  id: string;
  production_line_id?: string;
  reason: string;
  category: DowntimeCategory;
  started_at: string;
  ended_at?: string;
  duration_minutes?: number;
  created_at: string;
  updated_at: string;
}

export interface DowntimeEventListResponse {
  items: DowntimeEventResponse[];
  total: number;
}

export interface DowntimeSummaryItem {
  category: DowntimeCategory;
  total_minutes: number;
  count: number;
}

export interface DowntimeSummaryResponse {
  items: DowntimeSummaryItem[];
  total_events: number;
  total_downtime_minutes: number;
}

// ============ Promo Campaign Types ============

export type SalesChannel = 'DIRECT' | 'DISTRIBUTOR' | 'RETAIL' | 'ONLINE';

export interface PromoCampaignCreate {
  name: string;
  description?: string;
  channel: SalesChannel;
  product_id?: string;
  discount_percent?: number;
  start_date: string; // YYYY-MM-DD
  end_date?: string;
  budget?: number;
}

export interface PromoCampaignResponse {
  id: string;
  name: string;
  description?: string;
  channel: SalesChannel;
  product_id?: string;
  discount_percent?: number;
  start_date: string;
  end_date?: string;
  budget?: number;
  created_at: string;
  updated_at: string;
}

export interface PromoCampaignListResponse {
  items: PromoCampaignResponse[];
  total: number;
}

export interface PromoCampaignEffectivenessResponse {
  campaign_id: string;
  campaign_name: string;
  budget?: number;
  sales_during_campaign: number;
  baseline_sales: number;
  uplift: number;
  cost_per_uplift_unit?: number;
  roi: number;
  roi_percent: number;
}

// ============ Production Line Types ============

export interface ProductionLineResponse {
  id: string;
  code: string;
  name: string;
  description?: string;
  division?: string;
  is_active: boolean;
}

export interface ProductionLinesListResponse {
  production_lines: ProductionLineResponse[];
  total: number;
}

// ============ Phase 2 Types ============

export interface LineProductivityItem {
  production_line: string;
  productivity: number;
  total_output: number;
  days: number;
  target: number;
  status: 'ok' | 'warning' | 'critical';
  deviation: number;
}

export interface LineProductivityResponse {
  items: LineProductivityItem[];
  period: {
    from: string;
    to: string;
  };
  unit: string;
}

export interface ScrapPercentageResponse {
  scrap_percentage: number;
  rejected_tests: number;
  total_tests: number;
  target: number;
  status: 'ok' | 'warning' | 'critical';
  period: {
    from: string;
    to: string;
  };
}

// ============ API Service Class ============

export class ProductionAnalyticsAPI {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string = 'http://localhost:3000/api/production', token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(this.baseUrl + endpoint, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...(options?.headers as Record<string, string>)
      },
      ...options
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ========== KPI ==========

  async getKPI(
    fromDate: string,
    toDate: string,
    productionLineId?: string,
    granularity: 'day' | 'week' | 'month' = 'day',
    compareWithPrevious: boolean = false
  ): Promise<KPIResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate,
      granularity,
      compare_with_previous: compareWithPrevious.toString()
    });

    if (productionLineId) {
      params.append('production_line_id', productionLineId);
    }

    return this.request<KPIResponse>(`/kpi?${params}`);
  }

  async getOTIF(
    fromDate: string,
    toDate: string,
    productionLineId?: string
  ): Promise<OTIFResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate
    });

    if (productionLineId) {
      params.append('production_line_id', productionLineId);
    }

    return this.request<OTIFResponse>(`/kpi/otif?${params}`);
  }

  async getKPIBreakdown(
    fromDate: string,
    toDate: string,
    groupBy: 'productionLine' | 'product' | 'division' = 'productionLine',
    metric: 'oeeEstimate' | 'defectRate' | 'lineThroughput' | 'otifRate' = 'oeeEstimate',
    offset: number = 0,
    limit: number = 20
  ): Promise<KPIBreakdownResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate,
      group_by: groupBy,
      metric,
      offset: offset.toString(),
      limit: limit.toString()
    });

    return this.request<KPIBreakdownResponse>(`/kpi/breakdown?${params}`);
  }

  async getLineProductivity(
    fromDate: string,
    toDate: string,
    productionLineId?: string
  ): Promise<LineProductivityResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate
    });

    if (productionLineId) {
      params.append('production_line_id', productionLineId);
    }

    return this.request<LineProductivityResponse>(`/kpi/line-productivity?${params}`);
  }

  async getScrapPercentage(
    fromDate: string,
    toDate: string,
    productId?: string
  ): Promise<ScrapPercentageResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate
    });

    if (productId) {
      params.append('product_id', productId);
    }

    return this.request<ScrapPercentageResponse>(`/kpi/scrap-percentage?${params}`);
  }

  // ========== Sales ==========

  async getSalesMargin(
    fromDate: string,
    toDate: string,
    productId?: string,
    offset: number = 0,
    limit: number = 20
  ): Promise<SalesMarginResponse> {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate,
      offset: offset.toString(),
      limit: limit.toString()
    });

    if (productId) {
      params.append('product_id', productId);
    }

    return this.request<SalesMarginResponse>(`/sales/margin?${params}`);
  }

  // ========== Batch Inputs ==========

  async createBatchInput(payload: BatchInputCreate): Promise<BatchInputResponse> {
    return this.request<BatchInputResponse>('/batch-inputs', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async listBatchInputs(
    orderId?: string,
    productId?: string,
    offset: number = 0,
    limit: number = 20
  ): Promise<BatchInputListResponse> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString()
    });

    if (orderId) params.append('order_id', orderId);
    if (productId) params.append('product_id', productId);

    return this.request<BatchInputListResponse>(`/batch-inputs?${params}`);
  }

  async getYield(orderId: string): Promise<YieldResponse> {
    return this.request<YieldResponse>(`/batch-inputs/yield?order_id=${orderId}`);
  }

  // ========== Downtime Events ==========

  async createDowntimeEvent(payload: DowntimeEventCreate): Promise<DowntimeEventResponse> {
    return this.request<DowntimeEventResponse>('/downtime-events', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async listDowntimeEvents(
    fromDate?: string,
    toDate?: string,
    productionLineId?: string,
    category?: DowntimeCategory,
    offset: number = 0,
    limit: number = 20
  ): Promise<DowntimeEventListResponse> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString()
    });

    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (productionLineId) params.append('production_line_id', productionLineId);
    if (category) params.append('category', category);

    return this.request<DowntimeEventListResponse>(`/downtime-events?${params}`);
  }

  async getDowntimeSummary(
    fromDate?: string,
    toDate?: string
  ): Promise<DowntimeSummaryResponse> {
    const params = new URLSearchParams();

    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    return this.request<DowntimeSummaryResponse>(`/downtime-events/summary?${params}`);
  }

  // ========== Promo Campaigns ==========

  async createPromoCampaign(payload: PromoCampaignCreate): Promise<PromoCampaignResponse> {
    return this.request<PromoCampaignResponse>('/promo-campaigns', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async listPromoCampaigns(
    fromDate?: string,
    toDate?: string,
    channel?: SalesChannel,
    offset: number = 0,
    limit: number = 20
  ): Promise<PromoCampaignListResponse> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString()
    });

    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (channel) params.append('channel', channel);

    return this.request<PromoCampaignListResponse>(`/promo-campaigns?${params}`);
  }

  async getCampaignEffectiveness(
    campaignId: string
  ): Promise<PromoCampaignEffectivenessResponse> {
    return this.request<PromoCampaignEffectivenessResponse>(
      `/promo-campaigns/${campaignId}/effectiveness`
    );
  }

  // ========== Reference Data ==========

  async listProductionLines(
    division?: string,
    offset: number = 0,
    limit: number = 20
  ): Promise<ProductionLinesListResponse> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString()
    });

    if (division) params.append('division', division);

    return this.request<ProductionLinesListResponse>(`/production-lines?${params}`);
  }
}

// ============ Utility Functions ============

/**
 * Format number to Russian currency
 */
export function formatRuble(value: number): string {
  return `₽ ${value.toLocaleString('ru-RU')}`;
}

/**
 * Format percentage
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format hours and minutes
 */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}ч ${mins}м`;
}

/**
 * Translate downtime category
 */
export function translateDowntimeCategory(category: DowntimeCategory): string {
  const map: Record<DowntimeCategory, string> = {
    UNPLANNED_BREAKDOWN: 'Аварийный отказ',
    PLANNED_MAINTENANCE: 'Плановое ТО',
    QUALITY_ISSUE: 'Проблемы качества',
    MATERIAL_SHORTAGE: 'Нехватка материала',
    OTHER: 'Прочее'
  };
  return map[category];
}

/**
 * Translate sales channel
 */
export function translateSalesChannel(channel: SalesChannel): string {
  const map: Record<SalesChannel, string> = {
    DIRECT: 'Прямые продажи',
    DISTRIBUTOR: 'Дистрибьюторы',
    RETAIL: 'Розница',
    ONLINE: 'Онлайн'
  };
  return map[channel];
}

/**
 * Get status color for traffic light
 */
export function getStatusColor(status: 'ok' | 'warning' | 'critical'): string {
  const colors = {
    ok: '#4caf50',
    warning: '#ff9800',
    critical: '#f44336'
  };
  return colors[status];
}

/**
 * Get status background color for traffic light
 */
export function getStatusBackgroundColor(status: 'ok' | 'warning' | 'critical'): string {
  const colors = {
    ok: '#e8f5e9',
    warning: '#fff3e0',
    critical: '#ffebee'
  };
  return colors[status];
}
