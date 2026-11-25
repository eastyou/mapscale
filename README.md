# mapscale

[![CI](https://github.com/eastyou/mapscale/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/mapscale/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

面向初中地理「比例尺」知识点的命令行工具，零第三方依赖，只使用 Python 标准库。它可以求实际距离、反求比例尺、绘制线段比例尺 SVG、在 cm/m/km 之间换算，还能生成 A4 练习纸与概念卡片页，方便课堂讲评与作业布置。

## 特性

- `calc` 子命令：已知图上距离（厘米）与比例尺分母，按「实际距离 = 图上距离 × 分母 ÷ 100000」求实际距离（千米，保留 3 位小数）。
- `scale` 子命令：已知图上距离与实际距离，反求比例尺分母，四舍五入为整数并输出 `1:N` 形式。
- `bar` 子命令：生成带刻度、黑白相间线段与公里标注的线段比例尺 SVG，可打印到终端或写入文件。
- `convert` 子命令：按比例尺在 `cm`、`m`、`km` 之间换算，单位大小写不敏感。
- `sheet` 子命令：按种子生成可复现的 A4 练习纸，题型覆盖求实际距离、求比例尺、改写线段比例尺，可选答案页。
- `demo` 子命令：生成数字式、线段式、文字式三种表示法的概念卡片页。
- 严格的输入校验：布尔值不当作数值，非数字、空文本、NaN、Inf、零与负数都会给出中文错误提示。
- 纯字符串拼接生成 HTML 与 SVG，所有动态文本都经过 `html.escape`，不使用 `xml.etree`。

## 安装

需要 Python 3.9 或更高版本。在仓库根目录执行：

```bash
python3 -m pip install .
```

也可以不安装，直接以模块方式运行：

```bash
python3 -m mapscale --help
```

## 使用

求实际距离：图上 3.5 厘米，比例尺 1:100000。

```bash
$ mapscale calc --map 3.5 --scale 100000
图上距离：3.5 cm
比例尺：1:100000
实际距离：3.500 km
```

由图上距离与实际距离反求比例尺：

```bash
$ mapscale scale --map 3.5 --real 3.5
图上距离：3.5 cm
实际距离：3.5 km
比例尺：1:100000
```

按比例尺换算单位：图上 2 厘米，比例尺 1:50000，换算成千米。

```bash
$ mapscale convert --value 2 --from cm --to km --scale 50000
图上距离：2 cm
比例尺：1:50000
实际距离：1.000 km
```

生成线段比例尺 SVG（省略 `-o` 时把 SVG 打印到终端）：

```bash
$ mapscale bar --scale 50000 --length 4 -o bar.svg
已写入：bar.svg
```

生成 8 道练习题并附答案页：

```bash
$ mapscale sheet --count 8 --seed 1 -o sheet.html --answers
已生成练习纸：sheet.html（8 题，含答案）
```

生成概念卡片页：

```bash
$ mapscale demo -o demo.html
已生成概念页：demo.html
```

输入非法时返回退出码 2，并在标准错误输出中文提示：

```bash
$ mapscale calc --map 0 --scale 100000
错误：图上距离必须大于 0，收到：0
$ echo $?
2
```

### 参数

| 参数 | 所属子命令 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `calc` | 子命令 | 是 | 由图上距离与比例尺求实际距离 |
| `scale` | 子命令 | 是 | 由图上距离与实际距离反求比例尺 |
| `bar` | 子命令 | 是 | 生成线段比例尺 SVG |
| `convert` | 子命令 | 是 | 按比例尺在 cm、m、km 之间换算 |
| `sheet` | 子命令 | 是 | 生成 A4 练习纸 |
| `demo` | 子命令 | 是 | 生成比例尺概念卡片页 |
| `--map CM` | `calc`、`scale` | 是 | 图上距离，单位厘米，必须大于 0 |
| `--scale N` | `calc`、`bar`、`convert` | 是 | 比例尺分母 N，例如 100000，必须大于 0 |
| `--real KM` | `scale` | 是 | 实际距离，单位千米，必须大于 0 |
| `--length KM` | `bar` | 是 | 线段比例尺表示的最大千米数，范围 1 到 10000 |
| `--value V` | `convert` | 是 | 图上量得的长度，必须大于 0 |
| `--from UNIT` | `convert` | 是 | 图上长度单位，只接受 cm、m、km |
| `--to UNIT` | `convert` | 是 | 实际长度单位，只接受 cm、m、km |
| `--count N` | `sheet` | 否 | 题目数量，1 到 50，默认 8 |
| `--seed S` | `sheet` | 否 | 随机种子，0 到 2147483647，默认 1 |
| `-o PATH`、`--output PATH` | `bar`、`sheet`、`demo` | `sheet`、`demo` 必填 | 输出文件路径，UTF-8 编码 |
| `--answers` | `sheet` | 否 | 附加参考答案页 |
| `-h`、`--help` | 全局 | 否 | 显示帮助信息 |
| `--version` | 全局 | 否 | 显示版本号 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 命令执行成功 |
| 2 | 输入非法、写文件失败或命令行参数错误 |

## 作为库使用

```python
from mapscale import (
    actual_distance,
    convert,
    make_questions,
    render_bar,
    render_sheet,
    scale_denominator,
)

# 图上 3.5 厘米、比例尺 1:100000，返回 3.5 千米
real_km = actual_distance(3.5, 100000)

# 反求比例尺分母，返回 100000
denominator = scale_denominator(3.5, 3.5)

# 图上 2 厘米按 1:50000 换算为千米，返回 1.0
km = convert(2, "cm", "km", 50000)

# 生成线段比例尺 SVG 字符串
svg = render_bar(50000, 4)

# 生成 8 道题并渲染带答案的 A4 练习纸
questions = make_questions(8, 1)
html = render_sheet(questions, True)
```

`make_questions(count, seed)` 在相同种子下返回完全相同的题目，便于重现与批改。

## 开发与测试

测试仅使用标准库 `unittest`，共 157 个测试方法，覆盖正常值、边界值、非法输入、错误退出码、HTML/SVG 可解析性与随机种子可复现性。

```bash
python3 -m unittest discover -s tests -v
```

测试产物全部写入临时目录，不会留在仓库中。

## License

[MIT](LICENSE) © 2026 eastyou
