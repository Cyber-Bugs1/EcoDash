"use server"

import {
    fetchPollutionData as fetchPolData,
    fetchMonthlyData as fetchMonData,
    fetchMonthlyDataForYear as fetchMonDataYear,
    fetchMetricDetail as fetchMetricDet,
    fetchStates as fetchSt,
    getAvailableYears as getYears,
    checkBackendHealth,
    fetchStateSummary as fetchSummary,
    type MetricType,
    type StateSummaryResponse,
    type TrendData,
    type MetricDetailResponse
} from "./data-service";

export async function checkBackendHealthAction() {
    return await checkBackendHealth();
}

export async function fetchStatesAction() {
    return await fetchSt();
}

export async function fetchPollutionDataAction(state: string) {
    return await fetchPolData(state);
}

// NEW: Fetch state summary using new API format
export async function fetchStateSummaryAction(state: string): Promise<StateSummaryResponse | null> {
    return await fetchSummary(state);
}

export async function fetchMonthlyDataAction(
    state: string,
    metric: MetricType
) {
    return await fetchMonData(state, metric);
}

// Optimized: fetch only single year data
export async function fetchMonthlyDataForYearAction(
    state: string,
    metric: MetricType,
    year: number
) {
    return await fetchMonDataYear(state, metric, year);
}

export async function getAvailableYearsAction() {
    return await getYears();
}

// Fetch full metric detail (including annual stats)
export async function fetchMetricDetailAction(
    state: string,
    metric: MetricType,
    year: number
): Promise<MetricDetailResponse | null> {
    return await fetchMetricDet(state, metric, year);
}
