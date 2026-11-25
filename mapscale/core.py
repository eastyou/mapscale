"""初中地理比例尺的核心计算与输入校验。

本模块只依赖标准库，所有对外函数都会对输入做严格校验：
布尔值不视为数值，非数字、空文本、NaN、Inf 与越界值一律抛出中文 ValueError。
"""

import math
import random
from typing import Any, List, NamedTuple, Sequence

# 1 个该单位等于多少厘米
CM_PER_UNIT = {"cm": 1.0, "m": 100.0, "km": 100000.0}
UNITS = ("cm", "m", "km")

MIN_COUNT = 1
MAX_COUNT = 50
MIN_SEED = 0
MAX_SEED = 2 ** 31 - 1
MAX_BAR_KM = 10000.0
MAX_SCALE_DENOMINATOR = 1e15

# 线段比例尺可选的刻度间隔（千米）
_STEPS = (
    0.1,
    0.2,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    20.0,
    25.0,
    50.0,
    100.0,
    200.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    2500.0,
    5000.0,
)


class Question(NamedTuple):
    """一道练习题的题干、答案与解法。"""

    kind: str
    prompt: str
    answer: str
    solution: str


def _as_float(value: Any, name: str) -> float:
    """把外部输入转换为有限浮点数，失败时抛出中文 ValueError。"""

    if isinstance(value, bool):
        raise ValueError("%s不能是布尔值" % name)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s不能为空" % name)
        try:
            number = float(text)
        except ValueError:
            raise ValueError("%s必须是数字，收到：%s" % (name, text))
    elif isinstance(value, (int, float)):
        number = float(value)
    else:
        raise ValueError("%s必须是数字，收到：%r" % (name, value))
    if not math.isfinite(number):
        raise ValueError("%s必须是有限数值，不能是 NaN 或无穷大" % name)
    return number


def _as_int(value: Any, name: str, minimum: int, maximum: int) -> int:
    """把外部输入转换为指定范围内的整数，失败时抛出中文 ValueError。"""

    if isinstance(value, bool):
        raise ValueError("%s不能是布尔值" % name)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s不能为空" % name)
        try:
            number = int(text)
        except ValueError:
            raise ValueError("%s必须是整数，收到：%s" % (name, text))
    elif isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("%s必须是有限数值" % name)
        if value != math.floor(value):
            raise ValueError("%s必须是整数，收到：%s" % (name, value))
        number = int(value)
    else:
        raise ValueError("%s必须是整数，收到：%r" % (name, value))
    if number < minimum or number > maximum:
        raise ValueError(
            "%s必须在 %d 到 %d 之间，收到：%d" % (name, minimum, maximum, number)
        )
    return number


def _require_positive(value: Any, name: str) -> float:
    """校验并返回正数。"""

    number = _as_float(value, name)
    if number <= 0.0:
        raise ValueError("%s必须大于 0，收到：%s" % (name, _trim(number)))
    return number


def _trim(value: float) -> str:
    """把浮点数格式化为最多 3 位小数并去掉多余的 0。"""

    text = "%.3f" % value
    text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def format_denominator(value: float) -> str:
    """把比例尺分母格式化为文本，整数分母不带小数点。"""

    number = _as_float(value, "比例尺分母")
    if abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return "%.3f" % number


def format_number(value: float) -> str:
    """把普通数值格式化为最多 3 位小数并去掉多余的 0。"""

    return _trim(_as_float(value, "数值"))


def parse_number(text: str, name: str) -> float:
    """解析命令行传入的数值文本。"""

    return _as_float(text, name)


def parse_unit(text: str) -> str:
    """校验并归一化长度单位，只接受 cm、m、km。"""

    if not isinstance(text, str):
        raise ValueError("单位必须是文本，收到：%r" % (text,))
    unit = text.strip().lower()
    if unit not in CM_PER_UNIT:
        raise ValueError("单位只支持 cm、m、km，收到：%s" % text)
    return unit


def parse_count(text: str, name: str = "题目数量") -> int:
    """解析题目数量，范围为 1 到 50。"""

    return _as_int(text, name, MIN_COUNT, MAX_COUNT)


def parse_seed(text: str, name: str = "随机种子") -> int:
    """解析随机种子，范围为 0 到 2^31-1。"""

    return _as_int(text, name, MIN_SEED, MAX_SEED)


