"""
Script to process raw pollution data: AOD → PM2.5 → AQI.

Converts raw AOD data using meteorological parameters to PM2.5 concentrations,
then calculates AQI values according to India CPCB standards.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.schema import get_session, RawPollutionData, ProcessedPollutionData, CountryPollutionData
from analysis.aod_to_pm25 import AODtoPM25Converter, AQICalculator


def process_state_year_data(
    raw_data: RawPollutionData,
    converter: AODtoPM25Converter,
    aqi_calc: AQICalculator
) -> ProcessedPollutionData:
    """
    Process a single raw pollution data record.
    
    Args:
        raw_data: Raw pollution data record
        converter: AOD to PM2.5 converter
        aqi_calc: AQI calculator
    
    Returns:
        Processed pollution data record
    """
    # Convert AOD to PM2.5 using empirical regional factors
    pm25_stats = converter.convert_with_stats(
        aod_mean=raw_data.aod_mean,
        aod_stddev=raw_data.aod_stddev,
        aod_min=raw_data.aod_min,
        aod_max=raw_data.aod_max,
        state_name=raw_data.state_name,
        month=raw_data.month  # None for annual data
    )
    
    # Get scale factor used
    scale_factor = converter.get_scale_factor(raw_data.state_name, raw_data.month)
    
    # Calculate AQI from mean PM2.5
    aqi_value, aqi_category, aqi_color = aqi_calc.calculate(pm25_stats['pm25_mean'])
    
    # Create processed record
    processed = ProcessedPollutionData(
        state_name=raw_data.state_name,
        year=raw_data.year,
        
        # Raw AOD values
        aod_mean=raw_data.aod_mean,
        aod_stddev=raw_data.aod_stddev,
        aod_min=raw_data.aod_min,
        aod_max=raw_data.aod_max,
        
        # Meteorological parameters (may be null)
        blh=raw_data.blh,
        temperature=raw_data.temperature,
        relative_humidity=raw_data.relative_humidity,
        
        # PM2.5 values
        pm25_mean=pm25_stats['pm25_mean'],
        pm25_stddev=pm25_stats['pm25_stddev'],
        pm25_min=pm25_stats['pm25_min'],
        pm25_max=pm25_stats['pm25_max'],
        
        # AQI values
        aqi_mean=aqi_value,
        aqi_category=aqi_category,
        aqi_color=aqi_color,
        
        # Safety thresholds
        exceeds_who_limit=(pm25_stats['pm25_mean'] > 15) if pm25_stats['pm25_mean'] else None,
        exceeds_india_limit=(pm25_stats['pm25_mean'] > 60) if pm25_stats['pm25_mean'] else None,
        
        # Conversion metadata
        conversion_method='empirical_regional',
        hygroscopic_factor=scale_factor,  # Store scale factor in this field
        model_version='v2.0_empirical',
        processing_date=datetime.utcnow()
    )
    
    return processed


def calculate_trends(session, state_name: str, current_year: int):
    """
    Calculate year-over-year trends for a state.
    
    Args:
        session: Database session
        state_name: State name
        current_year: Current year
    
    Returns:
        Dictionary with trend data
    """
    # Get previous year's data
    prev_year_data = session.query(ProcessedPollutionData).filter_by(
        state_name=state_name,
        year=current_year - 1
    ).first()
    
    if not prev_year_data:
        return {
            'year_over_year_change': None,
            'trend_direction': None
        }
    
    # Get current year's data
    current_data = session.query(ProcessedPollutionData).filter_by(
        state_name=state_name,
        year=current_year
    ).first()
    
    if not current_data or not prev_year_data.pm25_mean:
        return {
            'year_over_year_change': None,
            'trend_direction': None
        }
    
    # Calculate change percentage
    change_pct = ((current_data.pm25_mean - prev_year_data.pm25_mean) / prev_year_data.pm25_mean) * 100
    
    # Determine direction
    if abs(change_pct) < 5:  # Less than 5% change is stable
        direction = 'stable'
    elif change_pct > 0:
        direction = 'increasing'
    else:
        direction = 'decreasing'
    
    return {
        'year_over_year_change': change_pct,
        'trend_direction': direction
    }


def aggregate_country_data(session, year: int):
    """
    Calculate country-wide aggregated statistics.
    
    Args:
        session: Database session
        year: Year to aggregate
    """
    # Get all processed data for the year
    all_data = session.query(ProcessedPollutionData).filter_by(year=year).all()
    
    if not all_data:
        print(f"  No processed data found for {year}")
        return
    
    # Calculate statistics
    pm25_values = [d.pm25_mean for d in all_data if d.pm25_mean is not None]
    
    if not pm25_values:
        print(f"  No valid PM2.5 values for {year}")
        return
    
    import numpy as np
    
    national_avg = np.mean(pm25_values)
    national_std = np.std(pm25_values)
    
    # Find max and min states
    max_state = max(all_data, key=lambda x: x.pm25_mean if x.pm25_mean else 0)
    min_state = min(all_data, key=lambda x: x.pm25_mean if x.pm25_mean else float('inf'))
    
    # Count states exceeding limits
    states_above_who = sum(1 for d in all_data if d.exceeds_who_limit)
    states_above_india = sum(1 for d in all_data if d.exceeds_india_limit)
    
    # Check if record exists
    country_record = session.query(CountryPollutionData).filter_by(year=year).first()
    
    if country_record:
        # Update existing
        country_record.pm25_national_avg = national_avg
        country_record.pm25_max_state = max_state.state_name
        country_record.pm25_max_value = max_state.pm25_mean
        country_record.pm25_min_state = min_state.state_name
        country_record.pm25_min_value = min_state.pm25_mean
        country_record.states_above_safe_limit = states_above_who
        country_record.total_states_measured = len(all_data)
        country_record.national_std_dev = national_std
        country_record.processing_date = datetime.utcnow()
    else:
        # Create new
        country_record = CountryPollutionData(
            year=year,
            pm25_national_avg=national_avg,
            pm25_max_state=max_state.state_name,
            pm25_max_value=max_state.pm25_mean,
            pm25_min_state=min_state.state_name,
            pm25_min_value=min_state.pm25_mean,
            states_above_safe_limit=states_above_who,
            total_states_measured=len(all_data),
            national_std_dev=national_std,
            processing_date=datetime.utcnow()
        )
        session.add(country_record)
    
    session.commit()
    
    print(f"\n  Country-wide statistics for {year}:")
    print(f"    National avg PM2.5: {national_avg:.1f} µg/m³")
    print(f"    Max: {max_state.state_name} ({max_state.pm25_mean:.1f} µg/m³)")
    print(f"    Min: {min_state.state_name} ({min_state.pm25_mean:.1f} µg/m³)")
    print(f"    States exceeding WHO limit (15 µg/m³): {states_above_who}/{len(all_data)}")
    print(f"    States exceeding India limit (60 µg/m³): {states_above_india}/{len(all_data)}")


def main():
    """Main processing function."""
    print("=" * 60)
    print("Processing Raw Data: AOD → PM2.5 → AQI")
    print("=" * 60)
    
    db_path = str(Path(__file__).parent.parent / "environmental_monitoring.db")
    session = get_session(db_path)
    
    # Initialize converters
    converter = AODtoPM25Converter()
    aqi_calc = AQICalculator()
    
    # Get all raw data
    raw_records = session.query(RawPollutionData).all()
    
    if not raw_records:
        print("\n✗ No raw data found in database")
        print("  Run: uv run python scripts/load_raw_data_to_db.py")
        return
    
    print(f"\nFound {len(raw_records)} raw pollution records")
    
    # Group by year
    years = sorted(set(r.year for r in raw_records))
    
    for year in years:
        print(f"\n{'='*60}")
        print(f"Processing year {year}")
        print(f"{'='*60}")
        
        year_records = [r for r in raw_records if r.year == year]
        records_processed = 0
        records_with_met = 0
        
        for raw_data in year_records:
            try:
                # Check if already processed
                existing = session.query(ProcessedPollutionData).filter_by(
                    state_name=raw_data.state_name,
                    year=raw_data.year
                ).first()
                
                if existing:
                    # Update existing record
                    processed = process_state_year_data(raw_data, converter, aqi_calc)
                    for key, value in processed.__dict__.items():
                        if not key.startswith('_') and key != 'id':
                            setattr(existing, key, value)
                else:
                    # Create new record
                    processed = process_state_year_data(raw_data, converter, aqi_calc)
                    session.add(processed)
                
                if raw_data.blh is not None:
                    records_with_met += 1
                
                records_processed += 1
                
                # Print progress
                if records_processed % 10 == 0:
                    print(f"  Processed {records_processed}/{len(year_records)} states...")
                
            except Exception as e:
                print(f"  ✗ Error processing {raw_data.state_name} {year}: {e}")
                continue
        
        session.commit()
        
        print(f"\n  ✓ Processed {records_processed} states for {year}")
        print(f"  ✓ {records_with_met} states had meteorological data")
        print(f"  ⚠ {records_processed - records_with_met} used default values")
        
        # Calculate trends
        print(f"\n  Calculating year-over-year trends...")
        for record in session.query(ProcessedPollutionData).filter_by(year=year).all():
            trends = calculate_trends(session, record.state_name, year)
            record.year_over_year_change = trends['year_over_year_change']
            record.trend_direction = trends['trend_direction']
        
        session.commit()
        
        # Aggregate country data
        aggregate_country_data(session, year)
    
    session.close()
    
    # Final summary
    session = get_session(db_path)
    total_processed = session.query(ProcessedPollutionData).count()
    total_country = session.query(CountryPollutionData).count()
    session.close()
    
    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Total processed records: {total_processed}")
    print(f"Country-wide records: {total_country}")
    print("\n✓ All data has been processed and stored in database!")


if __name__ == "__main__":
    main()
