#!/usr/bin/env python3
"""
Unit tests for AppCode filtering functionality.
"""

import unittest
import tempfile
import os
import csv
from app_filter import CSVAppCodeFilter
from data_processors import DataAnalysisService, CSVDataReader, CSVDataWriter, RiskChartGenerator, ConsoleReportGenerator


class TestAppCodeFilter(unittest.TestCase):
    """Test AppCode filtering functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test Apps.csv
        self.apps_data = [
            ['AppCode'],
            ['APP1'],
            ['APP2'],
            ['APP3']
        ]
        
        self.apps_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(self.apps_file)
        writer.writerows(self.apps_data)
        self.apps_file.close()
        
        # Create test sampleData.csv with mixed AppCodes
        self.sample_data = [
            ['ApplicationService', 'AppCode', 'CompositeScore', 'Class'],
            ['Test App 1', 'APP1', 'High', 'Server'],      # Should be included
            ['Test App 2', 'APP2', 'Moderate', 'Database'], # Should be included
            ['Test App 3', 'APP3', 'Low', 'Service'],       # Should be included
            ['Test App 4', 'APP4', 'High', 'VM'],           # Should be filtered out
            ['Test App 5', 'APP5', 'Moderate', 'Container'] # Should be filtered out
        ]
        
        self.sample_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(self.sample_file)
        writer.writerows(self.sample_data)
        self.sample_file.close()
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.apps_file.name):
            os.unlink(self.apps_file.name)
        if os.path.exists(self.sample_file.name):
            os.unlink(self.sample_file.name)
    
    def test_csv_appcode_filter_loading(self):
        """Test loading AppCodes from CSV file."""
        app_filter = CSVAppCodeFilter()
        allowed_codes = app_filter.load_allowed_appcodes(self.apps_file.name)
        
        expected_codes = {'APP1', 'APP2', 'APP3'}
        self.assertEqual(allowed_codes, expected_codes)
        self.assertEqual(app_filter.get_allowed_appcodes(), expected_codes)
    
    def test_csv_appcode_filter_is_allowed(self):
        """Test filtering logic."""
        app_filter = CSVAppCodeFilter()
        app_filter.load_allowed_appcodes(self.apps_file.name)
        
        # Should be allowed
        self.assertTrue(app_filter.is_allowed('APP1'))
        self.assertTrue(app_filter.is_allowed('APP2'))
        self.assertTrue(app_filter.is_allowed('APP3'))
        
        # Should not be allowed
        self.assertFalse(app_filter.is_allowed('APP4'))
        self.assertFalse(app_filter.is_allowed('APP5'))
        self.assertFalse(app_filter.is_allowed('UNKNOWN'))
    
    def test_csv_appcode_filter_empty_file(self):
        """Test behavior with non-existent filter file."""
        app_filter = CSVAppCodeFilter()
        allowed_codes = app_filter.load_allowed_appcodes('nonexistent.csv')
        
        self.assertEqual(allowed_codes, set())
        # Should allow all when no filter is loaded
        self.assertTrue(app_filter.is_allowed('ANY_CODE'))
    
    def test_data_analysis_service_with_filter(self):
        """Test DataAnalysisService with AppCode filtering."""
        # Create service with filter
        app_filter = CSVAppCodeFilter()
        app_filter.load_allowed_appcodes(self.apps_file.name)
        
        service = DataAnalysisService(
            data_reader=CSVDataReader(),
            data_writer=CSVDataWriter(),
            chart_generator=RiskChartGenerator(),
            report_generator=ConsoleReportGenerator(),
            app_filter=app_filter
        )
        
        # Analyze data
        records, counts = service.analyze_data(self.sample_file.name)
        
        # Should only have 3 records (APP1, APP2, APP3)
        self.assertEqual(len(records), 3)
        
        # Check that only allowed AppCodes are present
        app_codes_in_results = {record.app_code for record in records}
        expected_codes = {'APP1', 'APP2', 'APP3'}
        self.assertEqual(app_codes_in_results, expected_codes)
        
        # Check counts are filtered too
        self.assertEqual(set(counts.keys()), expected_codes)
        self.assertNotIn('APP4', counts)
        self.assertNotIn('APP5', counts)
    
    def test_data_analysis_service_without_filter(self):
        """Test DataAnalysisService without AppCode filtering."""
        # Create service without filter
        service = DataAnalysisService(
            data_reader=CSVDataReader(),
            data_writer=CSVDataWriter(),
            chart_generator=RiskChartGenerator(),
            report_generator=ConsoleReportGenerator(),
            app_filter=None
        )
        
        # Analyze data
        records, counts = service.analyze_data(self.sample_file.name)
        
        # Should have all 5 records
        self.assertEqual(len(records), 5)
        
        # Check that all AppCodes are present
        app_codes_in_results = {record.app_code for record in records}
        expected_codes = {'APP1', 'APP2', 'APP3', 'APP4', 'APP5'}
        self.assertEqual(app_codes_in_results, expected_codes)
    
    def test_risk_chart_filtering(self):
        """Test that risk chart is also filtered."""
        # Create service with filter
        app_filter = CSVAppCodeFilter()
        app_filter.load_allowed_appcodes(self.apps_file.name)
        
        service = DataAnalysisService(
            data_reader=CSVDataReader(),
            data_writer=CSVDataWriter(),
            chart_generator=RiskChartGenerator(),
            report_generator=ConsoleReportGenerator(),
            app_filter=app_filter
        )
        
        # Analyze data
        records, _ = service.analyze_data(self.sample_file.name)
        
        # Generate chart
        chart_entries = service.chart_generator.generate_chart(records)
        
        # Should only have 3 chart entries
        self.assertEqual(len(chart_entries), 3)
        
        # Check that only allowed AppCodes are in chart
        app_codes_in_chart = {entry.app_code for entry in chart_entries}
        expected_codes = {'APP1', 'APP2', 'APP3'}
        self.assertEqual(app_codes_in_chart, expected_codes)
    
    def test_filter_with_whitespace(self):
        """Test filtering handles whitespace correctly."""
        # Create Apps.csv with whitespace
        whitespace_data = [
            ['AppCode'],
            [' APP1 '],  # Leading/trailing spaces
            ['APP2\t'],   # Tab character
            [' APP3']     # Leading space
        ]
        
        whitespace_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(whitespace_file)
        writer.writerows(whitespace_data)
        whitespace_file.close()
        
        try:
            app_filter = CSVAppCodeFilter()
            app_filter.load_allowed_appcodes(whitespace_file.name)
            
            # Should handle whitespace correctly
            self.assertTrue(app_filter.is_allowed('APP1'))
            self.assertTrue(app_filter.is_allowed('APP2'))
            self.assertTrue(app_filter.is_allowed('APP3'))
            
            # Check that whitespace is stripped
            allowed_codes = app_filter.get_allowed_appcodes()
            self.assertEqual(allowed_codes, {'APP1', 'APP2', 'APP3'})
        
        finally:
            if os.path.exists(whitespace_file.name):
                os.unlink(whitespace_file.name)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)