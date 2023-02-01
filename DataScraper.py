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

VIEWTIME = 1

def clean(s, type="MSA"):
    #Used for conveniently cleaning the MSA and county data

    #print(s)
    parts = s.upper().split(", ")

    if type == "MSA":

        # clean("San Juan-Guaynabo, PR HUD Metro FMR Area")
        # # Output: "SAN JUAN-GUAYNABO, PR"
        #
        # clean("Montgomery, AL MSA")
        # # Output: "MONTGOMERY, AL"

        return parts[0] + ", " + parts[1].split(" ")[0]

    elif type == "price":

        s = s.strip("*")
        if "$" in s:
            s = s.strip("$")
        s = s.replace(",", "")
        return int(s)

    else: #we are cleaning a county

        return parts[0]



def parseData(year, state, county, html, driver, delay=False):

    print(f"Reading data for {county.get('name')}...")

    soup = BeautifulSoup(html, 'html.parser')
    #print(soup)

    #Breaks are mandatory otherwise the driver freezes up
    time.sleep(VIEWTIME)

    #Here's an example how our table is going to look

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| County  |       MSA       |   Median Family Income Limit |  Income Limit  |  FamilySize1  |  FamilySize2  |  FamilySize3  |  FamilySize4  |  FamilySize5  |  FamilySize6  |  FamilySize7  |  FamilySize8  |   Year  |
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUAUGA |  MONTGOMERY, AL  |             75000           |     Very Low    |     26450     |     30200     |     34000     |      37750    |     40800     |     43800     |     46850     |    49850      |  2022   |
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUAUGA |  MONTGOMERY, AL  |             75000           |  Extremely Low  |    15900      |    18310      |     23030     |     27750     |      32470    |      37190    |     41910     |     46630     |  2022   |
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUAUGA |  MONTGOMERY, AL  |             75000           |       Low       |     42300     |      48350    |     54400     |     60400     |     65250     |     70100     |     74900     |     79750     |  2022   |
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    #Scrape the data and send the data back to the User
    #The user will take the data and save the data after it has successfully parsed its way through each state
    #Permanently saving the data each time we scrape the data just off one table is too costly, and saving the data at the very end:
    #   3,000+ counties in the U.S. * each year we're parsing when we finally run this program = nearly 100,000!

    #Here's all the data we need for every iteration (in order to complete the table above)
    county = clean(county["name"], type="county")
    msa = clean(soup.find_all(class_ = "whole")[0].text)
    median = clean(soup.find_all(class_ = "whole")[1].text, type="price")

    #Retrieve the income Limits
    table = soup.find_all(class_ = "sum")[0]
    rows = table.find_all("tr")

    incomes = {"Very Low Income Limits": [], "Extremely Low Income Limits": [], "Low Income Limits": []}

    #loop through all the td tags and add the prices (as doubles) to our python dictionary
    for i in range(2, len(rows)):
        limits = rows[i].find_all("td")
        for j in range(1, len(limits)):
            if i == 2:
                incomes["Very Low Income Limits"].append(clean(limits[j].text, type="price"))
            elif i == 3:
                incomes["Extremely Low Income Limits"].append(clean(limits[j].text, type="price"))
            elif i == 4:
                incomes["Low Income Limits"].append(clean(limits[j].text, type="price"))

    print(f"County = {county}")
    print(f"MSA = {msa}")
    print(f"Median = {median}")
    print(f"Income Limits = {incomes}")
    print(f"Year = {year}")

    time.sleep(VIEWTIME)

    #After parsing the html go back and keep running through the program
    driver.back()
