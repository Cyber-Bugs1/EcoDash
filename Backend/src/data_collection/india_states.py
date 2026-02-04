"""
Indian state boundary definitions and metadata.
Contains state names and approximate centroid coordinates.
"""

# Indian states and Union Territories
INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
]

# Approximate bounding box for India (for Earth Engine region filtering)
INDIA_BOUNDS = {
    "type": "Polygon",
    "coordinates": [[
        [68.0, 6.0],
        [97.0, 6.0],
        [97.0, 37.0],
        [68.0, 37.0],
        [68.0, 6.0]
    ]]
}

# State centroids (approximate) for reference
STATE_CENTROIDS = {
    "Andhra Pradesh": [79.74, 15.91],
    "Arunachal Pradesh": [94.73, 28.22],
    "Assam": [92.94, 26.24],
    "Bihar": [85.31, 25.60],
    "Chhattisgarh": [81.87, 21.30],
    "Goa": [74.12, 15.30],
    "Gujarat": [71.64, 22.26],
    "Haryana": [76.13, 29.06],
    "Himachal Pradesh": [77.17, 31.10],
    "Jharkhand": [85.54, 23.61],
    "Karnataka": [75.71, 15.32],
    "Kerala": [76.27, 10.85],
    "Madhya Pradesh": [78.66, 22.97],
    "Maharashtra": [75.77, 19.75],
    "Manipur": [93.91, 24.66],
    "Meghalaya": [91.37, 25.47],
    "Mizoram": [92.94, 23.16],
    "Nagaland": [94.11, 26.16],
    "Odisha": [85.10, 20.95],
    "Punjab": [75.34, 31.15],
    "Rajasthan": [74.22, 27.02],
    "Sikkim": [88.51, 27.53],
    "Tamil Nadu": [78.68, 11.13],
    "Telangana": [79.02, 18.11],
    "Tripura": [91.94, 23.94],
    "Uttar Pradesh": [80.95, 26.85],
    "Uttarakhand": [79.01, 30.07],
    "West Bengal": [87.86, 22.99],
    "Delhi": [77.10, 28.70],
    "Jammu and Kashmir": [74.80, 33.78],
    "Ladakh": [78.00, 34.15],
}


def get_state_list():
    """Get list of Indian states."""
    return INDIAN_STATES.copy()


def get_india_bounds():
    """Get bounding box for India."""
    return INDIA_BOUNDS


def get_state_centroid(state_name: str):
    """Get centroid coordinates for a state."""
    return STATE_CENTROIDS.get(state_name)
