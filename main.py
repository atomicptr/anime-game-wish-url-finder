#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from operator import itemgetter
from typing import Optional

DEBUG_MODE = False

ANIME_GAME_NAME = "".join(["Ge", "nshi", "n I", "mpact"])

INSTALL_LOCATIONS = [
    # Anime Game Launcher GTK - Flatpak
    "~/.var/app/moe.launcher.an-anime-game-launcher-gtk/data/anime-game-launcher/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
    # Anime Game Launcher - Flatpak
    "~/.var/app/com.gitlab.KRypt0n_.an-anime-game-launcher/data/anime-game-launcher/game/drive_c/Program Files/%s" % ANIME_GAME_NAME,
]

CACHE_FILE_PATH = ["".join(["Gen", "shinI", "mpa", "ct_Data"]),
                   "webCaches", "Cache", "Cache_Data", "data_2"]

UID_REGEX = r"\"uid\":\"([0-9]+)\""

URL_REGEX = r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

GACHA_ENDPOINT = "e20190909gacha-v2"


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
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        timestamp = -1

        if "timestamp" in query_params:
            timestamp = int(query_params["timestamp"][0])

        matching_urls.append([timestamp, url])

    if len(matching_urls) > 0:
        newest = sorted(matching_urls, key=itemgetter(0))[0]
        return [uid, newest[1]]

    return [uid, None]


def print_result(uid: Optional[str], url: str):
    if uid is None:
        print("\n### URL For Unknown Account:\n\n%s\n" % (uid, url))
        return
    print("\n### URL For Account '%s':\n\n%s\n" % (uid, url))


def main():
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

        print_result(uid, url)


if __name__ == "__main__":
    main()
