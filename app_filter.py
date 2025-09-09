#!/usr/bin/env python3
"""
AppCode filtering utility following SOLID principles.

Provides functionality to filter data based on AppCodes from Apps.csv
"""

import csv
from typing import List, Set
from abc import ABC, abstractmethod


class AppCodeFilter(ABC):
    """Interface for filtering AppCodes."""
    
    @abstractmethod
    def load_allowed_appcodes(self, source: str) -> Set[str]:
        """Load allowed AppCodes from source."""
        pass
    
    @abstractmethod
    def is_allowed(self, app_code: str) -> bool:
        """Check if AppCode is allowed."""
        pass


class CSVAppCodeFilter(AppCodeFilter):
    """Concrete implementation for filtering based on CSV file."""
    
    def __init__(self):
        self.allowed_appcodes: Set[str] = set()
    
    def load_allowed_appcodes(self, source: str) -> Set[str]:
        """Load allowed AppCodes from CSV file."""
        try:
            with open(source, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                appcodes = set()
                for row in reader:
                    if 'AppCode' in row and row['AppCode'].strip():
                        appcodes.add(row['AppCode'].strip())
                
                self.allowed_appcodes = appcodes
                print(f"Loaded {len(appcodes)} allowed AppCodes from {source}")
                return appcodes
                
        except FileNotFoundError:
            print(f"Warning: Apps filter file {source} not found. No filtering will be applied.")
            return set()
        except Exception as e:
            print(f"Error reading apps filter file: {e}")
            return set()
    
    def is_allowed(self, app_code: str) -> bool:
        """Check if AppCode is in the allowed list."""
        # If no filter is loaded, allow all AppCodes
        if not self.allowed_appcodes:
            return True
        
        return app_code.strip() in self.allowed_appcodes
    
    def get_allowed_appcodes(self) -> Set[str]:
        """Get the set of allowed AppCodes."""
        return self.allowed_appcodes.copy()