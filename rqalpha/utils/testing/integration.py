import os
from warnings import warn
import json
from io import StringIO
from typing import Tuple, Optional

import pandas as pd
from pandas import DataFrame
from pandas.testing import assert_frame_equal

from rqalpha import run_func

__all__ = ['StructuredTextFormat', 'assert_result']


class StructuredTextFormat:
    """
    A specialized text format for serializing structured data containing DataFrames and dictionaries.
    
    The StructuredTextFormat (STF) is a general-purpose serializer for structured data that automatically
    handles pandas DataFrames and Python dictionaries with full type preservation.
    
    Format Specification:
    ====================
    
    The format uses an ini-like structure with sections, where each section contains:
    1. Section header: [section_name]  (case-sensitive)
    2. Object type: DataFrame, dict, list, etc.
    3. Metadata: Compact JSON with structural information
    4. Content: Serialized data (CSV for DataFrames, JSON for other types)
    5. Empty line separator between sections
    
    Example:
    --------
    [portfolio]
    DataFrame
    {"shape":[3,2],"dtypes":{"price":"float64","volume":"int64"},"index_dtype":"datetime64[ns]","index_name":"date","columns":["price","volume"]}
    ,price,volume
    2025-01-01 00:00:00,100.5,1000
    2025-01-02 00:00:00,101.2,1500
    2025-01-03 00:00:00,99.8,800
    
    [summary]
    dict
    {}
    {"total_returns":0.15,"volatility":0.25,"sharpe":0.8}
    
    Features:
    ---------
    - Human-readable text format
    - Preserves DataFrame dtypes and index information
    - Compact metadata representation
    - Supports empty DataFrames
    - General-purpose: no business logic hardcoded
    - Round-trip serialization fidelity
    """
    
    @staticmethod
    def _dataframe_to_csv_with_metadata(df: DataFrame) -> Tuple[str, dict, str]:
        """Convert DataFrame to CSV string with metadata"""
        object_type = "DataFrame"
        metadata = {
            "shape": list(df.shape),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "index_dtype": str(df.index.dtype),
            "index_name": df.index.name,
            "columns": list(df.columns),
        }
        if df.empty:
            csv_data = "# Empty DataFrame"
        else:
            csv_buffer = StringIO()
            # Convert index to string to avoid datetime serialization issues
            df_copy = df.copy()
            df_copy.index = [str(idx) for idx in df_copy.index]
            df_copy.to_csv(csv_buffer, index=True)
            csv_data = csv_buffer.getvalue().strip()
        
        return object_type, metadata, csv_data

    @staticmethod
    def _csv_to_dataframe_with_metadata(object_type: str, metadata: dict, csv_data: str) -> DataFrame:
        """Convert CSV string back to DataFrame using metadata"""
        if csv_data.strip() == "# Empty DataFrame":
            # Create empty DataFrame with correct structure
            df = DataFrame(columns=metadata.get("columns", []))
            # Try to restore column dtypes for empty DataFrame
            for col, dtype_str in metadata.get("dtypes", {}).items():
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(dtype_str)
                    except (ValueError, TypeError):
                        pass  # Keep original dtype if conversion fails
            # Restore empty index with correct dtype and name
            index_dtype = metadata.get("index_dtype")
            if index_dtype:
                try:
                    if isinstance(index_dtype, str) and index_dtype.startswith("datetime64"):
                        df.index = pd.DatetimeIndex([], dtype=index_dtype)
                    else:
                        df.index = pd.Index([], dtype=index_dtype)
                except (ValueError, TypeError):
                    # Fallback to default empty index
                    df.index = pd.Index([])
            if metadata.get("index_name"):
                df.index.name = metadata["index_name"]
            return df
        
        csv_buffer = StringIO(csv_data)
        df = pd.read_csv(csv_buffer, index_col=0, dtype={'order_book_id': 'str'})
        
        # Restore dtypes
        for col, dtype_str in metadata.get("dtypes", {}).items():
            if col in df.columns:
                try:
                    # Handle special cases
                    if dtype_str.startswith('datetime64'):
                        df[col] = pd.to_datetime(df[col])
                    elif dtype_str == 'category':
                        df[col] = df[col].astype('category')
                    elif dtype_str in ['int64', 'int32', 'float64', 'float32', 'bool', 'object']:
                        df[col] = df[col].astype(dtype_str)
                except (ValueError, TypeError):
                    pass  # Keep original dtype if conversion fails
        
        # Restore index dtype and name
        index_dtype = metadata.get("index_dtype")
        if index_dtype:
            try:
                if isinstance(index_dtype, str) and index_dtype.startswith('datetime64'):
                    df.index = pd.to_datetime(df.index)
                else:
                    df.index = df.index.astype(index_dtype)
            except (ValueError, TypeError):
                # Keep original index dtype if conversion fails
                pass
        
        # Restore index name
        if metadata.get("index_name"):
            df.index.name = metadata["index_name"]
        
        return df


    @classmethod
    def dumps(cls, obj: dict) -> str:
        """
        Serialize dictionary to STF string.
        
        Args:
            obj: Dictionary to serialize. Each key-value pair becomes a section.
            
        Returns:
            STF formatted string
        """
        sections = []
        
        for section_name, section_data in obj.items():
            section_lines = [f"[{section_name}]"]
            
            if isinstance(section_data, DataFrame):
                # DataFrame as CSV with metadata
                object_type, metadata, csv_data = cls._dataframe_to_csv_with_metadata(section_data)
                section_lines.append(object_type)
                section_lines.append(json.dumps(metadata, separators=(',', ':')))
                # Add CSV data lines (may be multiple lines)
                section_lines.extend(csv_data.split('\n'))
            else:
                # Other data as JSON with metadata
                object_type = type(section_data).__name__
                metadata = {}
                section_lines.append(object_type)
                section_lines.append(json.dumps(metadata, separators=(',', ':')))
                section_lines.append(json.dumps(section_data, separators=(',', ':'), default=str, indent=4))
            
            sections.append('\n'.join(section_lines))
        
        # Join sections with empty lines
        return '\n\n'.join(sections)

    @classmethod
    def loads(cls, s: str) -> dict:
        """
        Deserialize STF string to dictionary.
        
        Args:
            s: STF formatted string
            
        Returns:
            Deserialized dictionary
        """
        # Split into sections by empty lines
        sections = s.split('\n\n')
        
        result = {}
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            if len(lines) < 3:  # Must have at least: header, type, metadata
                raise ValueError(f"Invalid section: {section}")
                
            # Parse section header [section_name]
            header = lines[0]
            if not header.startswith('[') or not header.endswith(']'):
                raise ValueError(f"Invalid section header: {header}")
                
            section_name = header[1:-1]  # Remove brackets
                
            # Parse object type (second line)
            object_type = lines[1].strip()
            
            # Parse metadata (third line)
            metadata = json.loads(lines[2])
            
            # Parse data content (fourth line and beyond)
            data_lines = lines[3:]
            data_content = '\n'.join(data_lines)
            
            # Parse data based on object type
            if object_type == "DataFrame":
                # Parse DataFrame with metadata
                result[section_name] = cls._csv_to_dataframe_with_metadata(object_type, metadata, data_content)
            elif object_type == "dict":
                # Parse JSON dict
                result[section_name] = json.loads(data_content)
            else:
                raise NotImplementedError(f"Unsupported object type: {object_type}")
        
        return result

    @classmethod  
    def dump(cls, obj: dict, fp) -> None:
        """
        Serialize object to STF format and write to file.
        
        Args:
            obj: Dictionary to serialize
            fp: File-like object to write to
        """
        fp.write(cls.dumps(obj))

    @classmethod
    def load(cls, fp) -> dict:
        """
        Load and deserialize STF format from file.
        
        Args:
            fp: File-like object to read from
            
        Returns:
            Deserialized dictionary
        """
        return cls.loads(fp.read())


