"use server"

import {
    fetchPollutionData as fetchPolData,
    fetchMonthlyData as fetchMonData,
    fetchMonthlyDataForYear as fetchMonDataYear,
    fetchStates as fetchSt,
    getAvailableYears as getYears,
    checkBackendHealth,
    type MetricType
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
