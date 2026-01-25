# API Documentation

Base URL: `http://<server_ip>:5000`

## 1. Index / Health Check
*   **Endpoint:** `/`
*   **Method:** `GET`
*   **Description:** Checks if the backend service is running and lists water available endpoints.
*   **Response:**
    ```json
    {
      "status": "online",
      "message": "Environmental AI Backend Services are running",
      "endpoints": { ... }
    }
    ```

## 2. Data Output Service
*   **Endpoint:** `/api/data`
*   **Method:** `POST` (or `GET` with query params)
*   **Description:** Retrieves historical or predicted environmental data for a specific type.
*   **Parameters:**
    *   `type` (Required): One of `PM2.5`, `AOD`, `vegetation`, `crop_yield`, `water_levels`
    *   `state` (Required): Name of the state (e.g., "Delhi", "Punjab")
    *   `month` (Required): Month number (1-12)
    *   `city` (Optional): City name
    *   `year` (Optional): Year (default is current year)
*   **Example Query (JSON Body):**
    ```json
    {
      "type": "PM2.5",
      "state": "Delhi",
      "month": 1,
      "year": 2023
    }
    ```

## 3. Pollution Level Prediction
*   **Endpoint:** `/api/predict/pollution`
*   **Method:** `POST` (or `GET` with query params)
*   **Description:** Predicts PM2.5 and AQI levels for a given state and month.
*   **Parameters:**
    *   `state` (Required): Name of the state
    *   `month` (Required): Month number (1-12)
    *   `city` (Optional)
    *   `year` (Optional)
*   **Response includes:** `pm2.5`, `aqi`, `aod`, `category` ("Good"/"Poor")
*   **Example Query (JSON Body):**
    ```json
    {
      "state": "Punjab",
      "month": 10
    }
    ```

## 4. Historical Difference Service
*   **Endpoint:** `/api/history/diff`
*   **Method:** `POST` (or `GET` with query params)
*   **Description:** Retrieves environmental data (Pollution, Vegetation, Crop, Water) for the past 5 years to allow comparison.
*   **Parameters:**
    *   `state` (Required): Name of the state
    *   `city` (Optional)
*   **Example Query (JSON Body):**
    ```json
    {
      "state": "Haryana"
    }
    ```

## 5. Comparison & Extrapolation Service
*   **Endpoint:** `/api/compare`
*   **Method:** `POST` (or `GET` with query params)
*   **Description:** Compares data across a range of years and provides simple linear extrapolation for future years.
*   **Parameters:**
    *   `state` (Required): Name of the state
    *   `month` (Optional): Month number
    *   `start_year` (Optional): Start year (default 2020)
    *   `end_year` (Optional): End year (default 2030)
*   **Example Query (JSON Body):**
    ```json
    {
      "state": "Maharashtra",
      "start_year": 2020,
      "end_year": 2025
    }
    ```

## 6. Notification Service
*   **Endpoint:** `/api/notification`
*   **Method:** `POST` (or `GET` with query params)
*   **Description:** Checks current pollution levels against a threshold (60) to generate an alert, and provides a 10-month future forecast.
*   **Parameters:**
    *   `state` (Required): Name of the state
    *   `city` (Optional)
*   **Response includes:** `alert` (boolean), `message`, `ten_year_forecast` (list of next 10 months)
*   **Example Query (JSON Body):**
    ```json
    {
      "state": "Delhi"
    }
    ```