def _filter_integration_result(result: dict) -> dict:
    """Filter and prepare integration test result for STF serialization"""
    if "sys_analyser" not in result:
        return result
    
    sys_analyser = result["sys_analyser"]
    
    # Keep specified fields
    keep_fields = [
        'trades', 'stock_positions', 'future_positions', 
        'stock_account', 'future_account', 'portfolio', 'summary'
    ]
    
    filtered_data = {}
    
    for field in keep_fields:
        if field in sys_analyser:
            if field == 'summary':
                # Filter summary to keep only important fields
                important_fields = [
                    # Basic info
                    'strategy_name', 'start_date', 'end_date', 'starting_cash', 'total_value', 'cash',
                    # Returns
                    'total_returns', 'annualized_returns', 'unit_net_value',
                    # Excess
                    'excess_returns', 'excess_annual_returns', 'excess_max_drawdown', 'excess_sharpe',
                    # Risk metrics
                    'volatility', 'max_drawdown', 'sharpe', 'sortino',
                    # Other important metrics
                    'win_rate', 'alpha', 'beta', 'information_ratio', 'tracking_error'
                ]
                filtered_data[field] = {k: v for k, v in sys_analyser[field].items() if k in important_fields}
            else:
                filtered_data[field] = sys_analyser[field]
    
    return filtered_data


def _assert_dafaframe(result: DataFrame, expected_result: DataFrame, exclude_columns: Optional[list] = None):
    if result.empty:
        assert expected_result.empty
        return
    if exclude_columns:
        result = result.drop(exclude_columns, axis=1)
        expected_result = expected_result.drop(exclude_columns, axis=1)
    assert_frame_equal(result, expected_result, atol=1e-7)


def _assert_result(result: dict, expected_result: dict):
    actual = _filter_integration_result(result)
    expected = expected_result
    
    # Both should be DataFrames now
    _assert_dafaframe(actual["trades"], expected["trades"], exclude_columns=["order_id", "exec_id"])

    for field in [
        "stock_positions",
        "future_positions",
        "stock_account",
        "future_account",
        "portfolio",
    ]:
        if field in expected:
            _assert_dafaframe(actual[field], expected[field])
    
    for summary_field in expected["summary"]:
        actual_val = actual["summary"][summary_field]
        expected_val = expected["summary"][summary_field]
        
        # Handle NaN values - use math.isnan for proper comparison
        import math
        if (isinstance(actual_val, float) and math.isnan(actual_val)) and \
           (isinstance(expected_val, float) and math.isnan(expected_val)):
            continue
        
        if isinstance(expected_val, float):
            assert math.isclose(actual_val, expected_val, rel_tol=1e-7)
        else:   
            assert actual_val == expected_val


def assert_result(result: dict, expected_result_file: str):
    if not os.path.exists(expected_result_file):
        warn(f"Result file {expected_result_file} not found, creating it")
        # Filter result using business logic before serialization
        filtered_result = _filter_integration_result(result)
        with open(expected_result_file, "w", encoding='utf-8') as f:
            StructuredTextFormat.dump(filtered_result, f)
        return
    
    with open(expected_result_file, "r", encoding='utf-8') as f:
        expected_result = StructuredTextFormat.load(f)
    
    _assert_result(result, expected_result)    
