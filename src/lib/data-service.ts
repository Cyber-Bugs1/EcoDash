// API-based data service
// Uses the external API instead of local SQLite database

import { logApiCall, API_LOGGING_ENABLED } from './api-logger';

// Get API URL
function getApiBaseUrl(): string {
    return process.env.NEXT_PUBLIC_API_URL || 'http://192.168.29.212:5000';
}

export interface MonthlyData {
    month: string;
    value: number;
}

export interface MetricMonthlyData {
    year: number;
    months: MonthlyData[];
}

export interface PollutionData {
    year: number;
    pm25: number;
    aod: number;
}

export interface HealthStatus {
    online: boolean;
    message: string;
}

// Metric types supported by the API
export type MetricType = 'pm25' | 'aod' | 'vegetation' | 'crop_yield' | 'water_levels';

// Map our metric keys to API type parameters
const METRIC_TO_API_TYPE: Record<MetricType, string> = {
    pm25: 'pm2.5',
    aod: 'pm2.5', // AOD comes from same endpoint
    vegetation: 'vegetation',
    crop_yield: 'crop_yield',
    water_levels: 'water_levels',
};

const MONTHS = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

// List of Indian states for the dropdown
const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
    'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
    'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan',
    'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
    'Uttarakhand', 'West Bengal'
];

// Check if backend is online
export async function checkBackendHealth(): Promise<HealthStatus> {
    try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(baseUrl, {
            method: 'GET',
            cache: 'no-store',
            signal: AbortSignal.timeout(5000),
        });

        if (response.ok) {
            const data = await response.json();
            return {
                online: true,
                message: data.message || 'Backend is online'
            };
        }
        return {
            online: false,
            message: `Backend returned status ${response.status}`
        };
    } catch {
        return {
            online: false,
            message: `Backend server is not reachable`
        };
    }
}

// Helper to make API calls with query parameters and logging
async function apiCall(endpoint: string, params: Record<string, unknown>): Promise<any> {
    const baseUrl = getApiBaseUrl();
    const queryString = new URLSearchParams(
        Object.entries(params)
            .filter(([, v]) => v !== undefined && v !== null)
            .map(([k, v]) => [k, String(v)])
    ).toString();

    const url = `${baseUrl}${endpoint}?${queryString}`;
    const startTime = Date.now();

    try {
        const response = await fetch(url, {
            method: 'GET',
            cache: 'no-store',
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        const duration = Date.now() - startTime;

        // Log successful call
        logApiCall({
            method: 'GET',
            url,
            request: params,
            response: data,
            duration,
        });

        return data;
    } catch (error) {
        const duration = Date.now() - startTime;

        // Log failed call
        logApiCall({
            method: 'GET',
            url,
            request: params,
            error: error instanceof Error ? error.message : String(error),
            duration,
        });

        throw error;
    }
}

export async function fetchStates(): Promise<string[]> {
    return INDIAN_STATES;
}

export async function fetchPollutionData(state: string = 'Delhi'): Promise<PollutionData[]> {
    try {
        // Use compare endpoint - returns { comparison: [{pm25, year, source}, ...] }
        const response = await apiCall('/api/compare', {
            state,
            start_year: 2020,
            end_year: 2026,
        });

        if (response && response.comparison && Array.isArray(response.comparison)) {
            return response.comparison.map((item: any) => ({
                year: item.year,
                pm25: parseFloat((item.pm25 || 0).toFixed(1)),
                aod: 0, // API doesn't return AOD in compare endpoint
            }));
        }

        return [];
    } catch (error) {
        console.error("API Error fetching pollution data:", error);
        return [];
    }
}

// Fetch monthly data for a SINGLE year only (optimized)
export async function fetchMonthlyDataForYear(
    state: string,
    metric: MetricType,
    year: number
): Promise<MonthlyData[]> {
    try {
        const apiType = METRIC_TO_API_TYPE[metric];

        // Create requests for all 12 months at once
        const monthRequests = Array.from({ length: 12 }, (_, i) =>
            apiCall('/api/data', {
                type: apiType,
                state,
                month: i + 1,
                year,
            }).catch(() => null)
        );

        const monthResponses = await Promise.all(monthRequests);
        const months: MonthlyData[] = [];

        monthResponses.forEach((response, index) => {
            if (response) {
                let value = response.value || 0;

                // For AOD, try to get aod field specifically
                if (metric === 'aod' && response.aod !== undefined) {
                    value = response.aod;
                }

                months.push({
                    month: MONTHS[index],
                    value: parseFloat(Number(value).toFixed(2)),
                });
            }
        });

        return months;
    } catch (error) {
        console.error("API Error fetching monthly data for year:", error);
        return [];
    }
}

// Fetch monthly data for multiple years (used for year comparison chart)
export async function fetchMonthlyData(state: string, metric: MetricType): Promise<MetricMonthlyData[]> {
    try {
        const currentYear = new Date().getFullYear();
        const years = [currentYear - 2, currentYear - 1, currentYear];
        const results: MetricMonthlyData[] = [];

        // Fetch all years in parallel
        const yearPromises = years.map(async (year) => {
            const months = await fetchMonthlyDataForYear(state, metric, year);
            if (months.length > 0) {
                return { year, months };
            }
            return null;
        });

        const yearResults = await Promise.all(yearPromises);

        for (const result of yearResults) {
            if (result) {
                results.push(result);
            }
        }

        return results;
    } catch (error) {
        console.error("API Error fetching monthly data:", error);
        return [];
    }
}

export async function getAvailableYears(): Promise<number[]> {
    const currentYear = new Date().getFullYear();
    return [currentYear, currentYear - 1, currentYear - 2];
}

