"""
Database schema for environmental monitoring system.
Stores both raw and processed pollution data.
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class RawPollutionData(Base):
    """Table for storing raw AOD data from Google Earth Engine."""
    __tablename__ = 'raw_pollution_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True)  # Optional: for monthly data
    
    # AOD values from satellite
    aod_mean = Column(Float, nullable=False)  # Mean AOD value
    aod_stddev = Column(Float)  # Standard deviation
    aod_min = Column(Float)  # Minimum AOD
    aod_max = Column(Float)  # Maximum AOD
    
    # Meteorological parameters for PM2.5 conversion
    blh = Column(Float)  # Boundary Layer Height (meters)
    temperature = Column(Float)  # Temperature (Kelvin)
    relative_humidity = Column(Float)  # Relative Humidity (%)
    
    data_points_count = Column(Integer)  # Number of satellite observations used
    collection_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(200))  # Data source/satellite dataset name
    notes = Column(String(500))  # Additional metadata
    
    def __repr__(self):
        return f"<RawPollutionData(state='{self.state_name}', year={self.year}, aod={self.aod_mean})>"


class ProcessedPollutionData(Base):
    """Table for storing processed/analyzed PM2.5 pollution data with AQI."""
    __tablename__ = 'processed_pollution_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Raw AOD values (from raw data)
    aod_mean = Column(Float)  # Mean AOD value
    aod_stddev = Column(Float)  # Standard deviation
    aod_min = Column(Float)  # Minimum AOD
    aod_max = Column(Float)  # Maximum AOD
    
    # Meteorological parameters used
    blh = Column(Float)  # Boundary Layer Height (meters)
    temperature = Column(Float)  # Temperature (Kelvin)
    relative_humidity = Column(Float)  # Relative Humidity (%)
    
    # Converted PM2.5 metrics
    pm25_mean = Column(Float, nullable=False)  # Mean PM2.5 concentration (µg/m³)
    pm25_stddev = Column(Float)  # Standard deviation
    pm25_min = Column(Float)  # Minimum PM2.5 value
    pm25_max = Column(Float)  # Maximum PM2.5 value
    
    # AQI values (India CPCB standard)
    aqi_mean = Column(Integer)  # AQI value (0-500)
    aqi_category = Column(String(20))  # 'Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'
    aqi_color = Column(String(20))  # Color code for visualization
    
    # Trend analysis
    year_over_year_change = Column(Float)  # % change in PM2.5 from previous year
    trend_direction = Column(String(20))  # 'increasing', 'decreasing', 'stable'
    
    # Safety thresholds
    exceeds_who_limit = Column(Boolean)  # True if exceeds WHO guidelines (15 µg/m³)
    exceeds_india_limit = Column(Boolean)  # True if exceeds India standards (60 µg/m³)
    
    # Conversion metadata
    conversion_method = Column(String(50))  # 'advanced_meteorological'
    hygroscopic_factor = Column(Float)  # H factor used in conversion
    
    # Processing metadata
    processing_date = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))  # Version of analysis model used
    
    def __repr__(self):
        return f"<ProcessedPollutionData(state='{self.state_name}', year={self.year}, pm25={self.pm25_mean:.1f}, aqi={self.aqi_mean} [{self.aqi_category}])>"


class CountryPollutionData(Base):
    """Table for storing country-wide aggregated pollution data."""
    __tablename__ = 'country_pollution_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, unique=True, index=True)
    
    # Country-wide metrics
    pm25_national_avg = Column(Float, nullable=False)
    pm25_max_state = Column(String(100))  # State with highest pollution
    pm25_max_value = Column(Float)
    pm25_min_state = Column(String(100))  # State with lowest pollution
    pm25_min_value = Column(Float)
    
    # National statistics
    states_above_safe_limit = Column(Integer)  # Count of states exceeding WHO limits
    total_states_measured = Column(Integer)
    national_std_dev = Column(Float)
    
    # Trends
    year_over_year_change = Column(Float)
    trend_direction = Column(String(20))
    
    processing_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CountryPollutionData(year={self.year}, national_avg={self.pm25_national_avg})>"


def create_database(db_path: str = "environmental_monitoring.db"):
    """
    Create the database and all tables.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        Engine and Session objects
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_session(db_path: str = "environmental_monitoring.db"):
    """Get a database session."""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Create the database when run directly
    print("Creating database schema...")
    engine, Session = create_database("environmental_monitoring.db")
    print(f"✓ Database created successfully!")
    print(f"✓ Tables: {list(Base.metadata.tables.keys())}")
