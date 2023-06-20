import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def fetch_first_on_page(url: str) -> None | str:
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req)
        bs = BeautifulSoup(html, "html.parser")
        image_element = bs.find(
            "img", {"src": re.compile(".png"), "class": "pi-image-thumbnail"}
        )
    except:
        print(
            "Could not find any png image with class name 'pi-image-thumbnail' on the following page:",
            url,
        )
        return None
    return "https://satisfactory.wiki.gg" + image_element["src"]
