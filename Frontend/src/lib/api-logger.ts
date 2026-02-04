// API Logger - Temporary debugging utility
// TODO: Remove this file before production

interface LogEntry {
    timestamp: string;
    method: string;
    url: string;
    request?: any;
    response?: any;
    error?: string;
    duration: number;
}

const logs: LogEntry[] = [];
const MAX_LOGS = 100;

// Enable/disable logging
export const API_LOGGING_ENABLED = true;

export function logApiCall(entry: Omit<LogEntry, 'timestamp'>) {
    if (!API_LOGGING_ENABLED) return;

    const logEntry: LogEntry = {
        ...entry,
        timestamp: new Date().toISOString(),
    };

    logs.unshift(logEntry);

    // Keep only last MAX_LOGS entries
    if (logs.length > MAX_LOGS) {
        logs.pop();
    }

    // Console output for dev server
    const status = entry.error ? '❌ ERROR' : '✅ OK';
    console.log(`\n${'='.repeat(60)}`);
    console.log(`[API ${status}] ${entry.method} ${entry.url}`);
    console.log(`Duration: ${entry.duration}ms`);
    if (entry.request) {
        console.log('Request:', JSON.stringify(entry.request, null, 2));
    }
    if (entry.response) {
        console.log('Response:', JSON.stringify(entry.response, null, 2));
    }
    if (entry.error) {
        console.log('Error:', entry.error);
    }
    console.log('='.repeat(60));
}

export function getLogs(): LogEntry[] {
    return [...logs];
}

export function clearLogs() {
    logs.length = 0;
}
