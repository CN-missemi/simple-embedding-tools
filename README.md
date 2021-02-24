# Simple Embedding Toolchain

一套简洁的字幕压制工具链。

A simple toolchain for burn subtitles into mp4 video (hardcode embed).

------------

[中文说明](#简介)

## Intro

This script use `Chromium` + `Pyppeteer` for rendering subtitle images, and `OpenCV` + `numba` JIT to attach subtitles to video frames, then output the video. Finally it invokes `ffmpeg` to adjust bitrate and append audio track.

### Default Styles

- English text use `Candara` font, and Chinese text use `黑体` font by default. Code uses the `Fira Code` font.

- Code is colored bright blue (#B7F5F7), whereas plain text is white (#FFFFFF).

- Add semi-transparent rectangle shade by default.

## Syntax supports

This script support the extended `.sub` format, i.e:

- **Full Markdown syntax, including HTML elements / tags**

- **Render LaTeX math formula by KaTeX**

- Multi-line or irregular shape multi-line structures, to trigger the multi-line elements of the first two

## Setout

Please install `ffmpeg`.

### Subtitle format

The subtitle which to be burned should be in `.sub` format, the start / end time should be indicated by **frame**. One typical line of `.sub` should be:

```plain
{7261}{7287}例子 Example 例子
```

When trigger multi-line structures, you should append a `[ml]` / `[multiline]` identifier after the `{}{}`, then provide a legal **Python string**.

### Filename / Format requirements

By using this toolchain, you can burn a major subtitle (located in the bottom center) and a minor subtitle (located in the top center).

The major subtitle should be named as `major.sub`; or you can modify it in `render_subtitle.py`.

The minor subtitle should be named as `minor.sub`; or you can modify it in `render_subtitle.py`.

Best performance when provide a 1920x1080 video input.

## Run

### Burning

Get the subtitle file ready, then run `render_subitle.py` to render subtitle images.

After finished, invoke `ffmpeg` to extract audio. (Assume that original video is named `lec.mp4`)

```bash
 ffmpeg -i lec.mp4 -vn -acodec copy myaudio.m4a
```

Then execute `py render_video_opencv.py --chunk-size 500 --input lec.mp4`.

*(When `CHINK_SIZE` is set to `500`, render an video of 1920x1080 resolution takes 7GiB memory. Please modify to an appropriate value.)*

***(Execute `py render_video_opencv.py -h` to see help and all options)***

Finally, ensure the extracted audio is in the same folder with output video. Then modify the video filename below, and execute this command. The filename `output1.mp4` is the default output filename of the previous step:

```bash
ffmpeg -i output1.mp4 -i myaudio.m4a -c:v copy -c:a aac -strict experimental -b:v 500k -pix_fmt yuv420p -c:v libx264 output.mp4 -y
```

or just execute `generate_final_video.py` to generate final video. Video filename is also `output1.mp4` by default.

### Parallel Render

You can modify `PAGE_COUNT` value in `render_subtitle.py` to the parallel pages of rendering subtitle.

## 简介

使用 `Chromium` + `Pyppeteer` 渲染字幕图像，然后使用 `OpenCV` + `numba` JIT 将字幕逐帧附加到视频图片上并输出视频。使用 `ffmpeg` 调整码率并附加音频。

### 默认设置

- 默认中文字体为 `黑体`，英文字体为 `Candara`，代码字体为 `Fira Code Regular`

- 默认代码颜色为亮蓝色（#B7F5F7），普通字颜色为纯白色（#FFFFFF）

- 默认支持半透明背景

## 格式支持

支持扩展的 `.sub` 字幕格式，即：

- **支持完整的 Markdown 语法，包括内嵌 HTML 元素。**

- **支持通过 KaTeX 渲染 LaTeX 数学公式**

- 支持多行 / 不规则形状多行结构，用于触发前两者的多行语法

## 准备

请安装 `ffmpeg`。

### 字幕格式要求

准备压制的字幕文件应为 `.sub` 格式，按帧标明出现 / 消失时间。`.sub` 典型的一行格式如：

```plain
{7261}{7287}例子 Example 例子
```

触发多行结构时，应在 `{}{}` 后加入标识符 `[ml]` 或 `[multiline]`，然后提供一个合法的 **Python 字符串表达式**。

### 文件名 / 格式要求

工具链支持位于下方的**主字幕**和位于上方的**副字幕**。

主字幕文件名应为 `major.sub`；或在 `render_subtitle.py` 中修改 `MAJOR_FILENAME`。

副字幕文件名应为 `minor.sub`；或在 `render_subtitle.py` 中修改 `MINOR_FILENAME`。

视频分辨率为 1920x1080 时，渲染效果最好。

## 运行

### 渲染视频

准备好字幕文件后，运行 `render_subtitle.py` 渲染字幕。

等待完成后，使用 `ffmpeg` 提取原始视频文件的音频。（假设原始视频命名为 `lec.mp4`）

```bash
ffmpeg -i lec.mp4 -vn -acodec copy myaudio.m4a
```

然后执行 `py render_video_opencv.py --chunk-size 500 --input lec.mp4`。

*（`CHUNK_SIZE` 为 `500` 时，1920x1080 分辨率的视频约占用 7GiB 内存，请酌情修改。）*

***（使用 `py render_video_opencv.py -h` 查看帮助和所有选项）***

确保音频文件和生成的视频处于同一目录，之后修改下列命令中输入输出视频的文件名，并执行。此命令默认视频文件名为 `output1.mp4`（即上步的输出视频名），也可自行修改：

```bash
ffmpeg -i output1.mp4 -i myaudio.m4a -c:v copy -c:a aac -strict experimental -b:v 500k -pix_fmt yuv420p -c:v libx264 output.mp4 -y
```

或运行 `generate_final_video.py` 生成最终视频。默认视频名也为 `output1.mp4`。

### 并行渲染

在 `render_subtitle.py` 内，可修改 `PAGE_COUNT` 为并行渲染字幕的页面数。