def actual_distance(map_cm: float, scale_denominator: float) -> float:
    """由图上距离（厘米）与比例尺分母计算实际距离，单位为千米。"""

    map_value = _require_positive(map_cm, "图上距离")
    denominator = _require_positive(scale_denominator, "比例尺分母")
    if denominator > MAX_SCALE_DENOMINATOR:
        raise ValueError("比例尺分母过大，无法计算")
    result = map_value * denominator / CM_PER_UNIT["km"]
    if not math.isfinite(result):
        raise ValueError("实际距离超出可计算范围")
    if result > 1e15:
        raise ValueError("实际距离超出可计算范围")
    return result


def scale_denominator(map_cm: float, real_km: float) -> int:
    """由图上距离（厘米）与实际距离（千米）反求比例尺分母（四舍五入取整）。"""

    map_value = _require_positive(map_cm, "图上距离")
    real_value = _require_positive(real_km, "实际距离")
    raw = real_value * CM_PER_UNIT["km"] / map_value
    if not math.isfinite(raw):
        raise ValueError("比例尺分母超出可计算范围")
    if raw > MAX_SCALE_DENOMINATOR:
        raise ValueError("比例尺分母超出可计算范围")
    rounded = int(math.floor(raw + 0.5))
    if rounded <= 0:
        raise ValueError("比例尺分母过小，无法表示为 1:N 的形式")
    return rounded


def convert(
    value: float,
    from_unit: str,
    to_unit: str,
    scale_denominator: float,
) -> float:
    """按比例尺把图上长度换算为实际长度。

    value 是图上量得的长度，单位为 from_unit；
    返回值是实际长度，单位为 to_unit。
    """

    number = _require_positive(value, "长度")
    source = parse_unit(from_unit)
    target = parse_unit(to_unit)
    denominator = _require_positive(scale_denominator, "比例尺分母")
    if denominator > MAX_SCALE_DENOMINATOR:
        raise ValueError("比例尺分母过大，无法计算")
    real_cm = number * CM_PER_UNIT[source] * denominator
    result = real_cm / CM_PER_UNIT[target]
    if not math.isfinite(result) or result > 1e15:
        raise ValueError("换算结果超出可计算范围")
    return result


def _choose_step(max_km: float) -> float:
    """为线段比例尺挑选合适的刻度间隔，使刻段数不超过 6。"""

    for step in _STEPS:
        if max_km / step <= 6.0:
            return step
    return _STEPS[-1]


def render_bar(scale_denominator: float, max_km: float) -> str:
    """生成一条 0 到 max_km 的线段比例尺 SVG。"""

    import html as html_module

    denominator = _require_positive(scale_denominator, "比例尺分母")
    if denominator > MAX_SCALE_DENOMINATOR:
        raise ValueError("比例尺分母过大，无法绘制线段比例尺")
    top = _require_positive(max_km, "线段比例尺长度（千米）")
    if top > MAX_BAR_KM:
        raise ValueError("线段比例尺长度不能超过 %d 千米" % int(MAX_BAR_KM))

    step = _choose_step(top)
    ticks = int(math.ceil(top / step - 1e-9))
    if ticks < 1:
        ticks = 1

    left = 24.0
    chart_width = 720.0
    per_tick = chart_width / ticks
    width = 768
    height = 112
    km_per_cm = denominator / CM_PER_UNIT["km"]
    scale_text = format_denominator(denominator)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="线段比例尺">'
        % (width, height, width, height),
        "<title>线段比例尺 1:%s</title>" % html_module.escape(scale_text),
        "<desc>图上 1 厘米代表实际 %s 千米，刻度范围 0 到 %s 千米</desc>"
        % (html_module.escape(_trim(km_per_cm)), html_module.escape(_trim(ticks * step))),
        '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (width, height),
        '<text x="24" y="22" font-size="14" fill="#111111">比例尺 1:%s</text>'
        % html_module.escape(scale_text),
    ]

    for index in range(ticks):
        x = left + index * per_tick
        fill = "#1f2933" if index % 2 == 0 else "#ffffff"
        parts.append(
            '<rect x="%.2f" y="44" width="%.2f" height="18" fill="%s" '
            'stroke="#1f2933" stroke-width="1"/>' % (x, per_tick, fill)
        )

    for index in range(ticks + 1):
        x = left + index * per_tick
        label = _trim(index * step)
        parts.append(
            '<line x1="%.2f" y1="40" x2="%.2f" y2="64" stroke="#1f2933" '
            'stroke-width="1"/>' % (x, x)
        )
        parts.append(
            '<text x="%.2f" y="82" font-size="12" text-anchor="middle" '
            'fill="#111111">%s</text>' % (x, html_module.escape(label))
        )

    parts.append(
        '<text x="24" y="104" font-size="11" fill="#555555">单位：千米</text>'
    )
    parts.append(
        '<text x="744" y="104" font-size="11" text-anchor="end" '
        'fill="#555555">图上 1 厘米 = 实际 %s 千米</text>'
        % html_module.escape(_trim(km_per_cm))
    )
    parts.append("</svg>")
    return "\n".join(parts)


