import re
from urllib.request import urlopen

from bs4 import BeautifulSoup


def fetch_first_on_page(url: str) -> None | str:
    try:
        html = urlopen(url)
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
    return image_element["src"]
