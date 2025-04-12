"""Login and get cookies
The codes are base on https://github.com/MarvinTerry/HustLogin.git
and https://github.com/rachpt/Booking-Assistant.git
"""

import json
import re
from base64 import b64decode, b64encode
from logging import root as log

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from requests import Session

from hustpass.decaptcha import decaptcha


def get_dict_cookie(r):
    """将header中的cookie转成字典形式"""
    cookies = r.request.headers.get("Cookie")
    if cookies:
        cookies = cookies.split(";")
        cookies = set([i.strip() for i in cookies])
        cookies = {i.split("=")[0]: i.split("=")[1] for i in cookies}
    return cookies


def login_hustpass(
    username: str,
    password: str,
    target_url: str,
    headers: dict = {},
) -> Session:  # 以便ide进行类型检查与代码补全
    """
    PARAMETERS:\n
    username -- Username of pass.hust.edu.cn  e.g. U2022XXXXX\n
    password -- Password of pass.hust.edu.cn\n
    headers  -- Headers you want to use, optional
    """
    # 输入类型检查
    if not isinstance(username, str) or not isinstance(password, str):
        raise TypeError("HUSTPASS: CHECK YOUR UID AND PWD TYPE")
    if headers == {}:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }
    else:
        if not isinstance(headers, dict):
            raise TypeError("HUSTPASS: CHECK YOUR HEADERS TYPE")
    # 输入有效检查
    if len(username) == 0 or len(password) == 0:
        raise ValueError("HUSTPASS: YOUR UID OR PWD IS EMPTY")
    try:
        headers["User-Agent"]
    except Exception:
        raise ValueError("HUSTPASS: YOUR HEADERS DO NOT INCLUDE UA")
    # 建立session
    log.info("setting up session...")
    session = Session()
    session.headers.update(headers)
    # 请求网站HTML
    params = {"service": target_url}
    login_html = session.get(
        "https://pass.hust.edu.cn/cas/login", params=params
    )
    # 检查是否需要输入验证码
    # NOTE:未取得不使用验证码的网页样本，这个判断可能不符合预期
    captcha_check = (
        re.search('<div class="ide-code-box">(.*)</div>', login_html.text, re.S)
        is not None
    )
    if captcha_check:
        # 请求验证码图片
        captcha_img = session.get(
            "https://pass.hust.edu.cn/cas/code", stream=True
        )
        log.info("captcha detected, trying to decaptcha...")
    # 请求公钥并加密用户名密码
    log.debug("encrypting u/p...")
    pub_key = RSA.import_key(
        b64decode(
            json.loads(session.post("https://pass.hust.edu.cn/cas/rsa").text)[
                "publicKey"
            ]
        )
    )
    cipher = PKCS1_v1_5.new(pub_key)
    encrypted_u = b64encode(cipher.encrypt(username.encode())).decode()
    encrypted_p = b64encode(cipher.encrypt(password.encode())).decode()
    # 定位form
    form = re.search(
        '<form id="loginForm" (.*)</form>', login_html.text, re.S
    ).group(0)  # 忽略换行符
    # 抓取ticket
    nonce = re.search(
        '<input type="hidden" id="lt" name="lt" value="(.*)" />', form
    ).group(1)
    # 抓取execution
    execution = re.search(
        '<input type="hidden" name="execution" value="(.*)" />', form
    ).group(1)
    post_params = {
        "rsa": None,
        "ul": encrypted_u,
        "pl": encrypted_p,
        "code": None
        if not captcha_check
        else decaptcha(captcha_img.content).strip(),
        "phoneCode": None,
        "lt": nonce,
        "execution": execution,
        "_eventId": "submit",
    }
    log.debug("posting login-form...")
    resp = session.post(
        "https://pass.hust.edu.cn/cas/login",
        data=post_params,
        allow_redirects=False,
    )
    try:
        resp.headers["Location"]
    except Exception:
        raise ConnectionRefusedError("---HustPass Failed---")
    log.info("---HustPass Succeed---")
    log.debug("Thank you for using hust_login")

    # Location 中包含 ticket
    url2 = resp.headers.get("Location")
    # 获取 cookie
    if not url2:
        raise Exception("学号或者统一身份认证密码有误")
    resp = session.get(url2, headers=headers, allow_redirects=False)
    cookies = resp.cookies.get_dict()
    resp = session.get(target_url, cookies=cookies)
    cookies = get_dict_cookie(resp)
    return cookies
