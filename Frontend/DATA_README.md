# Data Configuration Guide

## Where to Add Your Data

The environmental data is managed in: **`src/lib/data-service.ts`**

### Current Mock Data Structure

```typescript
export interface EnvironmentalData {
  year: number;
  aqi: number;           // Air Quality Index
  co2: number;           // CO2 emissions (ppm)
  forest_cover: number;  // Forest cover percentage
  water_level: number;   // Water reservoir level percentage
  crop_yield: number;    // Crop yield (tons per hectare)
}
```

### Option 1: Update Mock Data Directly
Edit the `MOCK_DATA` array in `src/lib/data-service.ts`:

```typescript
const MOCK_DATA: EnvironmentalData[] = [
  { year: 2020, aqi: 120, co2: 500, forest_cover: 30, water_level: 80, crop_yield: 4.5 },
  // Add more years here...
];
```

### Option 2: Use CSV File
1. Place your CSV file in: `public/data/environmental_data.csv`
2. Update `data-service.ts` to fetch and parse the CSV:

```typescript
import Papa from 'papaparse';

export async function fetchEnvironmentalData(): Promise<EnvironmentalData[]> {
  const response = await fetch('/data/environmental_data.csv');
  const csvText = await response.text();
  const result = Papa.parse(csvText, { header: true, dynamicTyping: true });
  return result.data as EnvironmentalData[];
}
```

### CSV Format Expected
```csv
year,aqi,co2,forest_cover,water_level,crop_yield
2020,120,500,30,80,4.5
2021,115,480,31,78,4.6
```

### Adding New Data Fields
1. Update the `EnvironmentalData` interface
2. Update the charts in `OverviewCharts.tsx`
3. Update the cards in `page.tsx` and `year/[year]/page.tsx`
