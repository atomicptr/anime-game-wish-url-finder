#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, unquote, urlunparse
from operator import itemgetter
from typing import Optional
from requests import get as http_get
import json


DEBUG_MODE = False
ANIME_GAME_NAME = "".join(["Ge", "nshi", "n I", "mpact"])
INSTALL_LOCATIONS = [
    # Anime Game Launcher
    "~/.local/share/anime-game-launcher/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
    # Anime Game Launcher GTK
    "~/.local/share/anime-game-launcher-gtk/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
    # Anime Game Launcher GTK - Flatpak
    "~/.var/app/moe.launcher.an-anime-game-launcher-gtk/data/anime-game-launcher/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
    # Anime Game Launcher - Flatpak
    "~/.var/app/com.gitlab.KRypt0n_.an-anime-game-launcher/data/anime-game-launcher/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
]
CACHE_FILE_PATH = ["".join(["Gen", "shinI", "mpa", "ct_Data"]),
                   "webCaches", "Cache", "Cache_Data", "data_2"]
UID_REGEX = r"\"uid\":\"([0-9]+)\""
URL_REGEX = r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
API_HOST = "hk4e-api-os.hoyoverse.com"
GACHA_ENDPOINT = "e20190909gacha-v2"
TIME_CUTOFF_MINUTES = 15


def main():
    found_result = False

    for install_location in INSTALL_LOCATIONS:
        install_location = Path(install_location).expanduser()

        if not install_location.exists():
            if DEBUG_MODE:
                print(
                    "Installation '%s' does not exist, skipping..." %
                    install_location)
            continue

        cache_file = install_location.joinpath(*CACHE_FILE_PATH)

        if not cache_file.exists():
            if DEBUG_MODE:
                print("Cache file at '%s' does not exist." % cache_file)
            continue

        uid, url = find_url(cache_file)

        if url is None:
            continue

        found_result = True

        print_result(uid, url)

    if not found_result:
        print("Could not find result, please log into the game, open your wish history and try again.")
        exit(1)


def find_url(path: Path) -> [Optional[str], Optional[str]]:
    data = path.read_bytes().decode("utf-8", "ignore")

    uid = None

    res = re.search(UID_REGEX, data)
    if res:
        uid = res.group(1)

    urls = re.findall(URL_REGEX, data)

    matching_urls = []

    for url in urls:
        if GACHA_ENDPOINT not in url:
            continue

        if test_url(url):
            return [uid, url]

    return [uid, None]


def test_url(url: str) -> bool:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    query_params["lang"] = "en"
    query_params["init_type"] = 301
    query_params["gacha_type"] = 301
    query_params["size"] = "5"

    test_url = urlunparse(
        (
            parsed_url.scheme,
            API_HOST,
            "/event/gacha_info/api/getGachaLog",
            parsed_url.params,
            urlencode(query_params, doseq=True),
            None,
        )
    )

    res = http_get(
        test_url,
        headers={
            "Content-Type": "application/json",
        },
        timeout=10,
        allow_redirects=True
    )

    if DEBUG_MODE:
        print("Url: %s\nResponse: %s" % (test_url, res.status_code))

    if res.status_code != 200:
        return False

    json_res = json.loads(res.text)

    return json_res["retcode"] == 0


def print_result(uid: Optional[str], url: str):
    if uid is None:
        print("\n### URL For Unknown Account:\n\n%s\n" % (uid, url))
        return
    print("\n### URL For Account '%s':\n\n%s\n" % (uid, url))


if __name__ == "__main__":
    main()
