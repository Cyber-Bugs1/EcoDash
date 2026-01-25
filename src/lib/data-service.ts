// API-based data service
// Uses the external API instead of local SQLite database

import { logApiCall } from './api-logger';

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

// New API response format
export interface MetricSummary {
    category: string;
    mean_percentage_of_max: number;
    mean_value: number;
    spike_detected_next_10_months: boolean;
}

export interface TrendData {
    aod: number[];
    pm25: number[];
    years: number[];
}

export interface StateSummaryResponse {
    state: string;
    summary: {
        AOD: MetricSummary;
        'Crop Yield (t/ha)': MetricSummary;
        'PM2.5': MetricSummary;
        Vegetation: MetricSummary;
        'Water Level': MetricSummary;
    };
    trend: TrendData;
    year: number;
}

// Metric types supported by the API
export type MetricType = 'pm25' | 'aod' | 'vegetation' | 'crop_yield' | 'water_levels';

// New: API response for specific metric data
export interface MetricDetailResponse {
    annual_max: number;
    annual_mean: number;
    annual_min: number;
    monthly_averages: number[];
    state: string;
    type: string;
    year: string;
}

const MONTHS = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

// List of Indian states for the dropdown (matching API endpoint)
const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir',
    'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Madhya Pradesh', 'Maharashtra',
    'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan',
    'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
    'Uttarakhand', 'West Bengal'
];

// ============================================
// TEST DATA - Used when USE_TEST_DATA is true
// ============================================
const USE_TEST_DATA = false; // Set to false to use real API

