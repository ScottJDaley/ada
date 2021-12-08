import re
from urllib.request import urlopen

from bs4 import BeautifulSoup


def fetch_first_on_page(url: str) -> str:
    html = urlopen(url)
    bs = BeautifulSoup(html, "html.parser")
    image_element = bs.find(
        "img", {"src": re.compile(".png"), "class": "pi-image-thumbnail"}
    )
    if image_element is None:
        print(
            "Could not find any png image with class name 'pi-image-thumbnail' on the following page:",
            url,
        )
        return None
    return image_element["src"]
