# Simple Embedding Toolchain

一套简洁的字幕压制工具链。

------------

## 简介

使用 `Chromium` + `Pyppeteer` 渲染字幕图像，然后使用 `numba` JIT优化过的 `OpenCV` 操作来将字幕逐帧附加到视频图片上，最后将视频图片拼接起来。

### 默认设置

- 默认中文字体为 `黑体`，英文字体为 `Candara`，代码字体为 `Fira Code Regular`。

- 默认代码颜色为亮蓝色（#B7F5F7），普通字颜色为纯白色。

- 默认支持半透明背景。

## 格式支持

支持扩展的 `.sub` 字幕格式，即：

- **支持完整的 Markdown 语法，包括内嵌 HTML 元素。**

- **支持通过 KaTeX 渲染 LaTeX 数学公式**

- 支持多行 / 不规则形状多行结构，用于触发前两者的多行语法

## 准备

### 字幕格式要求

准备压制的字幕文件应为 `.sub` 格式，按帧标明出现 / 消失时间。`.sub` 典型的一行格式如：

```plain
{7261}{7287}例子 Example 例子
```

触发多行结构时，应在 `{}{}` 后加入标识符 `[ml]` 或 `[multiline]`，然后提供一个合法的 **Python 字符串表达式**。

### 视频文件要求

以 `png` 图片格式逐帧拆离视频，存储到 `./images/` 内。

分离原视频的音频文件为 `./myaudio.m4a`。

### 文件名 / 格式要求

工具链支持位于下方的**主字幕**和位于上方的**副字幕**。

主字幕文件名应为 `major.sub`；或在 `render_subtitle.py` 中修改 `MAJOR_FILENAME`。

副字幕文件名应为 `minor.sub`；或在 `render_subtitle.py` 中修改 `MINOR_FILENAME`。

视频分辨率应为 1920x1080；或在 `render_subtitle.py` 的 `63` 和 `90` 行修改为对应分辨率。

### 其他要求

硬盘应有充足的空间。

## 运行

### 渲染视频

准备好字幕文件后，运行 `render_subtitle.py` 渲染字幕。

等待完成后，运行 `render_image.py`，最后运行 `generate_final_video.py` 生成最终视频。

### 并行渲染

在 `render_subtitle.py` 内，可修改 `PAGE_COUNT` 为并行渲染字幕的页面数。