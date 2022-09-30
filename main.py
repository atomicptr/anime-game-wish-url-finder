#!/usr/bin/env python3
'''Script to extract the wish url for a certain anime game on Linux '''
import re
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional
from base64 import b64decode
from requests import get as http_get


DEBUG_MODE = False
ANIME_GAME_NAME = b64decode("R2Vuc2hpbiBJbXBhY3Q=").decode("utf-8")
INSTALL_LOCATIONS = [
    # Anime Game Launcher
    f"~/.local/share/anime-game-launcher/game/drive_c/Program Files/{ANIME_GAME_NAME}",
    # Anime Game Launcher GTK
    f"~/.local/share/anime-game-launcher-gtk/game/drive_c/Program Files/{ANIME_GAME_NAME}",
    # Anime Game Launcher GTK - Flatpak
    "~/.var/app/moe.launcher.an-anime-game-launcher-gtk/data/anime-game-launcher"
        f"/game/drive_c/Program Files/{ANIME_GAME_NAME}",
    # Anime Game Launcher - Flatpak
    "~/.var/app/com.gitlab.KRypt0n_.an-anime-game-launcher/data/anime-game-launcher"
        f"/game/drive_c/Program Files/{ANIME_GAME_NAME}",
]
CACHE_FILE_PATH = [
    b64decode("R2Vuc2hpbkltcGFjdF9EYXRh").decode("utf-8"),
    "webCaches",
    "Cache",
    "Cache_Data",
    "data_2"
]
UID_REGEX = r"\"uid\":\"([0-9]+)\""
URL_REGEX = r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
API_HOST = "hk4e-api-os.hoyoverse.com"
GACHA_ENDPOINT = "e20190909gacha-v2"
TIME_CUTOFF_MINUTES = 15


def main():
    '''Main function, go through install locations and look for valid wish urls'''
    found_result = False

    for install_location in INSTALL_LOCATIONS:
        install_location = Path(install_location).expanduser()

        if not install_location.exists():
            if DEBUG_MODE:
                print(f"Installation '{install_location}' does not exist, skipping...")
            continue

        cache_file = install_location.joinpath(*CACHE_FILE_PATH)

        if not cache_file.exists():
            if DEBUG_MODE:
                print(f"Cache file at '{cache_file}' does not exist.")
            continue

        uid, url = find_url(cache_file)

        if url is None:
            continue

        found_result = True

        print_result(uid, url)

    if not found_result:
        print(
            "Could not find result, please log into the game, open your wish history and try again."
        )
        sys.exit(1)


def find_url(path: Path) -> [Optional[str], Optional[str]]:
    '''Try to find url within cache file'''
    data = path.read_bytes().decode("utf-8", "ignore")

    uid = None

    res = re.search(UID_REGEX, data)
    if res:
        uid = res.group(1)

    urls = re.findall(URL_REGEX, data)

    for url in urls:
        if GACHA_ENDPOINT not in url:
            continue

        if test_url(url):
            return [uid, url]

    return [uid, None]


def test_url(url: str) -> bool:
    '''Test if the URL parameters are valid'''
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    query_params["lang"] = "en"
    query_params["gacha_type"] = 301
    query_params["size"] = "5"

    test_api_url = urlunparse(
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
        test_api_url,
        headers={
            "Content-Type": "application/json",
        },
        timeout=10,
        allow_redirects=True
    )

    if DEBUG_MODE:
        print(f"Url: {test_url}\nResponse: {res.status_code}")

    if res.status_code != 200:
        return False

    json_res = json.loads(res.text)

    return json_res["retcode"] == 0


def print_result(uid: Optional[str], url: str):
    '''Print the account uid (if found) and the url to copy'''
    if uid is None:
        print(f"\n### URL For Unknown Account:\n\n{url}\n")
        return
    print(f"\n### URL For Account '{uid}':\n\n{url}\n")


if __name__ == "__main__":
    main()
