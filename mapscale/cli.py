"""mapscale 命令行入口。"""

import argparse
import sys
from typing import Optional, Sequence

from . import __version__
from .core import (
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
)
from .paper import render_demo, render_sheet, write_text


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切换到 UTF-8，失败时忽略。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        prog="mapscale",
        description="初中地理比例尺工具：求实际距离、反求比例尺、绘制线段比例尺、"
        "单位换算，并生成 A4 练习纸。",
    )
    parser.add_argument(
        "--version", action="version", version="mapscale " + __version__
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令")
    subparsers.required = True

    calc = subparsers.add_parser("calc", help="由图上距离与比例尺求实际距离")
    calc.add_argument("--map", required=True, metavar="CM", help="图上距离，单位厘米")
    calc.add_argument(
        "--scale", required=True, metavar="N", help="比例尺分母 N，例如 100000"
    )

    scale = subparsers.add_parser("scale", help="由图上距离与实际距离反求比例尺")
    scale.add_argument("--map", required=True, metavar="CM", help="图上距离，单位厘米")
    scale.add_argument("--real", required=True, metavar="KM", help="实际距离，单位千米")

    bar = subparsers.add_parser("bar", help="生成线段比例尺 SVG")
    bar.add_argument("--scale", required=True, metavar="N", help="比例尺分母 N")
    bar.add_argument(
        "--length", required=True, metavar="KM", help="线段比例尺表示的最大千米数"
    )
    bar.add_argument(
        "-o", "--output", metavar="PATH", help="SVG 输出路径，省略时打印到终端"
    )

    conv = subparsers.add_parser("convert", help="按比例尺在 cm、m、km 之间换算")
    conv.add_argument("--value", required=True, metavar="V", help="图上量得的长度")
    conv.add_argument(
        "--from",
        dest="from_unit",
        required=True,
        metavar="UNIT",
        help="图上长度的单位：cm、m、km",
    )
    conv.add_argument(
        "--to",
        dest="to_unit",
        required=True,
        metavar="UNIT",
        help="实际长度的单位：cm、m、km",
    )
    conv.add_argument("--scale", required=True, metavar="N", help="比例尺分母 N")

    sheet = subparsers.add_parser("sheet", help="生成 A4 练习纸")
    sheet.add_argument("--count", default="8", metavar="N", help="题目数量，1 到 50，默认 8")
    sheet.add_argument("--seed", default="1", metavar="S", help="随机种子，默认 1")
    sheet.add_argument("-o", "--output", required=True, metavar="PATH", help="HTML 输出路径")
    sheet.add_argument("--answers", action="store_true", help="附加参考答案页")

    demo = subparsers.add_parser("demo", help="生成比例尺概念卡片页")
    demo.add_argument("-o", "--output", required=True, metavar="PATH", help="HTML 输出路径")

    return parser


def _run(args: argparse.Namespace) -> int:
    """根据解析结果执行子命令。"""

    command = args.command
    if command == "calc":
        map_cm = parse_number(args.map, "图上距离")
        denominator = parse_number(args.scale, "比例尺分母")
        real_km = actual_distance(map_cm, denominator)
        print("图上距离：%s cm" % format_number(map_cm))
        print("比例尺：1:%s" % format_denominator(denominator))
        print("实际距离：%.3f km" % real_km)
        return 0

    if command == "scale":
        map_cm = parse_number(args.map, "图上距离")
        real_km = parse_number(args.real, "实际距离")
        denominator = scale_denominator(map_cm, real_km)
        print("图上距离：%s cm" % format_number(map_cm))
        print("实际距离：%s km" % format_number(real_km))
        print("比例尺：1:%d" % denominator)
        return 0

    if command == "bar":
        denominator = parse_number(args.scale, "比例尺分母")
        length = parse_number(args.length, "线段比例尺长度（千米）")
        svg = render_bar(denominator, length)
        if args.output:
            write_text(args.output, svg + "\n")
            print("已写入：%s" % args.output)
        else:
            print(svg)
        return 0

    if command == "convert":
        value = parse_number(args.value, "长度")
        denominator = parse_number(args.scale, "比例尺分母")
        from_unit = parse_unit(args.from_unit)
        to_unit = parse_unit(args.to_unit)
        result = convert(value, from_unit, to_unit, denominator)
        print("图上距离：%s %s" % (format_number(value), from_unit))
        print("比例尺：1:%s" % format_denominator(denominator))
        print("实际距离：%.3f %s" % (result, to_unit))
        return 0

    if command == "sheet":
        count = parse_count(args.count)
        seed = parse_seed(args.seed)
        questions = make_questions(count, seed)
        document = render_sheet(questions, args.answers)
        write_text(args.output, document)
        suffix = "，含答案" if args.answers else ""
        print("已生成练习纸：%s（%d 题%s）" % (args.output, len(questions), suffix))
        return 0

    if command == "demo":
        document = render_demo()
        write_text(args.output, document)
        print("已生成概念页：%s" % args.output)
        return 0

    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数：成功返回 0，输入非法或写文件失败返回 2。"""

    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
