"""
Database operations for environmental monitoring system.
Handles inserting, querying, and aggregating pollution data.
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
import pandas as pd

from .schema import RawPollutionData, ProcessedPollutionData, CountryPollutionData, get_session


class PollutionDataOperations:
    """Operations for managing pollution data in the database."""
    
    def __init__(self, db_path: str = "environmental_monitoring.db"):
        self.db_path = db_path
    
    def get_session(self) -> Session:
        """Get a database session."""
        return get_session(self.db_path)
    
    # ========== RAW DATA OPERATIONS ==========
    
    def insert_raw_pollution_data(
        self,
        state_name: str,
        year: int,
        pm25_value: float,
        month: Optional[int] = None,
        data_points_count: Optional[int] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Insert raw pollution data into the database.
        
        Returns:
            ID of the inserted record
        """
        session = self.get_session()
        try:
            record = RawPollutionData(
                state_name=state_name,
                year=year,
                month=month,
                pm25_value=pm25_value,
                data_points_count=data_points_count,
                source=source,
                notes=notes
            )
            session.add(record)
            session.commit()
            record_id = record.id
            return record_id
        finally:
            session.close()
    
    def bulk_insert_raw_pollution_data(self, records: List[Dict]) -> int:
        """
        Bulk insert raw pollution data.
        
        Args:
            records: List of dictionaries with pollution data
        
        Returns:
            Number of records inserted
        """
        session = self.get_session()
        try:
            objects = [RawPollutionData(**record) for record in records]
            session.bulk_save_objects(objects)
            session.commit()
            return len(objects)
        finally:
            session.close()
    
    def get_raw_pollution_by_state_year(
        self,
        state_name: str,
        year: int
    ) -> List[RawPollutionData]:
        """Get all raw pollution records for a state and year."""
        session = self.get_session()
        try:
            records = session.query(RawPollutionData).filter(
                and_(
                    RawPollutionData.state_name == state_name,
                    RawPollutionData.year == year
                )
            ).all()
            return records
        finally:
            session.close()
    
    def get_all_raw_pollution_by_year(self, year: int) -> List[RawPollutionData]:
        """Get all raw pollution records for a given year."""
        session = self.get_session()
        try:
            records = session.query(RawPollutionData).filter(
                RawPollutionData.year == year
            ).all()
            return records
        finally:
            session.close()
    
    # ========== PROCESSED DATA OPERATIONS ==========
    
    def insert_processed_pollution_data(
        self,
        state_name: str,
        year: int,
        pm25_annual_avg: float,
        pm25_max: Optional[float] = None,
        pm25_min: Optional[float] = None,
        pm25_std_dev: Optional[float] = None,
        year_over_year_change: Optional[float] = None,
        trend_direction: Optional[str] = None,
        severity_level: Optional[str] = None,
        exceeds_safe_limit: Optional[bool] = None,
        model_version: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> int:
        """Insert processed pollution data into the database."""
        session = self.get_session()
        try:
            record = ProcessedPollutionData(
                state_name=state_name,
                year=year,
                pm25_annual_avg=pm25_annual_avg,
                pm25_max=pm25_max,
                pm25_min=pm25_min,
                pm25_std_dev=pm25_std_dev,
                year_over_year_change=year_over_year_change,
                trend_direction=trend_direction,
                severity_level=severity_level,
                exceeds_safe_limit=exceeds_safe_limit,
                model_version=model_version,
                confidence_score=confidence_score
            )
            session.add(record)
            session.commit()
            return record.id
        finally:
            session.close()
    
    def get_processed_pollution_by_state_year(
        self,
        state_name: str,
        year: int
    ) -> Optional[ProcessedPollutionData]:
        """Get processed pollution data for a state and year."""
        session = self.get_session()
        try:
            record = session.query(ProcessedPollutionData).filter(
                and_(
                    ProcessedPollutionData.state_name == state_name,
                    ProcessedPollutionData.year == year
                )
            ).first()
            return record
        finally:
            session.close()
    
    def get_all_processed_pollution_by_year(self, year: int) -> List[ProcessedPollutionData]:
        """Get all processed pollution records for a given year."""
        session = self.get_session()
        try:
            records = session.query(ProcessedPollutionData).filter(
                ProcessedPollutionData.year == year
            ).order_by(ProcessedPollutionData.pm25_annual_avg.desc()).all()
            return records
        finally:
            session.close()
    
    # ========== COUNTRY DATA OPERATIONS ==========
    
    def insert_country_pollution_data(
        self,
        year: int,
        pm25_national_avg: float,
        pm25_max_state: Optional[str] = None,
        pm25_max_value: Optional[float] = None,
        pm25_min_state: Optional[str] = None,
        pm25_min_value: Optional[float] = None,
        states_above_safe_limit: Optional[int] = None,
        total_states_measured: Optional[int] = None,
        national_std_dev: Optional[float] = None,
        year_over_year_change: Optional[float] = None,
        trend_direction: Optional[str] = None
    ) -> int:
        """Insert country-wide pollution data."""
        session = self.get_session()
        try:
            # Check if record exists for this year
            existing = session.query(CountryPollutionData).filter(
                CountryPollutionData.year == year
            ).first()
            
            if existing:
                # Update existing record
                existing.pm25_national_avg = pm25_national_avg
                existing.pm25_max_state = pm25_max_state
                existing.pm25_max_value = pm25_max_value
                existing.pm25_min_state = pm25_min_state
                existing.pm25_min_value = pm25_min_value
                existing.states_above_safe_limit = states_above_safe_limit
                existing.total_states_measured = total_states_measured
                existing.national_std_dev = national_std_dev
                existing.year_over_year_change = year_over_year_change
                existing.trend_direction = trend_direction
                existing.processing_date = datetime.utcnow()
                record_id = existing.id
            else:
                # Create new record
                record = CountryPollutionData(
                    year=year,
                    pm25_national_avg=pm25_national_avg,
                    pm25_max_state=pm25_max_state,
                    pm25_max_value=pm25_max_value,
                    pm25_min_state=pm25_min_state,
                    pm25_min_value=pm25_min_value,
                    states_above_safe_limit=states_above_safe_limit,
                    total_states_measured=total_states_measured,
                    national_std_dev=national_std_dev,
                    year_over_year_change=year_over_year_change,
                    trend_direction=trend_direction
                )
                session.add(record)
                record_id = record.id
            
            session.commit()
            return record_id
        finally:
            session.close()
    
    def get_country_pollution_by_year(self, year: int) -> Optional[CountryPollutionData]:
        """Get country-wide pollution data for a given year."""
        session = self.get_session()
        try:
            record = session.query(CountryPollutionData).filter(
                CountryPollutionData.year == year
            ).first()
            return record
        finally:
            session.close()
    
    def get_all_country_pollution_data(self) -> List[CountryPollutionData]:
        """Get all country-wide pollution data ordered by year."""
        session = self.get_session()
        try:
            records = session.query(CountryPollutionData).order_by(
                CountryPollutionData.year
            ).all()
            return records
        finally:
            session.close()
    
    # ========== AGGREGATION AND ANALYSIS ==========
    
    def get_states_list(self) -> List[str]:
        """Get list of unique states in the database."""
        session = self.get_session()
        try:
            states = session.query(RawPollutionData.state_name).distinct().all()
            return [state[0] for state in states]
        finally:
            session.close()
    
    def get_years_list(self) -> List[int]:
        """Get list of unique years in the database."""
        session = self.get_session()
        try:
            years = session.query(RawPollutionData.year).distinct().order_by(
                RawPollutionData.year
            ).all()
            return [year[0] for year in years]
        finally:
            session.close()
    
    def export_to_dataframe(
        self,
        table: str = "processed",
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Export data to pandas DataFrame for analysis.
        
        Args:
            table: 'raw', 'processed', or 'country'
            year: Filter by specific year (optional)
        
        Returns:
            DataFrame with the data
        """
        session = self.get_session()
        try:
            if table == "raw":
                query = session.query(RawPollutionData)
                if year:
                    query = query.filter(RawPollutionData.year == year)
            elif table == "processed":
                query = session.query(ProcessedPollutionData)
                if year:
                    query = query.filter(ProcessedPollutionData.year == year)
            elif table == "country":
                query = session.query(CountryPollutionData)
                if year:
                    query = query.filter(CountryPollutionData.year == year)
            else:
                raise ValueError(f"Invalid table: {table}")
            
            df = pd.read_sql(query.statement, session.bind)
            return df
        finally:
            session.close()
