import re
import ujson
from io import StringIO
import asyncio
import pathlib
import os
import shutil
import pyppeteer
import typing
import math
import time
import aiofiles
import ast
import tempfile
import html
MAIN_EXPR = re.compile(r"\{(?P<begin>[0-9]+)\}\{(?P<end>[0-9]+)\}(?P<text>.+)")
SUBTIITLE_MATCH_EXPR = re.compile(
    r"(?P<multiline_mark>\[((ml)|multiline)\])?(?P<text>.*)")
MAJOR_FILENAME = "major.sub"
MINOR_FILENAME = "minor.sub"
image_path = pathlib.Path("subtitle-images")
local = os.getcwd()

PAGE_COUNT = 8


def parse_subtitle_string(text: str) -> str:
    match_result = SUBTIITLE_MATCH_EXPR.match(text)
    assert match_result
    groups = match_result.groupdict()
    # print(groups)
    if groups["multiline_mark"] is not None:
        return ast.literal_eval(groups["text"])
    return (html.escape(groups["text"]))


async def main():
    begin_time = time.time()
    subtitles = []
    broswer_temp_path = tempfile.mkdtemp()

    def load_file(filename: str, subtitle_type: str):
        with open(filename, "r", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()[1:]):
                if line.strip():
                    pass
                match_result = MAIN_EXPR.match(line)
                assert match_result
                groups = match_result.groupdict()
                subtitles.append({
                    "begin": groups["begin"],
                    "end": groups["end"],
                    "text": parse_subtitle_string(groups["text"]),
                    "type": subtitle_type,
                    "type_id": i+1
                })
    load_file(MAJOR_FILENAME, "major")
    if MINOR_FILENAME:
        load_file(MINOR_FILENAME, "minor")
    async with aiofiles.open("index.html", "r") as f:
        html_content = await f.read()
    shutil.rmtree(image_path, True)
    os.mkdir(image_path)
    broswer = await pyppeteer.launch({
        "headless": True,
        'args': ['--disable-infobars', '--window-size=1920,1080', '--no-sandbox'],
        "userDataDir": broswer_temp_path
    })

    async def take_screen_shot(id: int, page: pyppeteer.page.Page):
        item = subtitles[id]
        elem = await page.querySelector(f"#{item['type']}-subtitle-{item['type_id']}")
        begin, end = item["begin"], item["end"]
        filename = f"{item['type']}-subtitle-{item['type_id']}-{begin}-{end}.png"
        await elem.screenshot({"path": f"{str(image_path)}/{filename}", "type": "png"})
        print(f"{item['type']}-{item['type_id']} done.")

    async def render_something(ids: typing.List[int], task_id: int):
        print(f"Task {task_id}, count = {len(ids)}")
        buf = StringIO()
        for x, item in zip(ids, (subtitles[y] for y in ids)):
            buf.write(f"""
            <div class="{item['type']}-subtitle subtitle normal-text" id="{item['type']}-subtitle-{item['type_id']}">
                <div class="markdown-required">{item["text"]}</div>
            </div>
            """)
        new_content = html_content.replace("REPLACE-HERE", buf.getvalue())
        async with aiofiles.open(f"render-{task_id}.html", "w", encoding="utf-8") as f:
            await f.write(new_content)
        print(f"{task_id} loaded")
        page = await broswer.newPage()
        await page.setViewport({
            "width": 1920,
            "height": 1080
        })

        await page.goto(f"file:///{local}/render-{task_id}.html")
        # await asyncio.wait([
        #     page.waitForSelector(f"#subtitle-{x}") for x in ids
        # ])
        await page.waitForSelector(".finish-signal")
        for i in ids:
            await take_screen_shot(i, page)
        await page.close()
        os.remove(f"render-{task_id}.html")
    tasks: typing.List[typing.List[int]] = []
    items_per_task = int(math.ceil(len(subtitles)/PAGE_COUNT))
    for i in range(len(subtitles)):
        if i == 0 or i//items_per_task != (i-1)//items_per_task:
            tasks.append([])
        tasks[i//items_per_task].append(i)
    # print(tasks)
    await asyncio.wait([
        render_something(x, i) for i, x in enumerate(tasks)
    ])
    await broswer.close()
    end_time = time.time()
    shutil.rmtree(broswer_temp_path, ignore_errors=True)
    print(f"ok, {(end_time-begin_time)}s")
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
