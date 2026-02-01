import pytest

from shared.table_utils import (
    build_table_code,
    derive_area_code,
    parse_table_code,
    validate_table_code,
)
from shared.validation import ValidationError


@pytest.mark.parametrize(
    "area,number,expected",
    [
        ("B", 1, "B-M01"),
        ("PB", 2, "PB-M02"),
        ("T1", 10, "T1-M10"),
        ("abc", 99, "ABC-M99"),
    ],
)
def test_build_table_code_valid(area, number, expected):
    assert build_table_code(area, number) == expected


@pytest.mark.parametrize(
    "area,number",
    [
        ("", 1),  # Empty area code
        ("B", 0),  # Table number 0
        ("B", 100),  # Table number > 99
        ("@@", 5),  # Invalid characters
    ],
)
def test_build_table_code_invalid(area, number):
    with pytest.raises(ValidationError):
        build_table_code(area, number)


def test_validate_table_code_accepts_normalized():
    assert validate_table_code("b-m01") == "B-M01"
    assert parse_table_code("B-M01") == ("B", 1)


def test_derive_area_code():
    assert derive_area_code("Barra Norte") == "B"
    assert derive_area_code("vip terraza") == "V"
    assert derive_area_code("Zona") == "ZON"
    assert derive_area_code("", "G") == "G"
