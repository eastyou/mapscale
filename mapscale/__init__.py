"""mapscale：初中地理比例尺工具。

对外提供实际距离计算、比例尺反求、线段比例尺 SVG、单位换算，
以及练习纸与概念页的 HTML 渲染。
"""

from .core import (
    CM_PER_UNIT,
    UNITS,
    Question,
    actual_distance,
    convert,
    format_denominator,
    format_number,
    make_questions,
    parse_count,
    parse_number,
    parse_seed,
    parse_unit,
    render_bar,
    scale_denominator,
    validate_questions,
)
from .paper import render_demo, render_sheet, write_text

__version__ = "0.1.0"

__all__ = [
    "CM_PER_UNIT",
    "UNITS",
    "Question",
    "__version__",
    "actual_distance",
    "convert",
    "format_denominator",
    "format_number",
    "make_questions",
    "parse_count",
    "parse_number",
    "parse_seed",
    "parse_unit",
    "render_bar",
    "render_demo",
    "render_sheet",
    "scale_denominator",
    "validate_questions",
    "write_text",
]
