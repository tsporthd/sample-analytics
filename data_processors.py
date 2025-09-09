#!/usr/bin/env python3
"""
Data processors implementing SOLID principles.

Concrete implementations of the interfaces defined in data_models.py
"""

import csv
from typing import List, Dict, Any
from data_models import (
    InfrastructureRecord, RiskChartEntry, CompositeScoreMapper, 
    AppCodeCounter, RiskCalculator, DataReader, DataWriter, 
    ChartGenerator, ReportGenerator
)
from app_filter import AppCodeFilter


class CSVDataReader(DataReader):
    """Concrete implementation for reading CSV data."""
    
    def read_data(self, source: str) -> List[InfrastructureRecord]:
        """Read data from CSV file."""
        records = []
        
        try:
            with open(source, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    record = InfrastructureRecord.from_dict(row)
                    records.append(record)
        except FileNotFoundError:
            print(f"Error: File {source} not found")
            return []
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
        
        return records


class CSVDataWriter(DataWriter):
    """Concrete implementation for writing CSV data."""
    
    def write_data(self, records: List[InfrastructureRecord], destination: str) -> None:
        """Write records to CSV file."""
        if not records:
            return
        
        try:
            with open(destination, 'w', newline='', encoding='utf-8') as file:
                # Get fieldnames from first record
                fieldnames = list(records[0].to_dict().keys())
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in records:
                    writer.writerow(record.to_dict())
        except Exception as e:
            print(f"Error writing CSV file: {e}")


class RiskChartGenerator(ChartGenerator):
    """Concrete implementation for generating risk charts."""
    
    def generate_chart(self, records: List[InfrastructureRecord]) -> List[RiskChartEntry]:
        """Generate risk chart entries sorted by risk percentage."""
        # Sort records by risk percentage in descending order
        sorted_records = sorted(
            records, 
            key=lambda x: x.composite_risk_score_percent, 
            reverse=True
        )
        
        chart_entries = []
        for i, record in enumerate(sorted_records, 1):
            entry = RiskChartEntry(
                rank=i,
                app_code=record.app_code,
                composite_risk_score=record.composite_risk_score,
                composite_risk_score_percent=record.composite_risk_score_percent
            )
            chart_entries.append(entry)
        
        return chart_entries


class ConsoleReportGenerator(ReportGenerator):
    """Concrete implementation for generating console reports."""
    
    def generate_report(self, records: List[InfrastructureRecord], 
                       appcode_counts: Dict[str, int]) -> str:
        """Generate summary report for console output."""
        total_records = len(records)
        unique_appcodes = len(appcode_counts)
        total_risk = sum(record.composite_risk_score for record in records)
        
        # Count composite scores
        score_distribution = {}
        for record in records:
            score = record.composite_score
            score_distribution[score] = score_distribution.get(score, 0) + 1
        
        report_lines = [
            "=" * 50,
            "DATA ANALYSIS SUMMARY",
            "=" * 50,
            "",
            f"Total records: {total_records}",
            f"Unique AppCodes: {unique_appcodes}",
            "",
            "AppCode counts:"
        ]
        
        # Add AppCode counts
        for appcode, count in sorted(appcode_counts.items()):
            report_lines.append(f"  {appcode}: {count} items")
        
        report_lines.extend([
            "",
            "CompositeScore distribution:"
        ])
        
        # Add score distribution
        for score, count in sorted(score_distribution.items()):
            numeric_score = CompositeScoreMapper.map_to_number(score)
            report_lines.append(f"  {score} (→ {numeric_score}): {count} items")
        
        report_lines.extend([
            "",
            f"Total Composite Risk Score across all AppCodes: {total_risk}",
            "",
            "New attributes added:",
            "  - TotalInfrastructure: Count of items per AppCode",
            "  - CompositeScoreNumber: Numeric mapping of CompositeScore",
            "  - CompositeRiskScore: CompositeScoreNumber × TotalInfrastructure",
            "  - CompositeRiskScorePercent: (CompositeRiskScore / Total) × 100"
        ])
        
        return "\n".join(report_lines)


class ConsoleChartDisplay:
    """Display chart data in console format."""
    
    @staticmethod
    def display_chart(chart_entries: List[RiskChartEntry]) -> None:
        """Display risk chart in console."""
        print("\n" + "=" * 80)
        print("RISK CHART - SORTED BY COMPOSITE RISK SCORE PERCENT (HIGH TO LOW)")
        print("=" * 80)
        print(f"{'Rank':<4} | {'AppCode':<10} | {'CompositeRiskScore':<18} | {'Percent':<8}")
        print("-" * 80)
        
        for entry in chart_entries:
            print(f"{entry.rank:<4} | {entry.app_code:<10} | "
                  f"{entry.composite_risk_score:<18.1f} | "
                  f"{entry.composite_risk_score_percent:<8.1f}%")
        
        print("-" * 80)
        print(f"Total records: {len(chart_entries)}")


class ChartCSVWriter:
    """Write chart data to CSV file."""
    
    @staticmethod
    def write_chart(chart_entries: List[RiskChartEntry], filename: str) -> None:
        """Write chart entries to CSV file."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if chart_entries:
                    fieldnames = list(chart_entries[0].to_dict().keys())
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    for entry in chart_entries:
                        writer.writerow(entry.to_dict())
            print(f"Risk chart data saved to: {filename}")
        except Exception as e:
            print(f"Error writing chart CSV: {e}")


class DataAnalysisService:
    """
    Main service class following Dependency Inversion Principle.
    Depends on abstractions (interfaces) rather than concrete implementations.
    """
    
    def __init__(self, 
                 data_reader: DataReader,
                 data_writer: DataWriter,
                 chart_generator: ChartGenerator,
                 report_generator: ReportGenerator,
                 app_filter: AppCodeFilter = None):
        self.data_reader = data_reader
        self.data_writer = data_writer
        self.chart_generator = chart_generator
        self.report_generator = report_generator
        self.app_filter = app_filter
    
    def analyze_data(self, source: str) -> tuple[List[InfrastructureRecord], Dict[str, int]]:
        """Main data analysis pipeline."""
        # Read data
        records = self.data_reader.read_data(source)
        if not records:
            return [], {}
        
        print(f"Loaded {len(records)} records from {source}")
        
        # Get unique records by AppCode (first occurrence)
        unique_records = {}
        for record in records:
            if record.app_code not in unique_records:
                unique_records[record.app_code] = record
        
        # Apply AppCode filter if configured
        if self.app_filter:
            filtered_records = {}
            for app_code, record in unique_records.items():
                if self.app_filter.is_allowed(app_code):
                    filtered_records[app_code] = record
            
            unique_records = filtered_records
            print(f"Filtered to {len(unique_records)} AppCodes based on Apps.csv")
        
        # Count AppCodes (from all records, not just unique)
        appcode_counts = AppCodeCounter.count_appcodes(records)
        
        # Filter counts to match filtered records
        if self.app_filter:
            filtered_counts = {}
            for app_code, count in appcode_counts.items():
                if self.app_filter.is_allowed(app_code):
                    filtered_counts[app_code] = count
            appcode_counts = filtered_counts
        
        unique_record_list = list(unique_records.values())
        
        print(f"Found {len(unique_record_list)} unique AppCodes")
        
        # Enhance records with calculated fields
        self._enhance_records(unique_record_list, appcode_counts)
        
        # Sort by AppCode
        unique_record_list.sort(key=lambda x: x.app_code)
        
        return unique_record_list, appcode_counts
    
    def _enhance_records(self, records: List[InfrastructureRecord], 
                        appcode_counts: Dict[str, int]) -> None:
        """Enhance records with calculated attributes."""
        # Add infrastructure counts and score numbers
        for record in records:
            record.total_infrastructure = appcode_counts[record.app_code]
            record.composite_score_number = CompositeScoreMapper.map_to_number(
                record.composite_score
            )
        
        # Calculate risk scores and percentages
        RiskCalculator.calculate_risk_scores(records)
        RiskCalculator.calculate_risk_percentages(records)
    
    def generate_full_report(self, records: List[InfrastructureRecord], 
                           appcode_counts: Dict[str, int]) -> None:
        """Generate complete analysis report."""
        # Generate summary report
        report = self.report_generator.generate_report(records, appcode_counts)
        print(report)
        
        # Generate and display risk chart
        chart_entries = self.chart_generator.generate_chart(records)
        ConsoleChartDisplay.display_chart(chart_entries)
        
        # Save chart to CSV
        ChartCSVWriter.write_chart(chart_entries, 'risk_chart.csv')
    
    def save_enhanced_data(self, records: List[InfrastructureRecord], 
                          destination: str) -> None:
        """Save enhanced data using the configured writer."""
        self.data_writer.write_data(records, destination)
        print(f"Enhanced data saved to: {destination}")