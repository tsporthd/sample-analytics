#!/usr/bin/env python3
"""
SOLID-compliant data analysis utility.

This refactored version follows SOLID principles:
- Single Responsibility: Each class has one clear purpose
- Open/Closed: Easy to extend with new readers/writers/generators
- Liskov Substitution: Interfaces can be substituted seamlessly
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

import sys
from data_processors import (
    CSVDataReader, CSVDataWriter, RiskChartGenerator, 
    ConsoleReportGenerator, DataAnalysisService
)
from app_filter import CSVAppCodeFilter


def create_analysis_service() -> DataAnalysisService:
    """Factory method to create configured analysis service."""
    # Dependency injection - easy to swap implementations
    data_reader = CSVDataReader()
    data_writer = CSVDataWriter()
    chart_generator = RiskChartGenerator()
    report_generator = ConsoleReportGenerator()
    
    # Create and configure AppCode filter
    app_filter = CSVAppCodeFilter()
    app_filter.load_allowed_appcodes('Apps.csv')
    
    return DataAnalysisService(
        data_reader=data_reader,
        data_writer=data_writer,
        chart_generator=chart_generator,
        report_generator=report_generator,
        app_filter=app_filter
    )


def display_sample_data(records, max_records=10):
    """Display sample of enhanced data."""
    print(f"\nSample of enhanced data:")
    print("-" * 100)
    
    if not records:
        print("No records to display")
        return
    
    # Print header
    sample_dict = records[0].to_dict()
    headers = list(sample_dict.keys())
    print(" | ".join(f"{h[:15]:<15}" for h in headers))
    print("-" * 100)
    
    # Print sample records
    for i, record in enumerate(records[:max_records]):
        record_dict = record.to_dict()
        print(" | ".join(f"{str(record_dict[h])[:15]:<15}" for h in headers))
    
    if len(records) > max_records:
        print(f"... and {len(records) - max_records} more records")


def main():
    """Main application entry point."""
    csv_file = 'sampleData.csv'
    
    # Create service with dependency injection
    analysis_service = create_analysis_service()
    
    # Analyze data
    enhanced_records, appcode_counts = analysis_service.analyze_data(csv_file)
    
    if not enhanced_records:
        print("No data to analyze")
        sys.exit(1)
    
    # Generate reports
    analysis_service.generate_full_report(enhanced_records, appcode_counts)
    
    # Save enhanced data (excluding AppCode column)
    analysis_service.save_enhanced_data(enhanced_records, 'analyzed_data.csv', exclude_appcode=True)
    
    # Display sample data
    display_sample_data(enhanced_records)


if __name__ == "__main__":
    main()