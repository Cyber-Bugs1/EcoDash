# 🛰️ Satellite Environmental Dashboard

A real-time environmental monitoring platform that provides actionable insights on air quality, agriculture, and water resources across Indian states using satellite data.

---

## 🌍 Overview

This dashboard transforms complex satellite and environmental data into clear, actionable information for policymakers, researchers, farmers, and citizens. It provides a unified view of five critical environmental metrics with predictive alerts for upcoming environmental changes.

---

## 📊 Key Metrics Monitored

| Metric | What It Measures | Real-World Impact |
|--------|------------------|-------------------|
| **PM2.5** | Fine particulate matter in air | Directly affects respiratory health and outdoor activity safety |
| **AOD** | Aerosol Optical Depth | Indicates atmospheric haze affecting visibility and solar radiation |
| **Vegetation** | Green cover and plant health | Tracks deforestation, urban expansion, and ecosystem health |
| **Crop Yield** | Agricultural productivity | Helps farmers and officials plan food security measures |
| **Water Level** | Water stress indicators | Essential for drought monitoring and water resource management |

---

## 🎯 Real-World Applications

### For Government & Policymakers
- Monitor environmental health across states at a glance
- Receive early warnings for pollution spikes
- Make data-driven decisions for resource allocation

### For Agriculture & Farmers
- Track crop yield trends and predictions
- Plan irrigation based on water stress levels
- Understand vegetation health patterns

### For Public Health
- Air quality monitoring for health advisories
- Pollution spike alerts for vulnerable populations
- Historical trends to understand seasonal patterns

### For Researchers & Educators
- Access consolidated environmental data
- Study long-term trends and predictions
- Validate models with real satellite observations

---

## ✨ Key Features

- **State-wise Analysis** — Select any Indian state for detailed metrics
- **Predictive Alerts** — Get warnings for upcoming environmental spikes
- **Trend Visualization** — View historical and predicted data through 2035
- **Category Ratings** — Easy-to-understand labels (Good, Moderate, Poor, etc.)
- **Monthly Breakdown** — Detailed monthly data for pattern analysis

---

## 🚀 Getting Started

1. Configure the API endpoint in `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://your-api-server:port
   ```

2. Install dependencies and run:
   ```bash
   npm install
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

---

## 📁 Project Structure

```
├── src/app/dashboard     # Main dashboard view
├── src/app/metric        # Individual metric detail pages
├── src/components        # Reusable UI components
├── src/lib               # Data services and utilities
└── public                # Static assets
```

---

## 🤝 Contributing

We welcome contributions to improve environmental monitoring capabilities. See `CHALLENGES.md` for known issues and development notes.

---

## 📜 License

This project was developed as part of a hackathon initiative for environmental awareness and public good.

---

*Built with Next.js • Powered by Satellite Data • Made for India 🇮🇳*
