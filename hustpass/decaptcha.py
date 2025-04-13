"""Use tesseract to decaptcha
The whole script is extracted from https://github.com/MarvinTerry/HustLogin/blob/main/hust_login/decaptcha.py
"""

import logging
from io import BytesIO

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def decaptcha(img_content):
    img_list = []
    with Image.open(BytesIO(img_content)) as img_gif:
        for i in range(img_gif.n_frames):
            img_gif.seek(i)
            img_list.append(img_gif.copy().convert("L"))
    width, height = img_list[0].size
    img_merge = Image.new(mode="L", size=(width, height), color=255)
    for pos in [(x, y) for x in range(width) for y in range(height)]:
        if sum([img.getpixel(pos) < 254 for img in img_list]) >= 3:
            img_merge.putpixel(pos, 0)
    try:
        captcha_code = pytesseract.image_to_string(
            img_merge, config="-c tessedit_char_whitelist=0123456789 --psm 6"
        )
    except pytesseract.TesseractNotFoundError:
        logger.exception("tesseract 没有安装！")
        raise EnvironmentError(
            "请安装 tesseract-ocr ，可参考 https://tesseract-ocr.github.io/tessdoc/Downloads.html"
        )
    logger.info("OCR结果：{}".format(captcha_code.strip()))
    return captcha_code
