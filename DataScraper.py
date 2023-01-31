import os
import pandas
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver

## TODO:

# Make a function that scrapes the states from the given html
## store it into files?

#Get the county information upon post form transcation (sent over from User.py)
## store values into tables

VIEWTIME = 3

def clean(s, county=False):
    #Used for conveniently cleaning the MSA and county data

    parts = s.upper().split(",")

    if county:

        return parts[0]


    else: #we are cleaning an MSA

        # clean("San Juan-Guaynabo, PR HUD Metro FMR Area")
        # # Output: "SAN JUAN-GUAYNABO, PR"
        #
        # clean("Montgomery, AL MSA")
        # # Output: "MONTGOMERY, AL"

        return parts[0] + ", " + parts[1].split(" ")[0]


def parseData(year, state, county, html, driver, delay=False):

    print(f"Reading data for {county.get('name')}...")

    soup = BeautifulSoup(html, 'html.parser')
    #print(soup)

    #Breaks are mandatory otherwise the driver freezes up
    time.sleep(VIEWTIME)

    #Here's an example how our table is going to look

    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| County  |     MSA     | Median Family Income Limit |            Very Low Income Limits (1-8)         |         Extremely Low Income Limits (1-8)        |                Low Income Limits (1-8)            | year |
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| Autauga | Montgomery |             75000          | 26450,30200,34000,37750,40800,43800,46850,49850  | 15900,18310,23030,27750,32470,37190,41910,46630  | 42300,48350,54400,60400,65250,70100,74900,79750  | 2022 |
    #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    #Scrape the data and send the data back to the User
    #The user will take the data and save the data after it has successfully parsed its way through each state
    #Permanently saving the data each time we scrape the data just off one table is too costly, and saving the data at the very end:
    #   3,000+ counties in the U.S. * each year we're parsing when we finally run this program = nearly 100,000!

    data = {}


    #After parsing the html go back and keep running through the program
    driver.back()
