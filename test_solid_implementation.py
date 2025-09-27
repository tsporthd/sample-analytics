#!/usr/bin/env python3
"""
Unit tests for SOLID-compliant data analysis implementation.

Tests the refactored code to ensure SOLID principles are followed
while maintaining functionality.
"""

import unittest
import tempfile
import os
import csv
from typing import List, Dict, Any

from data_models import (
    InfrastructureRecord, RiskChartEntry, CompositeScoreMapper,
    AppCodeCounter, RiskCalculator, DataReader, DataWriter, 
    ChartGenerator, ReportGenerator
)
from data_processors import (
    CSVDataReader, CSVDataWriter, RiskChartGenerator, 
    ConsoleReportGenerator, DataAnalysisService
)


class TestDataModels(unittest.TestCase):
    """Test data models and utility classes."""
    
    def test_infrastructure_record_creation(self):
        """Test InfrastructureRecord creation and conversion."""
        record = InfrastructureRecord(
            application_service="Test App",
            app_code="TEST",
            composite_score="High",
            class_type="Server"
        )
        
        self.assertEqual(record.app_code, "TEST")
        self.assertEqual(record.composite_score, "High")
        self.assertEqual(record.total_infrastructure, 0)  # default
    
    def test_record_dict_conversion(self):
        """Test record to/from dictionary conversion."""
        original_data = {
            'ApplicationService': 'Test App',
            'AppCode': 'TEST',
            'CompositeScore': 'High',
            'Class': 'Server'
        }
        
        # Test from_dict
        record = InfrastructureRecord.from_dict(original_data)
        self.assertEqual(record.app_code, 'TEST')
        self.assertEqual(record.composite_score, 'High')
        
        # Test to_dict
        converted_data = record.to_dict()
        self.assertEqual(converted_data['AppCode'], 'TEST')
        self.assertEqual(converted_data['CompositeScore'], 'High')
    
    def test_composite_score_mapper(self):
        """Test CompositeScoreMapper follows single responsibility."""
        self.assertEqual(CompositeScoreMapper.map_to_number('High'), 3.0)
        self.assertEqual(CompositeScoreMapper.map_to_number('Moderate High'), 2.5)
        self.assertEqual(CompositeScoreMapper.map_to_number('Moderate'), 2.0)
        self.assertEqual(CompositeScoreMapper.map_to_number('Low'), 1.0)
        self.assertEqual(CompositeScoreMapper.map_to_number('Unknown'), 0.0)
    
    def test_appcode_counter(self):
        """Test AppCodeCounter follows single responsibility."""
        records = [
            InfrastructureRecord("App1", "A1", "High", "Server"),
            InfrastructureRecord("App1", "A1", "High", "Server"),
            InfrastructureRecord("App2", "A2", "Low", "DB"),
        ]
        
        counts = AppCodeCounter.count_appcodes(records)
        expected = {"A1": 2, "A2": 1}
        self.assertEqual(counts, expected)
    
    def test_risk_calculator(self):
        """Test RiskCalculator follows single responsibility."""
        records = [
            InfrastructureRecord("App1", "A1", "High", "Server"),
            InfrastructureRecord("App2", "A2", "Low", "DB"),
        ]
        
        # Set up test data
        records[0].composite_score_number = 3.0
        records[0].total_infrastructure = 5
        records[1].composite_score_number = 1.0
        records[1].total_infrastructure = 2
        
        # Test risk score calculation
        RiskCalculator.calculate_risk_scores(records)
        self.assertEqual(records[0].composite_risk_score, 15.0)  # 3.0 * 5
        self.assertEqual(records[1].composite_risk_score, 2.0)   # 1.0 * 2
        
        # Test percentage calculation
        RiskCalculator.calculate_risk_percentages(records)
        total_risk = 15.0 + 2.0  # 17.0
        expected_pct_1 = (15.0 / 17.0) * 100
        expected_pct_2 = (2.0 / 17.0) * 100
        
        self.assertAlmostEqual(records[0].composite_risk_score_percent, expected_pct_1, places=5)
        self.assertAlmostEqual(records[1].composite_risk_score_percent, expected_pct_2, places=5)

    def test_risk_calculator_grouped_percentages(self):
        """Test RiskCalculator calculates percentages within groups."""
        records = [
            InfrastructureRecord("App1", "A1", "High", "Server"),
            InfrastructureRecord("App2", "A2", "High", "Server"),
            InfrastructureRecord("App3", "A3", "Low", "DB"),
            InfrastructureRecord("App4", "A4", "Low", "DB"),
        ]

        # Set up test data - two High (3.0) and two Low (1.0)
        records[0].composite_score_number = 3.0
        records[0].total_infrastructure = 10
        records[1].composite_score_number = 3.0
        records[1].total_infrastructure = 20
        records[2].composite_score_number = 1.0
        records[2].total_infrastructure = 30
        records[3].composite_score_number = 1.0
        records[3].total_infrastructure = 40

        # Calculate risk scores
        RiskCalculator.calculate_risk_scores(records)

        # Risk scores: 30.0, 60.0, 30.0, 40.0
        self.assertEqual(records[0].composite_risk_score, 30.0)
        self.assertEqual(records[1].composite_risk_score, 60.0)
        self.assertEqual(records[2].composite_risk_score, 30.0)
        self.assertEqual(records[3].composite_risk_score, 40.0)

        # Calculate grouped percentages
        RiskCalculator.calculate_risk_percentages_by_group(records)

        # High group total: 30.0 + 60.0 = 90.0
        # Low group total: 30.0 + 40.0 = 70.0
        high_group_pct_1 = (30.0 / 90.0) * 100  # 33.33%
        high_group_pct_2 = (60.0 / 90.0) * 100  # 66.67%
        low_group_pct_1 = (30.0 / 70.0) * 100   # 42.86%
        low_group_pct_2 = (40.0 / 70.0) * 100   # 57.14%

        self.assertAlmostEqual(records[0].composite_risk_score_percent, high_group_pct_1, places=2)
        self.assertAlmostEqual(records[1].composite_risk_score_percent, high_group_pct_2, places=2)
        self.assertAlmostEqual(records[2].composite_risk_score_percent, low_group_pct_1, places=2)
        self.assertAlmostEqual(records[3].composite_risk_score_percent, low_group_pct_2, places=2)