_MAP_CM_CHOICES = (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.5, 8.0)
_SCALE_CHOICES = (10000, 20000, 25000, 50000, 100000, 200000, 500000, 1000000)
_BAR_KM_PER_CM = (0.5, 1.0, 2.0, 2.5, 5.0, 10.0)
_KINDS = ("actual", "scale", "bar")


def _make_actual_question(rng: random.Random) -> Question:
    map_cm = rng.choice(_MAP_CM_CHOICES)
    denominator = rng.choice(_SCALE_CHOICES)
    real_km = actual_distance(map_cm, float(denominator))
    prompt = (
        "一幅地图的比例尺是 1:%d，图上量得两地相距 %s 厘米，"
        "两地的实际距离是多少千米？" % (denominator, _trim(map_cm))
    )
    solution = (
        "%s 厘米 × %d = %s 厘米 = %s 千米"
        % (_trim(map_cm), denominator, _trim(map_cm * denominator), _trim(real_km))
    )
    return Question("actual", prompt, "%s 千米" % _trim(real_km), solution)


def _make_scale_question(rng: random.Random) -> Question:
    map_cm = rng.choice(_MAP_CM_CHOICES)
    denominator = rng.choice(_SCALE_CHOICES)
    real_km = map_cm * denominator / CM_PER_UNIT["km"]
    prompt = (
        "图上 %s 厘米表示实际 %s 千米，求这幅地图的比例尺。"
        % (_trim(map_cm), _trim(real_km))
    )
    solution = (
        "%s 千米 = %s 厘米，%s ÷ %s = %d，比例尺是 1:%d"
        % (
            _trim(real_km),
            _trim(real_km * CM_PER_UNIT["km"]),
            _trim(real_km * CM_PER_UNIT["km"]),
            _trim(map_cm),
            denominator,
            denominator,
        )
    )
    return Question("scale", prompt, "1:%d" % denominator, solution)


def _make_bar_question(rng: random.Random) -> Question:
    km_per_cm = rng.choice(_BAR_KM_PER_CM)
    denominator = int(round(km_per_cm * CM_PER_UNIT["km"]))
    prompt = (
        "线段比例尺表示图上 1 厘米代表实际 %s 千米，请把它改写成数字比例尺。"
        % _trim(km_per_cm)
    )
    solution = (
        "1 千米 = 100000 厘米，%s × 100000 = %d，数字比例尺是 1:%d"
        % (_trim(km_per_cm), denominator, denominator)
    )
    return Question("bar", prompt, "1:%d" % denominator, solution)


def make_questions(count: int, seed: int) -> List[Question]:
    """按种子生成指定数量的比例尺练习题，结果可复现。"""

    total = _as_int(count, "题目数量", MIN_COUNT, MAX_COUNT)
    seed_value = _as_int(seed, "随机种子", MIN_SEED, MAX_SEED)
    rng = random.Random(seed_value)
    kinds = [_KINDS[index % len(_KINDS)] for index in range(total)]
    rng.shuffle(kinds)
    questions: List[Question] = []
    for kind in kinds:
        if kind == "actual":
            questions.append(_make_actual_question(rng))
        elif kind == "scale":
            questions.append(_make_scale_question(rng))
        else:
            questions.append(_make_bar_question(rng))
    return questions


def validate_questions(questions: Sequence[Question]) -> List[Question]:
    """校验题目序列，返回列表副本。"""

    if isinstance(questions, (str, bytes)):
        raise ValueError("题目列表必须是 Question 序列")
    if not isinstance(questions, (list, tuple)):
        raise ValueError("题目列表必须是 Question 序列")
    if not questions:
        raise ValueError("题目列表不能为空")
    result: List[Question] = []
    for index, item in enumerate(questions):
        if not isinstance(item, Question):
            raise ValueError("第 %d 道题不是 Question 对象" % (index + 1))
        result.append(item)
    return result