const TEST_STATE_SUMMARY: Record<string, StateSummaryResponse> = {
    'Delhi': {
        state: 'Delhi',
        summary: {
            AOD: {
                category: 'Very Hazy',
                mean_percentage_of_max: 103.9,
                mean_value: 1.039,
                spike_detected_next_10_months: true
            },
            'Crop Yield (t/ha)': {
                category: 'Average',
                mean_percentage_of_max: 55.6,
                mean_value: 0.556,
                spike_detected_next_10_months: false
            },
            'PM2.5': {
                category: 'Poor',
                mean_percentage_of_max: 147.7,
                mean_value: 147.742,
                spike_detected_next_10_months: true
            },
            Vegetation: {
                category: 'Poor',
                mean_percentage_of_max: 26.2,
                mean_value: 0.262,
                spike_detected_next_10_months: false
            },
            'Water Level': {
                category: 'Safe',
                mean_percentage_of_max: 25.0,
                mean_value: 0.25,
                spike_detected_next_10_months: false
            }
        },
        trend: {
            aod: [0.895, 1.039, 1.039, 1.039, 1.039],
            pm25: [105.34, 147.74, 147.74, 147.74, 147.74],
            years: [2024, 2025, 2026, 2027, 2028]
        },
        year: 2026
    },
    'Maharashtra': {
        state: 'Maharashtra',
        summary: {
            AOD: {
                category: 'Moderate',
                mean_percentage_of_max: 72.5,
                mean_value: 0.725,
                spike_detected_next_10_months: false
            },
            'Crop Yield (t/ha)': {
                category: 'Good',
                mean_percentage_of_max: 78.3,
                mean_value: 0.783,
                spike_detected_next_10_months: false
            },
            'PM2.5': {
                category: 'Moderate',
                mean_percentage_of_max: 68.4,
                mean_value: 68.4,
                spike_detected_next_10_months: false
            },
            Vegetation: {
                category: 'Good',
                mean_percentage_of_max: 65.8,
                mean_value: 0.658,
                spike_detected_next_10_months: false
            },
            'Water Level': {
                category: 'Moderate Stress',
                mean_percentage_of_max: 45.0,
                mean_value: 0.45,
                spike_detected_next_10_months: true
            }
        },
        trend: {
            aod: [0.68, 0.71, 0.725, 0.73, 0.74],
            pm25: [65.2, 67.0, 68.4, 69.0, 70.2],
            years: [2024, 2025, 2026, 2027, 2028]
        },
        year: 2026
    },
    'Kerala': {
        state: 'Kerala',
        summary: {
            AOD: {
                category: 'Clear',
                mean_percentage_of_max: 32.1,
                mean_value: 0.321,
                spike_detected_next_10_months: false
            },
            'Crop Yield (t/ha)': {
                category: 'Excellent',
                mean_percentage_of_max: 89.2,
                mean_value: 0.892,
                spike_detected_next_10_months: false
            },
            'PM2.5': {
                category: 'Good',
                mean_percentage_of_max: 28.5,
                mean_value: 28.5,
                spike_detected_next_10_months: false
            },
            Vegetation: {
                category: 'Excellent',
                mean_percentage_of_max: 88.7,
                mean_value: 0.887,
                spike_detected_next_10_months: false
            },
            'Water Level': {
                category: 'Safe',
                mean_percentage_of_max: 15.0,
                mean_value: 0.15,
                spike_detected_next_10_months: false
            }
        },
        trend: {
            aod: [0.31, 0.315, 0.321, 0.32, 0.318],
            pm25: [27.0, 27.8, 28.5, 28.2, 28.0],
            years: [2024, 2025, 2026, 2027, 2028]
        },
        year: 2026
    },
    'Rajasthan': {
        state: 'Rajasthan',
        summary: {
            AOD: {
                category: 'Hazy',
                mean_percentage_of_max: 95.2,
                mean_value: 0.952,
                spike_detected_next_10_months: true
            },
            'Crop Yield (t/ha)': {
                category: 'Poor',
                mean_percentage_of_max: 35.4,
                mean_value: 0.354,
                spike_detected_next_10_months: false
            },
            'PM2.5': {
                category: 'Moderate',
                mean_percentage_of_max: 82.3,
                mean_value: 82.3,
                spike_detected_next_10_months: true
            },
            Vegetation: {
                category: 'Very Poor',
                mean_percentage_of_max: 18.5,
                mean_value: 0.185,
                spike_detected_next_10_months: false
            },
            'Water Level': {
                category: 'Severe Stress',
                mean_percentage_of_max: 85.0,
                mean_value: 0.85,
                spike_detected_next_10_months: true
            }
        },
        trend: {
            aod: [0.88, 0.92, 0.952, 0.98, 1.02],
            pm25: [75.0, 79.0, 82.3, 86.0, 90.0],
            years: [2024, 2025, 2026, 2027, 2028]
        },
        year: 2026
    }
};

// Generate test data for any state not explicitly defined
function generateTestDataForState(state: string): StateSummaryResponse {
    // Use hash of state name to generate consistent random values
    const hash = state.split('').reduce((a, b) => ((a << 5) - a + b.charCodeAt(0)) | 0, 0);
    const rand = (min: number, max: number) => min + Math.abs(hash % 100) / 100 * (max - min);

    const baseAod = parseFloat(rand(0.3, 1.0).toFixed(3));
    const basePm25 = parseFloat(rand(40, 120).toFixed(1));

    return {
        state,
        summary: {
            AOD: {
                category: rand(0, 1) > 0.5 ? 'Moderate' : 'Hazy',
                mean_percentage_of_max: parseFloat(rand(30, 100).toFixed(1)),
                mean_value: baseAod,
                spike_detected_next_10_months: rand(0, 1) > 0.6
            },
            'Crop Yield (t/ha)': {
                category: rand(0, 1) > 0.5 ? 'Good' : 'Average',
                mean_percentage_of_max: parseFloat(rand(40, 90).toFixed(1)),
                mean_value: parseFloat(rand(0.4, 0.9).toFixed(3)),
                spike_detected_next_10_months: false
            },
            'PM2.5': {
                category: rand(0, 1) > 0.5 ? 'Moderate' : 'Poor',
                mean_percentage_of_max: parseFloat(rand(40, 120).toFixed(1)),
                mean_value: basePm25,
                spike_detected_next_10_months: rand(0, 1) > 0.5
            },
            Vegetation: {
                category: rand(0, 1) > 0.5 ? 'Good' : 'Moderate',
                mean_percentage_of_max: parseFloat(rand(30, 80).toFixed(1)),
                mean_value: parseFloat(rand(0.3, 0.8).toFixed(3)),
                spike_detected_next_10_months: false
            },
            'Water Level': {
                category: rand(0, 1) > 0.5 ? 'Safe' : 'Moderate Stress',
                mean_percentage_of_max: parseFloat(rand(15, 60).toFixed(1)),
                mean_value: parseFloat(rand(0.15, 0.6).toFixed(2)),
                spike_detected_next_10_months: rand(0, 1) > 0.7
            }
        },
        trend: {
            aod: [baseAod * 0.9, baseAod * 0.95, baseAod, baseAod * 1.02, baseAod * 1.05],
            pm25: [basePm25 * 0.9, basePm25 * 0.95, basePm25, basePm25 * 1.02, basePm25 * 1.05],
            years: [2024, 2025, 2026, 2027, 2028]
        },
        year: 2026
    };
}