class TestDataProcessors(unittest.TestCase):
    """Test concrete implementations of interfaces."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = [
            ['ApplicationService', 'AppCode', 'CompositeScore', 'Class'],
            ['Test App 1', 'APP1', 'High', 'Server'],
            ['Test App 1', 'APP1', 'High', 'Server'],
            ['Test App 2', 'APP2', 'Moderate', 'Database'],
        ]
        
        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(self.temp_file)
        writer.writerows(self.test_data)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_csv_data_reader(self):
        """Test CSVDataReader implements DataReader interface."""
        reader = CSVDataReader()
        
        # Test it implements the interface
        self.assertIsInstance(reader, DataReader)
        
        # Test functionality
        records = reader.read_data(self.temp_file.name)
        self.assertEqual(len(records), 3)  # 3 data rows
        self.assertEqual(records[0].app_code, 'APP1')
    
    def test_csv_data_reader_error_handling(self):
        """Test CSVDataReader handles errors gracefully."""
        reader = CSVDataReader()
        records = reader.read_data('nonexistent_file.csv')
        self.assertEqual(records, [])
    
    def test_csv_data_writer(self):
        """Test CSVDataWriter implements DataWriter interface."""
        writer = CSVDataWriter()
        
        # Test it implements the interface
        self.assertIsInstance(writer, DataWriter)
        
        # Test functionality without exclude_appcode
        records = [
            InfrastructureRecord("Test", "T1", "High", "Server")
        ]
        
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        output_file.close()
        
        try:
            writer.write_data(records, output_file.name)
            self.assertTrue(os.path.exists(output_file.name))
            
            # Verify content includes AppCode
            with open(output_file.name, 'r') as f:
                content = f.read()
                self.assertIn('Test', content)
                self.assertIn('T1', content)
                self.assertIn('AppCode', content)  # Should include AppCode column
        finally:
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_csv_data_writer_exclude_appcode(self):
        """Test CSVDataWriter with exclude_appcode option."""
        writer = CSVDataWriter()
        
        records = [
            InfrastructureRecord("Test App", "T1", "High", "Server")
        ]
        
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        output_file.close()
        
        try:
            # Write with exclude_appcode=True
            writer.write_data(records, output_file.name, exclude_appcode=True)
            self.assertTrue(os.path.exists(output_file.name))
            
            # Verify AppCode column is excluded
            with open(output_file.name, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Should not contain AppCode
                self.assertNotIn('AppCode', headers)
                
                # Should contain other columns
                self.assertIn('ApplicationService', headers)
                self.assertIn('CompositeScore', headers)
                self.assertIn('Class', headers)
                
                # Verify data
                row = next(reader)
                self.assertEqual(row['ApplicationService'], 'Test App')
                self.assertEqual(row['CompositeScore'], 'High')
                self.assertEqual(row['Class'], 'Server')
                
        finally:
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_risk_chart_generator(self):
        """Test RiskChartGenerator implements ChartGenerator interface."""
        generator = RiskChartGenerator()
        
        # Test it implements the interface
        self.assertIsInstance(generator, ChartGenerator)
        
        # Test functionality
        records = [
            InfrastructureRecord("App1", "A1", "High", "Server"),
            InfrastructureRecord("App2", "A2", "Low", "DB"),
        ]

        # Set required fields for risk chart generation
        records[0].composite_score_number = 3.0
        records[0].composite_risk_score = 15.0
        records[0].composite_risk_score_percent = 75.0
        records[1].composite_score_number = 1.0
        records[1].composite_risk_score = 5.0
        records[1].composite_risk_score_percent = 25.0
        
        chart_entries = generator.generate_chart(records)

        self.assertEqual(len(chart_entries), 2)
        self.assertEqual(chart_entries[0].rank, 1)
        self.assertEqual(chart_entries[0].application_service, "App1")
        self.assertEqual(chart_entries[0].app_code, "A1")  # Higher composite score first
        self.assertEqual(chart_entries[0].composite_score_number, 3.0)
        self.assertEqual(chart_entries[1].rank, 2)
        self.assertEqual(chart_entries[1].application_service, "App2")
        self.assertEqual(chart_entries[1].app_code, "A2")
        self.assertEqual(chart_entries[1].composite_score_number, 1.0)
    
    def test_console_report_generator(self):
        """Test ConsoleReportGenerator implements ReportGenerator interface."""
        generator = ConsoleReportGenerator()
        
        # Test it implements the interface
        self.assertIsInstance(generator, ReportGenerator)
        
        # Test functionality
        records = [InfrastructureRecord("Test", "T1", "High", "Server")]
        appcode_counts = {"T1": 1}
        
        report = generator.generate_report(records, appcode_counts)
        
        self.assertIn("DATA ANALYSIS SUMMARY", report)
        self.assertIn("Total records: 1", report)
        self.assertIn("T1: 1 items", report)


class TestSOLIDPrinciples(unittest.TestCase):
    """Test that SOLID principles are properly implemented."""
    
    def test_liskov_substitution_principle(self):
        """Test that implementations can be substituted for interfaces."""
        # Any DataReader implementation should work
        readers = [CSVDataReader()]
        
        for reader in readers:
            self.assertIsInstance(reader, DataReader)
            # Interface contract: read_data should return List[InfrastructureRecord]
            # Test with invalid file to ensure it returns empty list, not crashes
            result = reader.read_data('nonexistent.csv')
            self.assertIsInstance(result, list)
    
    def test_interface_segregation_principle(self):
        """Test that interfaces are focused and segregated."""
        # DataReader only has read_data method
        reader_methods = [method for method in dir(DataReader) 
                         if not method.startswith('_') and callable(getattr(DataReader, method))]
        self.assertEqual(len(reader_methods), 1)
        self.assertIn('read_data', reader_methods)
        
        # DataWriter only has write_data method
        writer_methods = [method for method in dir(DataWriter) 
                         if not method.startswith('_') and callable(getattr(DataWriter, method))]
        self.assertEqual(len(writer_methods), 1)
        self.assertIn('write_data', writer_methods)
    
    def test_dependency_inversion_principle(self):
        """Test that DataAnalysisService depends on abstractions."""
        # Create mock implementations (could be any implementation)
        reader = CSVDataReader()
        writer = CSVDataWriter()
        chart_generator = RiskChartGenerator()
        report_generator = ConsoleReportGenerator()
        
        # Service should accept any implementations of the interfaces
        service = DataAnalysisService(reader, writer, chart_generator, report_generator)
        
        # Test that service stores the abstractions, not concrete types
        self.assertIsInstance(service.data_reader, DataReader)
        self.assertIsInstance(service.data_writer, DataWriter)
        self.assertIsInstance(service.chart_generator, ChartGenerator)
        self.assertIsInstance(service.report_generator, ReportGenerator)


class TestDataAnalysisService(unittest.TestCase):
    """Test the main service class."""
    
    def setUp(self):
        """Set up test data and service."""
        self.test_data = [
            ['ApplicationService', 'AppCode', 'CompositeScore', 'Class'],
            ['Test App 1', 'APP1', 'High', 'Server'],
            ['Test App 1', 'APP1', 'High', 'Server'],
            ['Test App 2', 'APP2', 'Moderate', 'Database'],
        ]
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(self.temp_file)
        writer.writerows(self.test_data)
        self.temp_file.close()
        
        # Create service with real implementations
        self.service = DataAnalysisService(
            data_reader=CSVDataReader(),
            data_writer=CSVDataWriter(),
            chart_generator=RiskChartGenerator(),
            report_generator=ConsoleReportGenerator()
        )
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_analyze_data_integration(self):
        """Test full data analysis integration."""
        records, counts = self.service.analyze_data(self.temp_file.name)
        
        # Should return unique records by AppCode
        self.assertEqual(len(records), 2)  # APP1 and APP2
        
        # Should count all occurrences
        expected_counts = {'APP1': 2, 'APP2': 1}
        self.assertEqual(counts, expected_counts)
        
        # Records should be enhanced with calculated fields
        for record in records:
            self.assertGreater(record.total_infrastructure, 0)
            self.assertGreaterEqual(record.composite_score_number, 0)
            self.assertGreaterEqual(record.composite_risk_score, 0)
            self.assertGreaterEqual(record.composite_risk_score_percent, 0)
    
    def test_save_enhanced_data_integration(self):
        """Test saving enhanced data."""
        records, _ = self.service.analyze_data(self.temp_file.name)
        
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        output_file.close()
        
        try:
            self.service.save_enhanced_data(records, output_file.name)
            self.assertTrue(os.path.exists(output_file.name))
            
            # Verify enhanced data is saved with AppCode
            with open(output_file.name, 'r') as f:
                reader = csv.DictReader(f)
                saved_records = list(reader)
                
                self.assertEqual(len(saved_records), 2)
                self.assertIn('AppCode', reader.fieldnames)
                self.assertIn('TotalInfrastructure', reader.fieldnames)
                self.assertIn('CompositeRiskScore', reader.fieldnames)
        finally:
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_save_enhanced_data_exclude_appcode(self):
        """Test saving enhanced data without AppCode column."""
        records, _ = self.service.analyze_data(self.temp_file.name)
        
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        output_file.close()
        
        try:
            # Save with exclude_appcode=True
            self.service.save_enhanced_data(records, output_file.name, exclude_appcode=True)
            self.assertTrue(os.path.exists(output_file.name))
            
            # Verify AppCode column is excluded
            with open(output_file.name, 'r') as f:
                reader = csv.DictReader(f)
                saved_records = list(reader)
                
                self.assertEqual(len(saved_records), 2)
                self.assertNotIn('AppCode', reader.fieldnames)
                self.assertIn('ApplicationService', reader.fieldnames)
                self.assertIn('TotalInfrastructure', reader.fieldnames)
                self.assertIn('CompositeRiskScore', reader.fieldnames)
                
                # Verify data integrity without AppCode
                for record in saved_records:
                    self.assertIn('ApplicationService', record)
                    self.assertIn('CompositeScore', record)
                    self.assertNotIn('AppCode', record)
        finally:
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)