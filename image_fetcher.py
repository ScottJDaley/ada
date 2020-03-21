from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

def fetch_first_on_page(url):
    html = urlopen(url)
    bs = BeautifulSoup(html, 'html.parser')
    return bs.find('img', {'src':re.compile('.png')})['src']