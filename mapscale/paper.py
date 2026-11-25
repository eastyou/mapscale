"""A4 练习纸与概念卡片页的 HTML 渲染。

不使用 xml.etree，全部通过字符串拼接配合 html.escape 生成。
"""

import html
from typing import List, Sequence

from .core import Question, render_bar, validate_questions

_SHEET_CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Songti SC", "STSong", "SimSun", serif;
  color: #111111;
  font-size: 12pt;
  line-height: 1.9;
}
h1 { font-size: 18pt; text-align: center; margin: 0 0 4pt; letter-spacing: 2pt; }
h2 { font-size: 14pt; margin: 0 0 10pt; }
.meta { text-align: center; font-size: 10pt; color: #555555; margin-bottom: 14pt; }
ol { padding-left: 1.6em; margin: 0; }
li { margin-bottom: 14pt; }
.stem { text-align: justify; }
.writing { border-bottom: 1px solid #bbbbbb; height: 20pt; margin-top: 2pt; }
.answers { page-break-before: always; break-before: page; }
.answer { margin-bottom: 10pt; }
.answer-text { font-weight: bold; }
.solution { color: #444444; font-size: 10.5pt; }
footer { margin-top: 18pt; font-size: 9pt; color: #777777; text-align: center; }
@media print { body { font-size: 12pt; } }
"""

_DEMO_CSS = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 16px;
  background: #f5f6f7;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #1f2933;
  line-height: 1.7;
}
h1 { font-size: 22px; margin: 0 0 4px; }
.lead { color: #52606d; font-size: 13px; margin: 0 0 18px; }
.card {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 14px;
}
.card h2 { font-size: 16px; margin: 0 0 8px; color: #243b53; }
.card p { margin: 4px 0; font-size: 13px; }
.formula {
  font-family: "SFMono-Regular", "Menlo", monospace;
  background: #eef2f6;
  border-radius: 4px;
  padding: 6px 10px;
  display: inline-block;
  margin: 6px 0;
}
.example { border-left: 3px solid #486581; padding-left: 10px; color: #334e68; }
.bar { margin-top: 8px; }
@media print {
  body { background: #ffffff; padding: 0; }
  .card { border-color: #bbbbbb; page-break-inside: avoid; }
}
"""


def _page(title: str, css: str, body: str) -> str:
    """拼装完整的 HTML 文档。"""

    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>\n%s</style>\n"
        "</head>\n"
        "<body>\n%s\n</body>\n"
        "</html>\n" % (html.escape(title), css, body)
    )


def render_sheet(questions: Sequence[Question], answers: bool = False) -> str:
    """把题目列表渲染为 A4 练习纸 HTML，可选附加答案页。"""

    items = validate_questions(questions)
    if not isinstance(answers, bool):
        raise ValueError("答案开关必须是布尔值")
    lines: List[str] = [
        "<h1>比例尺练习纸</h1>",
        '<p class="meta">共 %d 题　姓名：__________　班级：__________</p>' % len(items),
        "<ol>",
    ]
    for question in items:
        lines.append('<li class="question">')
        lines.append('<div class="stem">%s</div>' % html.escape(question.prompt))
        lines.append('<div class="writing"></div>')
        lines.append("</li>")
    lines.append("</ol>")
    lines.append("<footer>比例尺 = 图上距离 : 实际距离</footer>")
    if answers:
        lines.append('<section class="answers">')
        lines.append("<h2>参考答案</h2>")
        lines.append('<ol class="answer-list">')
        for question in items:
            lines.append('<li class="answer">')
            lines.append(
                '<div class="answer-text">答案：%s</div>' % html.escape(question.answer)
            )
            lines.append(
                '<div class="solution">解法：%s</div>' % html.escape(question.solution)
            )
            lines.append("</li>")
        lines.append("</ol>")
        lines.append("</section>")
    body = "\n".join(lines)
    return _page("比例尺练习纸", _SHEET_CSS, body)


def render_demo() -> str:
    """渲染比例尺概念与三种表示法的卡片页。"""

    bar = render_bar(100000.0, 4.0)
    lines: List[str] = [
        "<h1>认识比例尺</h1>",
        '<p class="lead">比例尺表示图上距离与实际距离的比，'
        "常见表示法有三种：数字式、线段式和文字式。</p>",
        '<section class="card">',
        "<h2>一、比例尺的含义</h2>",
        '<p class="formula">比例尺 = 图上距离 : 实际距离 = 1 : N</p>',
        "<p>比例尺 1:100000 表示图上 1 厘米相当于实际 100000 厘米，也就是 1 千米。</p>",
        '<p class="example">换算时先统一单位：1 千米 = 100000 厘米。</p>',
        "</section>",
        '<section class="card">',
        "<h2>二、数字式</h2>",
        '<p class="formula">1 : 100000</p>',
        "<p>数字式用比的形式书写，前项通常为 1，后项越大比例尺越小。</p>",
        "</section>",
        '<section class="card">',
        "<h2>三、线段式</h2>",
        '<p>在线段比例尺上，每一段代表一定的实际距离，可以直接用直尺量算。</p>',
        '<div class="bar">%s</div>' % bar,
        "</section>",
        '<section class="card">',
        "<h2>四、文字式</h2>",
        '<p class="formula">图上 1 厘米代表实际 1 千米</p>',
        "<p>文字式用一句话说明图上距离与实际距离的关系，便于口述和阅读。</p>",
        "</section>",
        '<section class="card">',
        "<h2>五、例题</h2>",
        "<p>在比例尺为 1:100000 的地图上，量得甲、乙两地相距 3.5 厘米，"
        "求两地的实际距离。</p>",
        '<p class="example">3.5 厘米 × 100000 = 350000 厘米 = 3.5 千米。</p>',
        "<p>反过来，若图上 3.5 厘米表示实际 3.5 千米，"
        "则比例尺分母为 3.5 × 100000 ÷ 3.5 = 100000。</p>",
        "</section>",
    ]
    body = "\n".join(lines)
    return _page("比例尺概念卡片", _DEMO_CSS, body)


def write_text(path: str, text: str) -> None:
    """以 UTF-8 写入文本文件，失败时转换为中文 ValueError。"""

    if not isinstance(path, str):
        raise ValueError("输出路径必须是文本")
    target = path.strip()
    if not target:
        raise ValueError("输出路径不能为空")
    if not isinstance(text, str):
        raise ValueError("写入内容必须是文本")
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (target, exc))
