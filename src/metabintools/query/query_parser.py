"""
Query parser for filtering bins using expressions.

Supports filtering by bin properties, statistics, and taxonomy.
Examples:
    - group == "high_quality"
    - completeness >= 90 and contamination <= 5
    - phylum == "Bacteroidetes" or phylum == "Firmicutes"
    - length > 1000000
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from metabintools.dataclasses.bin import Bin
from metabintools.dataclasses.bin_statistics import BinStatistics
from metabintools.dataclasses.bin_taxonomy import BinTaxonomy


@dataclass
class FilterContext:
    """Context for evaluating filter expressions."""

    bin: Bin

    def __getattr__(self, name: str) -> Any:
        """
        Resolve attribute access to bin properties.

        Tries to resolve in this order:
        1. Direct bin properties (id, group, contigs, import_name)
        2. Statistics fields
        3. Taxonomy fields
        """
        if hasattr(self.bin, name):
            return getattr(self.bin, name)

        if self.bin.statistics and hasattr(self.bin.statistics, name):
            return getattr(self.bin.statistics, name)

        if self.bin.taxonomy and hasattr(self.bin.taxonomy, name):
            return getattr(self.bin.taxonomy, name)

        raise AttributeError(f"Bin has no attribute '{name}'")


class ContextDict(dict):
    """
    Dict-like object that delegates to FilterContext for attribute access.

    Args:
        context: The FilterContext to delegate to.
    """

    def __init__(self, context: FilterContext) -> None:
        self.context = context
        super().__init__()

    def __contains__(self, key: object) -> bool:
        """
        Return whether the given key is a valid attribute of the context.

        Args:
            key: The key to check for validity.

        Returns:
            True if the key is a valid attribute of the context, False otherwise.
        """
        if not isinstance(key, str):
            return False
        try:
            getattr(self.context, key)
            return True
        except AttributeError:
            return False

    def __getitem__(self, key: object) -> Any:
        """
        Return the value of the given key from the context.

        Args:
            key: The key to look up in the context.

        Raises:
            KeyError: If the key is not a valid attribute of the context.

        Returns:
            The value of the given key from the context.
        """
        if not isinstance(key, str):
            raise KeyError(key)
        try:
            return getattr(self.context, key)
        except AttributeError:
            raise KeyError(key)


def parse_filter_query(query: str) -> Callable[[Bin], bool]:
    """
    Parse a filter query string and return a filter function.

    Args:
        query: A filter expression using Python comparison operators
               and boolean logic (and, or, not)

    Returns:
        A callable that takes a Bin and returns True if it matches the filter

    Raises:
        ValueError: If the query is invalid
    """
    # Sanitize the query to prevent injection
    # Only allow alphanumeric, spaces, operators, quotes, parentheses
    allowed_pattern = r'^[a-zA-Z0-9_\s=!<>()&|"\'.,\-+]*$'
    if not re.match(allowed_pattern, query):
        raise ValueError(
            "Invalid characters in filter query. Only alphanumeric, operators, "
            "quotes, and parentheses are allowed."
        )

    try:
        code = compile(query, "<filter>", "eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid filter query: {e}")

    def filter_func(bin: Bin) -> bool:
        context = FilterContext(bin=bin)
        try:
            # Use eval with restricted globals/locals for safety
            # We only allow access to the context object and built-in functions
            result = eval(
                code,
                {
                    "__builtins__": {
                        "True": True,
                        "False": False,
                        "None": None,
                    }
                },
                ContextDict(context),
            )
            return bool(result)
        except (AttributeError, TypeError, NameError, KeyError) as e:
            raise ValueError(f"Error evaluating filter: {e}")

    return filter_func


def get_available_fields() -> dict[str, str]:
    """
    Get a dictionary of all available fields that can be used in filters.

    Dynamically extracts field descriptions from Pydantic model schemas.

    Returns:
        Dictionary mapping field names to their descriptions
    """
    fields = {}

    # Bin properties
    for field_name, field_info in Bin.model_fields.items():
        if field_name not in ["statistics", "taxonomy"] and field_info.description:
            fields[field_name] = field_info.description

    # Statistics fields
    if BinStatistics.model_fields:
        for field_name, field_info in BinStatistics.model_fields.items():
            if field_info.description:
                fields[field_name] = field_info.description

    # Taxonomy fields
    if BinTaxonomy.model_fields:
        for field_name, field_info in BinTaxonomy.model_fields.items():
            if field_info.description:
                fields[field_name] = field_info.description

    return fields


def parse_rename_template(template: str) -> Callable[[Bin], str]:
    """
    Parse a rename template string and return a function that generates bin names.

    Allows injecting field values into the template using the format `{field_name}`.
    Field names are resolved from bin properties, statistics, and taxonomy.

    Args:
        template: A template string with field placeholders like "bin_{taxon_name}"

    Returns:
        A callable that takes a Bin and returns the generated name

    Raises:
        ValueError: If the template contains invalid field references
    """
    # Find all field placeholders in the template
    placeholder_pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    placeholders = re.findall(placeholder_pattern, template)

    def rename_func(bin: Bin) -> str:
        context = FilterContext(bin=bin)
        result = template

        for placeholder in placeholders:
            try:
                value = getattr(context, placeholder)
                # Convert value to string, replacing None or empty values with "NA"
                str_value = str(value) if value is not None else "NA"
                result = result.replace(f"{{{placeholder}}}", str_value)
            except AttributeError:
                # Return "NA" if field doesn't exist
                result = result.replace(f"{{{placeholder}}}", "NA")

        return result

    return rename_func
