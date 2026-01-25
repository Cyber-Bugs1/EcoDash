# 🚧 Problems & Challenges Faced While Building This Project

This document outlines the major challenges encountered during the development of the Satellite Environmental Dashboard project.

---

## 1. API Key Mismatch - `'Crop Yield'` vs `'Crop Yield (t/ha)'`

**Error**: `Cannot read properties of undefined (reading 'mean_value')`

**Cause**: The frontend expected the API to return `summary['Crop Yield']` but the API actually returns `summary['Crop Yield (t/ha)']` with the unit in the key name.

**Solution**: Updated the TypeScript interface `StateSummaryResponse` and all component references to use the correct key.

---

## 2. Project Migration Issues

**Problem**: After moving the project to a new folder, the application stopped working.

**Cause**: Path discrepancies and broken dependencies after folder relocation.

**Solution**: Debugged and fixed path issues, including `node_modules` reinstallation.

---

## 3. API Backend Migration

**Challenge**: Migrating from local SQLite database to an external API backend.

**Tasks involved**:
- Updating `data-service.ts` to make `fetch()` calls instead of SQLite queries
- Creating `.env.local` for API configuration
- Handling API server offline scenarios gracefully
- Adding new metric pages (Vegetation, Crop Yield, Water Level) similar to existing PM2.5 and AOD pages
- Implementing temporary API logging for debugging

---

## 4. Database Schema Migration

**Challenge**: Migrating to a new SQLite database (`envdb.db`) with pollution-specific data.

**Issues**: 
- Updating data service to query the new schema
- Refactoring dashboard and metric pages to display PM2.5 and AOD
- Removing old environmental metrics that were no longer relevant

---

## 5. API Response Format Changes

**Problem**: The API response format changed, breaking the dashboard.

**New format included**: Summary data for 5 metrics (AOD, Crop Yield, PM2.5, Vegetation, Water Level) with:
- `category`
- `mean_value`
- `mean_percentage_of_max`
- `spike_detected_next_10_months`

**Solution**: Updated data service and dashboard components to consume the new format.

---

## 6. UI/UX Enhancements & Fixes

Several UI issues needed addressing:

| Issue | Solution |
|-------|----------|
| State selection dropdown had variable height | Fixed to have a constant height |
| Y-axis resolution on graphs was too low | Added more intermediate values |
| No loading feedback during page transitions | Implemented ghost skeleton loading animations |
| Year-over-year comparison was unnecessary | Removed from metric detail pages |
| Old API endpoint format | Updated to use `/api/data?state=X&type=Y&year=Z` |

---

## 7. Font & Design Updates

- Updated application font to a cleaner, more formal design using Google Fonts
- Fixed state selection dropdown sizing issues
- Implemented smoke/water-themed page transition animations that trigger correctly on client-side navigation

---

## 8. Python Application Debugging

- Earlier debugging work on a Python backend application that wasn't working correctly on the development device

---

## 📋 Summary of Key Lessons Learned

| Category | Issue | Takeaway |
|----------|-------|----------|
| **API Integration** | Key name mismatches | Always verify actual API response structure |
| **Type Safety** | Undefined access errors | Add null checks for optional API fields |
| **Migration** | Database & folder changes | Test thoroughly after any migration |
| **UI/UX** | Loading states | Use skeleton loaders for better UX |
| **Error Handling** | Backend offline | Show user-friendly error messages |

---

*Last updated: January 25, 2026*