// Check if backend is online
export async function checkBackendHealth(): Promise<HealthStatus> {
    if (USE_TEST_DATA) {
        return { online: true, message: 'Using test data' };
    }

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

// NEW: Fetch state summary using new API format
// Request: /api/data?state=Delhi
// Response: { state, summary: { AOD, Crop Yield, PM2.5, Vegetation, Water Level }, year }
export async function fetchStateSummary(state: string = 'Delhi'): Promise<StateSummaryResponse | null> {
    if (USE_TEST_DATA) {
        // Return test data
        if (TEST_STATE_SUMMARY[state]) {
            return TEST_STATE_SUMMARY[state];
        }
        return generateTestDataForState(state);
    }

    try {
        const response = await apiCall('/api/data', { state });
        return response as StateSummaryResponse;
    } catch (error) {
        console.error("API Error fetching state summary:", error);
        return null;
    }
}

// Legacy function - converts new API response to old format for compatibility
export async function fetchPollutionData(state: string = 'Delhi'): Promise<PollutionData[]> {
    try {
        const summary = await fetchStateSummary(state);
        if (!summary) {
            return [];
        }

        // Convert new format to old format for backwards compatibility
        return [{
            year: summary.year,
            pm25: summary.summary['PM2.5'].mean_value,
            aod: summary.summary.AOD.mean_value,
        }];
    } catch (error) {
        console.error("API Error fetching pollution data:", error);
        return [];
    }
}

// Fetch monthly data for a SINGLE year only (optimized)
// Now uses the new API: /api/data?state=X&type=Y&year=Z
export async function fetchMonthlyDataForYear(
    state: string,
    metric: MetricType,
    year: number
): Promise<MonthlyData[]> {
    // Map MetricType to API type parameter
    const apiTypeMap: Record<MetricType, string> = {
        'pm25': 'pm2.5',
        'aod': 'aod',
        'vegetation': 'vegetation',
        'crop_yield': 'crop_yield',
        'water_levels': 'water_level',
    };

    const apiType = apiTypeMap[metric];

    if (USE_TEST_DATA) {
        // Generate synthetic monthly test data
        const summary = TEST_STATE_SUMMARY[state] || generateTestDataForState(state);
        let baseValue = 0;

        switch (metric) {
            case 'pm25':
                baseValue = summary.summary['PM2.5'].mean_value;
                break;
            case 'aod':
                baseValue = summary.summary.AOD.mean_value;
                break;
            case 'vegetation':
                baseValue = summary.summary.Vegetation.mean_value;
                break;
            case 'crop_yield':
                baseValue = summary.summary['Crop Yield (t/ha)'].mean_value;
                break;
            case 'water_levels':
                baseValue = summary.summary['Water Level'].mean_value;
                break;
        }

        // Generate monthly variations
        return MONTHS.map((month, index) => {
            const seasonalFactor = Math.sin((index / 12) * 2 * Math.PI) * 0.2;
            const variation = (Math.random() - 0.5) * 0.1;
            let value = baseValue * (1 + seasonalFactor + variation);
            value = Math.max(0, value);

            return {
                month,
                value: parseFloat(value.toFixed(2)),
            };
        });
    }

    try {
        // Call new API endpoint with state, type, and year
        const response = await apiCall('/api/data', {
            state,
            type: apiType,
            year
        }) as MetricDetailResponse;

        // Convert monthly_averages array to MonthlyData format
        if (response && response.monthly_averages && response.monthly_averages.length === 12) {
            return MONTHS.map((month, index) => ({
                month,
                value: parseFloat(response.monthly_averages[index].toFixed(2)),
            }));
        }

        return [];
    } catch (error) {
        console.error("API Error fetching monthly data for year:", error);
        return [];
    }
}

// Fetch full metric detail including annual stats
// Uses: /api/data?state=X&type=Y&year=Z
export async function fetchMetricDetail(
    state: string,
    metric: MetricType,
    year: number
): Promise<MetricDetailResponse | null> {
    const apiTypeMap: Record<MetricType, string> = {
        'pm25': 'pm2.5',
        'aod': 'aod',
        'vegetation': 'vegetation',
        'crop_yield': 'crop_yield',
        'water_levels': 'water_level',
    };

    try {
        const response = await apiCall('/api/data', {
            state,
            type: apiTypeMap[metric],
            year
        }) as MetricDetailResponse;
        return response;
    } catch (error) {
        console.error("API Error fetching metric detail:", error);
        return null;
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
    // 2024 is actual data, 2025-2035 are predicted
    const years = [];
    for (let year = 2024; year <= 2035; year++) {
        years.push(year);
    }
    return years;
}

// Helper function to get category color
export function getCategoryColor(category: string): string {
    const categoryColors: Record<string, string> = {
        // Good categories
        'Excellent': 'text-green-500',
        'Good': 'text-green-400',
        'Safe': 'text-green-500',
        'Clear': 'text-green-400',
        // Moderate categories
        'Average': 'text-yellow-500',
        'Moderate': 'text-yellow-500',
        'Moderate Stress': 'text-yellow-500',
        // Poor categories
        'Poor': 'text-orange-500',
        'Very Poor': 'text-orange-600',
        'Hazy': 'text-orange-500',
        // Severe categories
        'Very Hazy': 'text-red-500',
        'Severe Stress': 'text-red-500',
    };

    return categoryColors[category] || 'text-muted-foreground';
}

// Helper to get background color for category badges
export function getCategoryBgColor(category: string): string {
    const categoryColors: Record<string, string> = {
        // Good categories
        'Excellent': 'bg-green-500/20 text-green-500',
        'Good': 'bg-green-400/20 text-green-400',
        'Safe': 'bg-green-500/20 text-green-500',
        'Clear': 'bg-green-400/20 text-green-400',
        // Moderate categories
        'Average': 'bg-yellow-500/20 text-yellow-500',
        'Moderate': 'bg-yellow-500/20 text-yellow-500',
        'Moderate Stress': 'bg-yellow-500/20 text-yellow-500',
        // Poor categories
        'Poor': 'bg-orange-500/20 text-orange-500',
        'Very Poor': 'bg-orange-600/20 text-orange-600',
        'Hazy': 'bg-orange-500/20 text-orange-500',
        // Severe categories  
        'Very Hazy': 'bg-red-500/20 text-red-500',
        'Severe Stress': 'bg-red-500/20 text-red-500',
    };

    return categoryColors[category] || 'bg-muted text-muted-foreground';
}
