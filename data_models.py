#!/usr/bin/env python3
"""
Data models for analytics application following SOLID principles.

Single Responsibility: Each class has one clear responsibility
Open/Closed: Classes are open for extension, closed for modification
Liskov Substitution: Interfaces can be substituted
Interface Segregation: Small, focused interfaces
Dependency Inversion: Depend on abstractions, not concretions
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class InfrastructureRecord:
    """Data model representing a single infrastructure record."""
    application_service: str
    app_code: str
    composite_score: str
    class_type: str
    total_infrastructure: int = 0
    composite_score_number: float = 0.0
    composite_risk_score: float = 0.0
    composite_risk_score_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary format."""
        return {
            'ApplicationService': self.application_service,
            'AppCode': self.app_code,
            'CompositeScore': self.composite_score,
            'Class': self.class_type,
            'TotalInfrastructure': self.total_infrastructure,
            'CompositeScoreNumber': self.composite_score_number,
            'CompositeRiskScore': self.composite_risk_score,
            'CompositeRiskScorePercent': self.composite_risk_score_percent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InfrastructureRecord':
        """Create record from dictionary."""
        return cls(
            application_service=data.get('ApplicationService', ''),
            app_code=data.get('AppCode', ''),
            composite_score=data.get('CompositeScore', ''),
            class_type=data.get('Class', '')
        )


@dataclass
class RiskChartEntry:
    """Data model for risk chart entries."""
    rank: int
    app_code: str
    composite_risk_score: float
    composite_risk_score_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary format."""
        return {
            'Rank': self.rank,
            'AppCode': self.app_code,
            'CompositeRiskScore': self.composite_risk_score,
            'CompositeRiskScorePercent': self.composite_risk_score_percent
        }


class CompositeScoreMapper:
    """Single Responsibility: Maps composite score text to numeric values."""
    
    SCORE_MAPPING = {
        'High': 3.0,
        'Moderate High': 2.5,
        'Moderate': 2.0,
        'Low': 1.0
    }
    
    @classmethod
    def map_to_number(cls, score: str) -> float:
        """Map composite score text to numeric value."""
        return cls.SCORE_MAPPING.get(score, 0.0)


class AppCodeCounter:
    """Single Responsibility: Counts occurrences of AppCodes."""
    
    @staticmethod
    def count_appcodes(records: List[InfrastructureRecord]) -> Dict[str, int]:
        """Count occurrences of each AppCode."""
        counts = {}
        for record in records:
            counts[record.app_code] = counts.get(record.app_code, 0) + 1
        return counts


class RiskCalculator:
    """Single Responsibility: Calculates risk scores and percentages."""
    
    @staticmethod
    def calculate_risk_scores(records: List[InfrastructureRecord]) -> None:
        """Calculate composite risk scores for all records."""
        for record in records:
            record.composite_risk_score = (
                record.composite_score_number * record.total_infrastructure
            )
    
    @staticmethod
    def calculate_risk_percentages(records: List[InfrastructureRecord]) -> None:
        """Calculate risk score percentages for all records."""
        total_risk = sum(record.composite_risk_score for record in records)
        
        if total_risk > 0:
            for record in records:
                record.composite_risk_score_percent = (
                    record.composite_risk_score / total_risk
                ) * 100
        else:
            for record in records:
                record.composite_risk_score_percent = 0.0


# Interfaces (Abstract Base Classes)

class DataReader(ABC):
    """Interface for reading data from various sources."""
    
    @abstractmethod
    def read_data(self, source: str) -> List[InfrastructureRecord]:
        """Read data from source and return list of records."""
        pass


class DataWriter(ABC):
    """Interface for writing data to various destinations."""
    
    @abstractmethod
    def write_data(self, records: List[InfrastructureRecord], destination: str) -> None:
        """Write records to destination."""
        pass


class ChartGenerator(ABC):
    """Interface for generating charts."""
    
    @abstractmethod
    def generate_chart(self, records: List[InfrastructureRecord]) -> List[RiskChartEntry]:
        """Generate chart entries from records."""
        pass


class ReportGenerator(ABC):
    """Interface for generating reports."""
    
    @abstractmethod
    def generate_report(self, records: List[InfrastructureRecord], 
                       appcode_counts: Dict[str, int]) -> str:
        """Generate report from records and counts."""
        pass