# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import urllib
import os


ROOT_URL = "http://www.uvo.gov.sk/evestnik/-/vestnik"


def get_new_bulletins():
    """Scrape new bulletins"""
    # get list of all already scraped bulletins from bulletin file
    # if file does not exists, no bulletins were previously scraped
    original_bulletins = []
    try:
        with open("bulletins.json", "r") as bulletin_file:
            original_bulletins = json.load(bulletin_file)
    except:
        pass
    
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
            if bulletin["issue"] not in original_bulletins:
                bulletins.append(bulletin)
    return bulletins


def download_xml(url):
    """Download xml file from announcement url. The url contains a numeric 
       name of the xml file, no need to search the url content."""

    # get file name from
    filename = "%s.xml" % (re.search("/([0-9]+);", url).group(1))
    url = ROOT_URL + "/save/" + filename
    destination = os.path.join("data", filename)
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
        
    # get list of already scraped bulletins
    bulletins = []
    try:
        with open("bulletins.json", "r") as bulletin_file:
            bulletins = json.load(bulletin_file)
    except:
        pass
    
    # store all scraped bulletins
    with open("bulletins.json", "w") as bulletin_file:
        bulletins.append(bulletin["issue"])
        json.dump(bulletins, bulletin_file, indent=4)


if __name__ == "__main__":

    # scrape new bulletins
    bulletins = get_new_bulletins()
    for bulletin in bulletins:
        scrape_bulletin(bulletin)