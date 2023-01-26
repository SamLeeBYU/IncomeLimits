import os
import pandas
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver

## TODO:

# Make a function that scrapes the states from the given html
## store it into files?

#Scrape the county information as well upon post form transcation
## store values into tables

VIEWTIME = 3

def parseData(year, state, county, html, driver, delay=False):

    print(f"Reading data for {county.get('name')}...")

    soup = BeautifulSoup(html, 'html.parser')
    #print(soup)

    time.sleep(VIEWTIME)

    #After parsing the html go back and keep running through the program
    driver.back()
