"""mapscale 的单元测试。"""

import contextlib
import io
import math
import os
import re
import tempfile
import unittest
from html.parser import HTMLParser
from typing import Any, List, Sequence, Tuple

from mapscale import (
    CM_PER_UNIT,
    UNITS,
    Question,
    __version__,
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
    render_demo,
    render_sheet,
    scale_denominator,
    validate_questions,
    write_text,
)
from mapscale.cli import main


class _TagCollector(HTMLParser):
    """收集标签名，用于确认 HTML/SVG 能被标准解析器接受。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.texts = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        self.tags.append(tag)

    def handle_data(self, data: str) -> None:
        self.texts.append(data)


def _parse_document(text: str) -> _TagCollector:
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector


def _run_cli(args: Sequence[str]) -> Tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()


class TestPackageSurface(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_units_constant(self) -> None:
        self.assertEqual(UNITS, ("cm", "m", "km"))

    def test_unit_centimeters(self) -> None:
        self.assertEqual(CM_PER_UNIT["cm"], 1.0)
        self.assertEqual(CM_PER_UNIT["m"], 100.0)
        self.assertEqual(CM_PER_UNIT["km"], 100000.0)


class TestParseNumber(unittest.TestCase):
    def test_integer_text(self) -> None:
        self.assertEqual(parse_number("100000", "比例尺分母"), 100000.0)

    def test_decimal_with_spaces(self) -> None:
        self.assertEqual(parse_number(" 3.5 ", "图上距离"), 3.5)

    def test_negative_is_allowed_here(self) -> None:
        self.assertEqual(parse_number("-2", "数值"), -2.0)

    def test_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("", "图上距离")

    def test_blank_text(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("   ", "图上距离")

    def test_not_a_number(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("三厘米", "图上距离")

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("nan", "图上距离")

    def test_infinity_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("inf", "图上距离")

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_number(True, "图上距离")

    def test_none_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_number(None, "图上距离")

    def test_thousands_separator_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_number("1,000", "图上距离")


class TestParseUnit(unittest.TestCase):
    def test_centimeter(self) -> None:
        self.assertEqual(parse_unit("cm"), "cm")

    def test_meter(self) -> None:
        self.assertEqual(parse_unit("m"), "m")

    def test_kilometer(self) -> None:
        self.assertEqual(parse_unit("km"), "km")

    def test_uppercase_normalized(self) -> None:
        self.assertEqual(parse_unit(" KM "), "km")

    def test_unknown_unit(self) -> None:
        with self.assertRaises(ValueError):
            parse_unit("inch")

    def test_empty_unit(self) -> None:
        with self.assertRaises(ValueError):
            parse_unit("")

    def test_non_text_unit(self) -> None:
        with self.assertRaises(ValueError):
            parse_unit(3)


class TestParseCountAndSeed(unittest.TestCase):
    def test_default_like_count(self) -> None:
        self.assertEqual(parse_count("8"), 8)

    def test_lower_bound(self) -> None:
        self.assertEqual(parse_count("1"), 1)

    def test_upper_bound(self) -> None:
        self.assertEqual(parse_count("50"), 50)

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_count("0")

    def test_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_count("51")

    def test_decimal_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_count("8.0")

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_count(True)

    def test_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_count("很多")

    def test_seed_zero_allowed(self) -> None:
        self.assertEqual(parse_seed("0"), 0)

    def test_negative_seed_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_seed("-1")


class TestActualDistance(unittest.TestCase):
    def test_typical(self) -> None:
        self.assertAlmostEqual(actual_distance(3.5, 100000), 3.5, places=9)

    def test_half_kilometer(self) -> None:
        self.assertAlmostEqual(actual_distance(1, 50000), 0.5, places=9)

    def test_large_scale(self) -> None:
        self.assertAlmostEqual(actual_distance(2, 200000), 4.0, places=9)

    def test_fractional_result(self) -> None:
        self.assertAlmostEqual(actual_distance(2.5, 100000), 2.5, places=9)

    def test_text_inputs(self) -> None:
        self.assertAlmostEqual(actual_distance("3.5", "100000"), 3.5, places=9)

    def test_zero_map_distance(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(0, 100000)

    def test_negative_map_distance(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(-3.5, 100000)

    def test_zero_scale(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(3.5, 0)

    def test_negative_scale(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(3.5, -100000)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(float("nan"), 100000)

    def test_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(3.5, float("inf"))

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(True, 100000)

    def test_overflow_rejected(self) -> None:
        with self.assertRaises(ValueError):
            actual_distance(1e308, 1e308)

    def test_result_is_finite(self) -> None:
        self.assertTrue(math.isfinite(actual_distance(8.0, 1000000)))


class TestScaleDenominator(unittest.TestCase):
    def test_typical(self) -> None:
        self.assertEqual(scale_denominator(3.5, 3.5), 100000)

    def test_one_to_one(self) -> None:
        self.assertEqual(scale_denominator(1, 1), 100000)

    def test_two_point_five(self) -> None:
        self.assertEqual(scale_denominator(2.5, 5), 200000)

    def test_rounds_down(self) -> None:
        self.assertEqual(scale_denominator(3, 1), 33333)

    def test_rounds_up(self) -> None:
        self.assertEqual(scale_denominator(7, 1), 14286)

    def test_text_inputs(self) -> None:
        self.assertEqual(scale_denominator("4", "4"), 100000)

    def test_zero_map_distance(self) -> None:
        with self.assertRaises(ValueError):
            scale_denominator(0, 3.5)

    def test_negative_real_distance(self) -> None:
        with self.assertRaises(ValueError):
            scale_denominator(3.5, -3.5)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            scale_denominator(float("nan"), 3.5)

    def test_too_small_denominator(self) -> None:
        with self.assertRaises(ValueError):
            scale_denominator(1e9, 1e-9)

    def test_result_is_int(self) -> None:
        self.assertIsInstance(scale_denominator(3.5, 3.5), int)


class TestConvert(unittest.TestCase):
    def test_cm_to_km(self) -> None:
        self.assertAlmostEqual(convert(2, "cm", "km", 50000), 1.0, places=9)

    def test_km_to_cm(self) -> None:
        self.assertAlmostEqual(convert(1, "km", "cm", 50000), 5e9, places=3)

    def test_cm_to_m(self) -> None:
        self.assertAlmostEqual(convert(100, "cm", "m", 100000), 100000.0, places=6)

    def test_m_to_km(self) -> None:
        self.assertAlmostEqual(convert(1, "m", "km", 10000), 10.0, places=9)

    def test_same_unit(self) -> None:
        self.assertAlmostEqual(convert(5, "cm", "cm", 1000), 5000.0, places=6)

    def test_uppercase_unit(self) -> None:
        self.assertAlmostEqual(convert(2, "CM", "KM", 50000), 1.0, places=9)

    def test_unknown_from_unit(self) -> None:
        with self.assertRaises(ValueError):
            convert(2, "inch", "km", 50000)

    def test_unknown_to_unit(self) -> None:
        with self.assertRaises(ValueError):
            convert(2, "cm", "里", 50000)

    def test_zero_value(self) -> None:
        with self.assertRaises(ValueError):
            convert(0, "cm", "km", 50000)

    def test_negative_value(self) -> None:
        with self.assertRaises(ValueError):
            convert(-2, "cm", "km", 50000)

    def test_zero_scale(self) -> None:
        with self.assertRaises(ValueError):
            convert(2, "cm", "km", 0)

    def test_nan_value(self) -> None:
        with self.assertRaises(ValueError):
            convert(float("nan"), "cm", "km", 50000)

    def test_overflow(self) -> None:
        with self.assertRaises(ValueError):
            convert(1e308, "km", "cm", 1e308)


class TestRenderBar(unittest.TestCase):
    def test_returns_svg_root(self) -> None:
        svg = render_bar(50000, 4)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))

    def test_has_namespace_and_role(self) -> None:
        svg = render_bar(50000, 4)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertIn('role="img"', svg)

    def test_parseable_by_html_parser(self) -> None:
        collector = _parse_document(render_bar(50000, 4))
        self.assertEqual(collector.tags[0], "svg")
        self.assertEqual(collector.tags.count("rect"), 5)

    def test_scale_label(self) -> None:
        svg = render_bar(50000, 4)
        self.assertIn("比例尺 1:50000", svg)

    def test_kilometer_labels(self) -> None:
        svg = render_bar(50000, 4)
        for label in ("0", "1", "2", "3", "4"):
            self.assertIn(">%s</text>" % label, svg)

    def test_unit_hint(self) -> None:
        self.assertIn("单位：千米", render_bar(50000, 4))

    def test_large_range_step(self) -> None:
        svg = render_bar(50000, 50)
        self.assertIn(">50</text>", svg)
        self.assertIn(">10</text>", svg)

    def test_small_range_step(self) -> None:
        svg = render_bar(50000, 0.3)
        self.assertIn(">0.3</text>", svg)

    def test_has_title_and_desc(self) -> None:
        svg = render_bar(50000, 4)
        self.assertIn("<title>", svg)
        self.assertIn("<desc>", svg)

    def test_zero_scale(self) -> None:
        with self.assertRaises(ValueError):
            render_bar(0, 4)

    def test_negative_length(self) -> None:
        with self.assertRaises(ValueError):
            render_bar(50000, -1)

    def test_zero_length(self) -> None:
        with self.assertRaises(ValueError):
            render_bar(50000, 0)

    def test_length_too_large(self) -> None:
        with self.assertRaises(ValueError):
            render_bar(50000, 10001)

    def test_nan_length(self) -> None:
        with self.assertRaises(ValueError):
            render_bar(50000, float("nan"))


class TestQuestions(unittest.TestCase):
    def test_single_question(self) -> None:
        questions = make_questions(1, 1)
        self.assertEqual(len(questions), 1)
        self.assertIsInstance(questions[0], Question)

    def test_fifty_questions(self) -> None:
        self.assertEqual(len(make_questions(50, 2)), 50)

    def test_all_kinds_present(self) -> None:
        kinds = set(question.kind for question in make_questions(8, 1))
        self.assertEqual(kinds, {"actual", "scale", "bar"})

    def test_same_seed_reproducible(self) -> None:
        self.assertEqual(make_questions(12, 7), make_questions(12, 7))

    def test_different_seed_differs(self) -> None:
        first = [item.prompt for item in make_questions(20, 1)]
        second = [item.prompt for item in make_questions(20, 2)]
        self.assertNotEqual(first, second)

    def test_count_zero(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(0, 1)

    def test_count_too_large(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_count_bool(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(True, 1)

    def test_seed_negative(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(5, -3)

    def test_actual_answer_matches_formula(self) -> None:
        for question in make_questions(30, 5):
            if question.kind != "actual":
                continue
            match = re.search(r"1:(\d+)", question.prompt)
            self.assertIsNotNone(match)
            denominator = int(match.group(1))
            map_match = re.search(r"相距 ([\d.]+) 厘米", question.prompt)
            self.assertIsNotNone(map_match)
            map_cm = float(map_match.group(1))
            expected = actual_distance(map_cm, denominator)
            self.assertEqual(question.answer, "%s 千米" % format_number(expected))

    def test_scale_answer_matches_formula(self) -> None:
        for question in make_questions(30, 6):
            if question.kind != "scale":
                continue
            match = re.search(r"图上 ([\d.]+) 厘米表示实际 ([\d.]+) 千米", question.prompt)
            self.assertIsNotNone(match)
            expected = scale_denominator(float(match.group(1)), float(match.group(2)))
            self.assertEqual(question.answer, "1:%d" % expected)

    def test_bar_answer_matches_formula(self) -> None:
        for question in make_questions(30, 8):
            if question.kind != "bar":
                continue
            match = re.search(r"代表实际 ([\d.]+) 千米", question.prompt)
            self.assertIsNotNone(match)
            expected = int(round(float(match.group(1)) * 100000))
            self.assertEqual(question.answer, "1:%d" % expected)


class TestValidateQuestions(unittest.TestCase):
    def test_returns_copy(self) -> None:
        questions = make_questions(3, 1)
        result = validate_questions(questions)
        self.assertIsNot(result, questions)
        self.assertEqual(result, questions)

    def test_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_questions([])

    def test_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_questions("题目")

    def test_wrong_item_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_questions([make_questions(1, 1)[0], "不是题目"])


class TestRenderSheet(unittest.TestCase):
    def _questions(self) -> List[Question]:
        return make_questions(6, 3)

    def test_document_header(self) -> None:
        html = render_sheet(self._questions())
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', html)

    def test_parseable_by_html_parser(self) -> None:
        collector = _parse_document(render_sheet(self._questions(), True))
        self.assertIn("html", collector.tags)
        self.assertIn("ol", collector.tags)
        self.assertIn("section", collector.tags)

    def test_question_count_in_meta(self) -> None:
        html = render_sheet(self._questions())
        self.assertIn("共 6 题", html)

    def test_each_question_rendered(self) -> None:
        questions = self._questions()
        html = render_sheet(questions)
        for question in questions:
            self.assertIn(question.prompt, html)

    def test_no_answers_by_default(self) -> None:
        self.assertNotIn("参考答案", render_sheet(self._questions()))

    def test_answers_page_when_requested(self) -> None:
        html = render_sheet(self._questions(), True)
        self.assertIn("参考答案", html)
        self.assertIn("解法：", html)

    def test_escapes_special_characters(self) -> None:
        question = Question("actual", "<b>图上</b> & 距离", "答案<1>", "解法&说明")
        html = render_sheet([question], True)
        self.assertIn("&lt;b&gt;图上&lt;/b&gt; &amp; 距离", html)
        self.assertNotIn("<b>图上</b>", html)
        self.assertIn("答案&lt;1&gt;", html)

    def test_empty_questions_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([])

    def test_non_question_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([("actual", "题", "答", "解")])

    def test_answers_must_be_bool(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(self._questions(), "yes")

    def test_question_list_items(self) -> None:
        collector = _parse_document(render_sheet(self._questions(), True))
        self.assertEqual(collector.tags.count("li"), 12)


class TestRenderDemo(unittest.TestCase):
    def test_document_header(self) -> None:
        self.assertTrue(render_demo().startswith("<!DOCTYPE html>"))

    def test_parseable_by_html_parser(self) -> None:
        collector = _parse_document(render_demo())
        self.assertIn("html", collector.tags)
        self.assertIn("style", collector.tags)

    def test_three_notations(self) -> None:
        html = render_demo()
        self.assertIn("数字式", html)
        self.assertIn("线段式", html)
        self.assertIn("文字式", html)

    def test_embeds_bar_svg(self) -> None:
        self.assertIn("<svg", render_demo())

    def test_states_formula(self) -> None:
        self.assertIn("比例尺 = 图上距离 : 实际距离 = 1 : N", render_demo())


class TestWriteText(unittest.TestCase):
    def test_writes_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.html")
            write_text(path, "<p>比例尺 1:100000</p>")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "<p>比例尺 1:100000</p>")

    def test_empty_path_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_text("", "内容")

    def test_directory_path_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                write_text(folder, "内容")

    def test_missing_parent_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "缺失目录", "out.html")
            with self.assertRaises(ValueError):
                write_text(path, "内容")

    def test_non_text_content_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.html")
            with self.assertRaises(ValueError):
                write_text(path, None)


class TestFormatting(unittest.TestCase):
    def test_format_number_integer(self) -> None:
        self.assertEqual(format_number(1000.0), "1000")

    def test_format_number_decimal(self) -> None:
        self.assertEqual(format_number(3.5), "3.5")

    def test_format_number_rounding(self) -> None:
        self.assertEqual(format_number(1.23456), "1.235")

    def test_format_denominator_integer(self) -> None:
        self.assertEqual(format_denominator(100000.0), "100000")

    def test_format_denominator_decimal(self) -> None:
        self.assertEqual(format_denominator(50000.5), "50000.500")

    def test_format_number_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            format_number(True)


class TestCliSuccess(unittest.TestCase):
    def test_calc(self) -> None:
        code, out, err = _run_cli(["calc", "--map", "3.5", "--scale", "100000"])
        self.assertEqual(code, 0)
        self.assertIn("实际距离：3.500 km", out)
        self.assertIn("比例尺：1:100000", out)
        self.assertEqual(err, "")

    def test_scale(self) -> None:
        code, out, _ = _run_cli(["scale", "--map", "3.5", "--real", "3.5"])
        self.assertEqual(code, 0)
        self.assertIn("比例尺：1:100000", out)

    def test_bar_stdout(self) -> None:
        code, out, _ = _run_cli(["bar", "--scale", "50000", "--length", "4"])
        self.assertEqual(code, 0)
        self.assertIn("<svg", out)
        self.assertIn("比例尺 1:50000", out)

    def test_bar_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bar.svg")
            code, out, _ = _run_cli(
                ["bar", "--scale", "50000", "--length", "4", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已写入", out)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertTrue(content.startswith("<svg"))
            _parse_document(content)

    def test_convert(self) -> None:
        code, out, _ = _run_cli(
            ["convert", "--value", "2", "--from", "cm", "--to", "km", "--scale", "50000"]
        )
        self.assertEqual(code, 0)
        self.assertIn("实际距离：1.000 km", out)

    def test_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            code, out, _ = _run_cli(
                ["sheet", "--count", "5", "--seed", "3", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("（5 题）", out)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("共 5 题", content)
            _parse_document(content)

    def test_sheet_with_answers(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            code, out, _ = _run_cli(
                ["sheet", "--count", "2", "--answers", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("含答案", out)
            with open(path, encoding="utf-8") as handle:
                self.assertIn("参考答案", handle.read())

    def test_sheet_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            code, _, _ = _run_cli(["sheet", "-o", path])
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as handle:
                self.assertIn("共 8 题", handle.read())

    def test_sheet_seed_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            first = os.path.join(folder, "a.html")
            second = os.path.join(folder, "b.html")
            _run_cli(["sheet", "--count", "6", "--seed", "9", "-o", first])
            _run_cli(["sheet", "--count", "6", "--seed", "9", "-o", second])
            with open(first, encoding="utf-8") as handle:
                text_a = handle.read()
            with open(second, encoding="utf-8") as handle:
                text_b = handle.read()
            self.assertEqual(text_a, text_b)

    def test_demo(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "demo.html")
            code, out, _ = _run_cli(["demo", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("已生成概念页", out)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("<svg", content)
            _parse_document(content)


class TestCliErrors(unittest.TestCase):
    def _assert_error(self, args: Sequence[str]) -> None:
        code, out, err = _run_cli(args)
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)
        self.assertEqual(out, "")

    def test_calc_zero(self) -> None:
        self._assert_error(["calc", "--map", "0", "--scale", "100000"])

    def test_calc_negative(self) -> None:
        self._assert_error(["calc", "--map", "-3.5", "--scale", "100000"])

    def test_calc_not_a_number(self) -> None:
        self._assert_error(["calc", "--map", "三", "--scale", "100000"])

    def test_calc_nan(self) -> None:
        self._assert_error(["calc", "--map", "nan", "--scale", "100000"])

    def test_calc_zero_scale(self) -> None:
        self._assert_error(["calc", "--map", "3.5", "--scale", "0"])

    def test_scale_zero_real(self) -> None:
        self._assert_error(["scale", "--map", "3.5", "--real", "0"])

    def test_scale_too_small(self) -> None:
        self._assert_error(["scale", "--map", "1000000", "--real", "0.000001"])

    def test_convert_unknown_unit(self) -> None:
        self._assert_error(
            ["convert", "--value", "2", "--from", "inch", "--to", "km", "--scale", "50000"]
        )

    def test_convert_zero_value(self) -> None:
        self._assert_error(
            ["convert", "--value", "0", "--from", "cm", "--to", "km", "--scale", "50000"]
        )

    def test_bar_zero_length(self) -> None:
        self._assert_error(["bar", "--scale", "50000", "--length", "0"])

    def test_bar_length_too_large(self) -> None:
        self._assert_error(["bar", "--scale", "50000", "--length", "20000"])

    def test_sheet_count_zero(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            self._assert_error(["sheet", "--count", "0", "-o", path])

    def test_sheet_count_too_large(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            self._assert_error(["sheet", "--count", "51", "-o", path])

    def test_sheet_bad_seed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sheet.html")
            self._assert_error(["sheet", "--seed", "-1", "-o", path])

    def test_sheet_unwritable_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "缺失目录", "sheet.html")
            self._assert_error(["sheet", "-o", path])

    def test_demo_unwritable_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "缺失目录", "demo.html")
            self._assert_error(["demo", "-o", path])


class TestCliArgparse(unittest.TestCase):
    def test_missing_required_argument(self) -> None:
        with self.assertRaises(SystemExit) as raising:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["calc", "--map", "3.5"])
        self.assertEqual(raising.exception.code, 2)

    def test_unknown_subcommand(self) -> None:
        with self.assertRaises(SystemExit) as raising:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["measure"])
        self.assertEqual(raising.exception.code, 2)

    def test_no_subcommand(self) -> None:
        with self.assertRaises(SystemExit) as raising:
            with contextlib.redirect_stderr(io.StringIO()):
                main([])
        self.assertEqual(raising.exception.code, 2)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as raising:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(raising.exception.code, 0)

    def test_version(self) -> None:
        buffer = io.StringIO()
        with self.assertRaises(SystemExit) as raising:
            with contextlib.redirect_stdout(buffer):
                main(["--version"])
        self.assertEqual(raising.exception.code, 0)
        self.assertIn("0.1.0", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
