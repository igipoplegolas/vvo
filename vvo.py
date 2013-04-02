# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import urllib
import os
from common import create_context


def get_scraped_bulletins(ctx):
    """Get list of already scraped bulletins from bulletin catalog file"""

    bulletins = []
    if os.path.exists(ctx.bulletin_catalog):
        with open(ctx.bulletin_catalog, "r") as bulletin_file:
            bulletins = json.load(bulletin_file)

    ctx.logger.debug("Number of scraped bulletins: %d" % 
                        (len(bulletins)))    
    return bulletins  


def get_new_bulletins(ctx):
    """Scrape new bulletins"""

    # get list of all already scraped bulletins
    scraped_bulletins = get_scraped_bulletins(ctx)
    
    # create connection
    response = ctx.session.get(ctx.root_url + "/all")
    soup = BeautifulSoup(response.text)
    
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

    ctx.logger.debug("Number of unscraped bulletins: %d" % (len(bulletins)))                
    return bulletins


def download_xml(ctx, url):
    """Download xml file from announcement url. The url contains a numeric 
    name of the xml file, no need to search the url content."""

    # get file name from url
    filename = "%s.xml" % (re.search("/([0-9]+)", url).group(1))
    destination = os.path.join(ctx.workspace_path, filename)

    # download file
    response = ctx.session.get(ctx.root_url + "/save/" + filename)
    with open(destination, "wb") as xml_file:
        xml_file.write(response.content)  



def scrape_bulletin(ctx, bulletin):
    """Scrape announcements from bulletin url as xml file. 
    Store bulletin issue into bulletin catalog file."""

    # create connection
    response = ctx.session.get(bulletin["url"])
    soup = BeautifulSoup(response.text)
    
    # find all announcement links and download its content in xml
    announcements = soup.findAll("div", attrs={"class": "portlet-body"})[-1]
    announcements = announcements.findAll("a", text=re.compile("[0-9]+"))

    ctx.logger.debug("Scraping bulletin issue '%s' with %d announcements..." % 
                        (bulletin["issue"], len(announcements)))

    for announcement in announcements:
        download_xml(ctx, announcement["href"])

        
    # get list of already scraped bulletins and add newly scraped one
    bulletins = get_scraped_bulletins(ctx)
    bulletins.append(bulletin["issue"])
    
    # store all scraped bulletins
    with open(ctx.bulletin_catalog, "w") as bulletin_file:
        json.dump(bulletins, bulletin_file, indent=4)


if __name__ == "__main__":
    # create context
    ctx = create_context("config.ini")

    # scrape new bulletins
    bulletins = get_new_bulletins(ctx)
    for bulletin in bulletins:
        scrape_bulletin(ctx, bulletin)