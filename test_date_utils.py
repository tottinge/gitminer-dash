"""
Tests for the date_utils module.

This module contains tests for the date_utils module, including doctests
and additional test cases.
"""
import unittest
import doctest
from datetime import datetime, timedelta
from unittest.mock import patch

import date_utils


class TestDateUtils(unittest.TestCase):
    """Test cases for the date_utils module."""

    @patch('date_utils.datetime')
    def test_calculate_date_range_7_days(self, mock_datetime):
        """Test calculate_date_range with 'Last 7 days'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 7 days')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 10, 15).date())
        self.assertEqual((end.date() - begin.date()).days, 7)

    @patch('date_utils.datetime')
    def test_calculate_date_range_30_days(self, mock_datetime):
        """Test calculate_date_range with 'Last 30 days'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 30 days')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 9, 22).date())
        self.assertEqual((end.date() - begin.date()).days, 30)

    @patch('date_utils.datetime')
    def test_calculate_date_range_60_days(self, mock_datetime):
        """Test calculate_date_range with 'Last 60 days'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 60 days')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 8, 23).date())
        self.assertEqual((end.date() - begin.date()).days, 60)

    @patch('date_utils.datetime')
    def test_calculate_date_range_90_days(self, mock_datetime):
        """Test calculate_date_range with 'Last 90 days'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 90 days')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 7, 24).date())
        self.assertEqual((end.date() - begin.date()).days, 90)

    @patch('date_utils.datetime')
    def test_calculate_date_range_6_months(self, mock_datetime):
        """Test calculate_date_range with 'Last 6 Months'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 6 Months')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 4, 22).date())
        # Check that the month is decreased by 6, day remains the same
        self.assertEqual(begin.year, end.year)
        self.assertEqual(begin.month, end.month - 6)
        self.assertEqual(begin.day, end.day)

    @patch('date_utils.datetime')
    def test_calculate_date_range_1_year(self, mock_datetime):
        """Test calculate_date_range with 'Last 1 Year'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 1 Year')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2024, 10, 22).date())
        # Check that the year is decreased by 1, month and day remain the same
        self.assertEqual(begin.year, end.year - 1)
        self.assertEqual(begin.month, end.month)
        self.assertEqual(begin.day, end.day)

    @patch('date_utils.datetime')
    def test_calculate_date_range_5_years(self, mock_datetime):
        """Test calculate_date_range with 'Last 5 Years'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function
        begin, end = date_utils.calculate_date_range('Last 5 Years')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2020, 10, 22).date())
        # Check that the year is decreased by 5, month and day remain the same
        self.assertEqual(begin.year, end.year - 5)
        self.assertEqual(begin.month, end.month)
        self.assertEqual(begin.day, end.day)

    @patch('date_utils.datetime')
    def test_calculate_date_range_ever(self, mock_datetime):
        """Test calculate_date_range with 'Ever'."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # Call function
        begin, end = date_utils.calculate_date_range('Ever')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(1970, 1, 1).date())


    @patch('date_utils.datetime')
    def test_calculate_date_range_default(self, mock_datetime):
        """Test calculate_date_range with None or empty string."""
        # Setup mock
        mock_date = datetime(2025, 10, 22, 17, 59)
        mock_datetime.today.return_value = mock_date
        mock_datetime.astimezone = lambda x: x

        # Call function with None
        begin, end = date_utils.calculate_date_range(None)
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 9, 22).date())
        self.assertEqual((end.date() - begin.date()).days, 30)

        # Call function with empty string
        begin, end = date_utils.calculate_date_range('')
        
        # Assertions - compare only the date parts
        self.assertEqual(end.date(), mock_date.date())
        self.assertEqual(begin.date(), datetime(2025, 9, 22).date())
        self.assertEqual((end.date() - begin.date()).days, 30)


def load_tests(loader, tests, ignore):
    """Load doctests and return combined test suite."""
    tests.addTests(doctest.DocTestSuite(date_utils))
    return tests


if __name__ == '__main__':
    # Run doctests first
    doctest_results = doctest.testmod(date_utils)
    if doctest_results.failed == 0:
        print(f"All {doctest_results.attempted} doctests passed!")
    else:
        print(f"Failed {doctest_results.failed} out of {doctest_results.attempted} doctests.")
        exit(1)
    
    # Then run unittest tests
    unittest.main()