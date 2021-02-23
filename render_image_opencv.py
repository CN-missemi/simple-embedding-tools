from concurrent.futures import ThreadPoolExecutor
from numba import cuda
import numba
import time
import re
from cv2 import cv2
import pathlib
import numpy
import os
import shutil
import typing
import dataclasses
from pydash import py_
import typing
# ffmpeg的帧编码从1开始
# render_subtitle渲染所得文件的帧编号也从1开始
# sub里的帧编码从1开始


subtitle_images = pathlib.Path("subtitle-images")
rendered_images = pathlib.Path("rendered-images")
raw_images = pathlib.Path("images")
FILENAME_EXPR = re.compile(
    r"(?P<type>(major)|(minor))-subtitle-(?P<id>[0-9]+)-(?P<begin>[0-9]+)-(?P<end>[0-9]+)\.png")
    
# This is by default 这是默认配置
BOTTOM_OFFSET = 40  # 主字幕底边距离视频底部的距离
TOP_OFFSET = 40  # 副字幕顶边距离视频顶部的距离
INPUT_VIDEO_FILENAME = "lec.mp4"  # 输入文件名
OUTPUT_VIDEO_FILENAME = "output1.mp4"
CHUNK_SIZE = 1000
TOTAL_FLAPS = 86880
VIDEO_SHAPE = (1920, 1080)
FPS = 30


@dataclasses.dataclass
class RenderData:
    flap: int
    subtitle_img: numpy.ndarray = None
    subtitle_id: int = -1
    minor_subtitle_img: numpy.ndarray = None
    minor_subtitle_id: int = -1
    has_subtitle: bool = False
    force_render: bool = False  # 为true时，即使目标文件已经存在也要重新渲染


@numba.njit(parallel=True, nogil=True, inline="always", boundscheck=False)
# @cuda.jit()
def render_subtitle(src_img: numpy.ndarray, subtitle_img: numpy.ndarray, major: bool):
    rowc = len(subtitle_img)
    colc = len(subtitle_img[0])
    img_rowc = len(src_img)
    img_colc = len(src_img[0])
    if major:
        lurow = img_rowc-BOTTOM_OFFSET-rowc
    else:
        lurow = TOP_OFFSET
    lucol = (img_colc-colc)//2
    # (lurow,lucol) 主字幕左上角坐标
    bg_area = src_img[lurow:lurow+rowc, lucol:lucol+colc]  # 截取背景
    for r in range(rowc):
        for c in range(colc):
            # 背景色(黑色)，半透明处理
            if subtitle_img[r, c][0] == 0 and subtitle_img[r, c][1] == 0 and subtitle_img[r, c][2] == 0:
                bg_area[r, c] = (bg_area[r, c]+subtitle_img[r, c])//2
            else:
                # 非背景色，不透明
                bg_area[r, c] = subtitle_img[r, c]
    src_img[lurow:lurow+rowc, lucol:lucol+colc] = bg_area


@numba.njit(nogil=True)
def render_subtitle_wrapper(arg: typing.Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]):
    src_img, major_subtitle_img, minor_subtitle_img = arg
    if len(major_subtitle_img) != 0:
        render_subtitle(src_img, major_subtitle_img, True)
    if len(minor_subtitle_img) != 0:
        render_subtitle(src_img, minor_subtitle_img, False)
    return src_img


def main():
    begin_time = time.time()
    if not os.path.exists(rendered_images):
        os.mkdir(rendered_images)
        
    video_reader = cv2.VideoCapture(INPUT_VIDEO_FILENAME)
    FPS = int(video_reader.get(cv2.CAP_PROP_FPS))
    VIDEO_SHAPE = (int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH)), 
    int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    TOTAL_FLAPS = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video size = {VIDEO_SHAPE}, FPS = {FPS}, has {TOTAL_FLAPS} frames in total.")
    
    renderdata = [RenderData(flap=i, subtitle_img=None, subtitle_id=-1, minor_subtitle_id=-1, minor_subtitle_img=None,
                             has_subtitle=False) for i in range(0, TOTAL_FLAPS)]  # full:67071
    for item in os.listdir(subtitle_images):
        match_result = FILENAME_EXPR.match(item)
        groupdict = match_result.groupdict()
        # sub里的帧数从1开始
        begin = int(groupdict["begin"])-1
        end = int(groupdict["end"])-1
        subtitle_type = groupdict["type"]
        subtitle_id = int(groupdict["id"])
        print(subtitle_images/item)
        image_data = cv2.imread(str(subtitle_images/item))
        if subtitle_type == "major":
            for j in range(begin, end+1):
                if j >= len(renderdata):
                    break
                renderdata[j] = RenderData(
                    flap=j,
                    subtitle_img=image_data,
                    subtitle_id=subtitle_id,
                    minor_subtitle_id=renderdata[j].minor_subtitle_id,
                    minor_subtitle_img=renderdata[j].minor_subtitle_img,
                    has_subtitle=True)

        else:
            for j in range(begin, end+1):
                if j >= len(renderdata):
                    break
                renderdata[j] = RenderData(
                    flap=j,
                    subtitle_img=renderdata[j].subtitle_img,
                    subtitle_id=renderdata[j].subtitle_id,
                    minor_subtitle_img=image_data,
                    minor_subtitle_id=subtitle_id,
                    has_subtitle=True
                )
    print(f"{len(renderdata)} flaps loaded")
    pool = ThreadPoolExecutor()
    video_writer = cv2.VideoWriter(OUTPUT_VIDEO_FILENAME, cv2.VideoWriter_fourcc(
    *"mp4v"), FPS, VIDEO_SHAPE, True)
    empty_frame = numpy.ndarray([0, 0, 0])
    for seq in py_.chunk(renderdata, CHUNK_SIZE):
        chunk_begin = time.time()
        print(
            f"Rendering for {len(seq)} flaps, range from {seq[0].flap} to {seq[-1].flap}")
        count = len(seq)
        frames = []
        print("Decoding frames..")
        for _ in range(count):
            ok, frame = video_reader.read()
            if not ok:
                print("?")
                break
            frames.append(frame)
            # print(len(frame),len(frame[0]))
        print(f"{len(seq)=} {len(frames)=}")
        assert len(seq) == len(frames)
        print("Frames loaded.")
        args = [(frame, (empty_frame if render_data.subtitle_img is None else render_data.subtitle_img),
                 (empty_frame if render_data.minor_subtitle_img is None else render_data.minor_subtitle_img)) for frame, render_data in zip(frames, seq)]
        output: typing.List[numpy.ndarray] = list(pool.map(
            render_subtitle_wrapper, args))
        print("Render done.")
        for frame in output:
            video_writer.write(frame)
        chunk_end = time.time()
        print(f"Output ok with {chunk_end-chunk_begin}s .")
    pool.shutdown()
    video_reader.release()
    video_writer.release()
    end_time = time.time()
    print(f"Task done, {end_time-begin_time}s")


if __name__ == "__main__":
    main()
