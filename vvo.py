# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import urllib
import os


ROOT_URL = "http://www.uvo.gov.sk/evestnik/-/vestnik"
BULLETIN_CATALOG = "bulletins.json"
DATA_DIR = "data"


def get_scraped_bulletins():
    """Get list of already scraped bulletins from bulletin catalog file"""

    original_bulletins = []
    if os.path.exists(BULLETIN_CATALOG):
        with open(BULLETIN_CATALOG, "r") as bulletin_file:
            original_bulletins = json.load(bulletin_file)

    return original_bulletins  


def get_new_bulletins():
    """Scrape new bulletins"""

    # get list of all already scraped bulletins
    scraped_bulletins = get_scraped_bulletins()
    
    # create connection
    responce = requests.get(ROOT_URL + "/all")
    soup = BeautifulSoup(responce.text)
    
    # scrape all bulletin issues and links
    bulletins = []
    bulletins_in_years = soup.findAll("table", id=re.compile("rok_[0-9]+"))
    for bulletins_in_year in bulletins_in_years:
        bulletins_per_year = bulletins_in_year.findAll("a")
        for bulletin in bulletins_per_year:
            # store bulletins as dictiory with issue and http link
            bulletin = {
                "issue": bulletin.text,
                "url": bulletin["href"]
            }
            # bulletin has not been scraped before, add it to unscraped list
            if bulletin["issue"] not in scraped_bulletins:
                bulletins.append(bulletin)
    return bulletins


def download_xml(url):
    """Download xml file from announcement url. The url contains a numeric 
    name of the xml file, no need to search the url content."""

    # get file name from
    filename = "%s.xml" % (re.search("/([0-9]+);", url).group(1))
    url = ROOT_URL + "/save/" + filename

    # check if data directory exists, if not raise exception
    if not os.path.exists(DATA_DIR):
        raise Exception("Data directory does not exist")

    destination = os.path.join(DATA_DIR, filename)
    urllib.urlretrieve(url, destination)


def scrape_bulletin(bulletin):
    """Scrape announcements from bulletin url as xml file. 
    Store bulletin issue into bulletin catalog file."""

    # create connection
    response = requests.get(bulletin["url"])
    soup = BeautifulSoup(response.text)
    
    # find all announcement links and download its content in xml
    announcements = soup.findAll("div", attrs={"class": "portlet-body"})[-1]
    announcements = announcements.findAll("a", text=re.compile("[0-9]+"))
    for announcement in announcements:
        download_xml(announcement["href"])
        
    # get list of already scraped bulletins and add newly scraped one
    bulletins = get_scraped_bulletins()
    bulletins.append(bulletin["issue"])
    
    # store all scraped bulletins
    with open(BULLETIN_CATALOG, "w") as bulletin_file:
        json.dump(bulletins, bulletin_file, indent=4)


if __name__ == "__main__":

    # scrape new bulletins
    bulletins = get_new_bulletins()
    for bulletin in bulletins:
        scrape_bulletin(bulletin)