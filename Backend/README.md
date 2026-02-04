# Satalite (EcoDash)

**AI-based Environmental Monitoring System using Google Earth Engine**

## Overview
Satalite (EcoDash) is a comprehensive backend system designed for environmental monitoring and prediction. It leverages AI models and Google Earth Engine data to provide insights into pollution levels (PM2.5, AOD), vegetation health, crop yields, and water levels across various states in India.

## Features

*   **Data Output Service**: Retrieval of historical and predicted environmental data (PM2.5, AOD, Vegetation, Crop Yield, Water Levels).
*   **Pollution Prediction**: AI-powered prediction of PM2.5 and AQI levels based on historical data.
*   **Historical Analysis**: Comparative analysis of environmental data over the past 5 years.
*   **Comparison & Extrapolation**: Tools to compare data across years and extrapolate future trends.
*   **Notification System**: Alerting system for high pollution levels with future forecasting.
*   **Expose Server**: Publicly accessible endpoints for integration.

## API Documentation
For detailed information on available endpoints and request formats, please refer to [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Prerequisites
*   **OS**: Windows, macOS, or Linux
*   **Python**: Version 3.12 or higher

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd Satalite
    ```

2.  **Set up Virtual Environment**
    It is recommended to use `uv` for dependency management, but standard `pip` works as well.

    *Using uv:*
    ```bash
    uv sync
    ```

    *Using pip:*
    ```bash
    python -m venv .venv
    # Activate the virtual environment
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is not present, install from `pyproject.toml` dependencies).*

## Usage

### Windows Users 🪟
We have provided a convenient batch script to start both backend servers automatically.

1.  Double-click **`run_servers.bat`** in the root directory.
    *   *Alternatively, run it from the command line:*
        ```cmd
        run_servers.bat
        ```
2.  This will open two terminal windows:
    *   **Basic Backend Server**: Runs the core API logic.
    *   **Expose Server**: Handles public exposure of endpoints.

### Non-Windows Users (macOS/Linux) 🍎🐧
You will need to manually start the servers in separate terminal sessions.

**Terminal 1: Basic Backend Server**
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python src/api/basic_backend_server.py
```

**Terminal 2: Expose Server**
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python src/api/expose_server.py
```

## Project Structure
*   `src/api/`: Contains server implementations (`basic_backend_server.py`, `expose_server.py`).
*   `models/`: Trained AI models.
*   `data/`: Raw and processed data storage.
*   `scripts/`: Utility scripts for data processing and model training.

---
*Built for the Polytechnic-Minor Hackathon.*
