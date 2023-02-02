import os
import pandas
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver

import User

## TODO:

#Get the county information upon post form transcation (sent over from User.py)
## store values into tables

VIEWTIME = 2

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

        #Get county FIPS codes

        if len(parts) > 1:
            return parts[0] + ", " + parts[1].split(" ")[0]
        else:
            #EX Alaska's "Kusilvak Census Area"
            return parts[0]

    elif type == "price":

        s = s.strip("*")
        if "$" in s:
            s = s.strip("$")
        s = s.replace(",", "")
        return int(s)

    else: #we are cleaning a county

        return parts[0].replace(" COUNTY", "")

DATA = None #This variable will store the data in the RAM until we tell it otherwise
def catch_data(data):

    #This function will keep track of the parsed data we send to it from parsedData(...)

    global DATA
    if DATA is None:
        DATA = data
    else:
        DATA = pandas.concat([DATA, data])

    print(DATA)

    print("End of Phase 3.")
    print()


def parseData(year, state, county, html, driver, delay=False):

    print(f"Reading data for {county.get('name')}...")

    soup = BeautifulSoup(html, 'html.parser')
    #print(soup)

    #Breaks are mandatory otherwise the driver freezes up
    time.sleep(VIEWTIME)

    #Here's an example how our table is going to look

    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| County  |       MSA        |   Median Family Income Limit | Family Size |  Very Low Income Limit |  Extremely Low Income Limit  |  Low Income Limit  |   Year  |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       1      |          26450         |            15900            |        42300       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       2      |          30200         |            18310            |        48350       |  2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       3      |          34000         |            23030            |        54400       |  2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       4      |          37750         |            27750            |        60400       |  2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       5      |          40800         |            32470            |        65250       |  2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       6      |          42300         |            37190            |        70100      |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       7      |          43800         |            41910            |        74900      |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       8      |          46850         |            46630            |        79750      |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------

    #Scrape the data and send the data back to the User
    #The user will take the data and save the data after it has successfully parsed its way through each state
    #Permanently saving the data each time we scrape the data just off one table is too costly, and saving the data at the very end:
    #   3,000+ counties in the U.S. * each year we're parsing when we finally run this program = nearly 100,000!

    #Here's all the data we need for every iteration (in order to complete the table above)
    county_data = clean(county["name"], type="county")
    msa = clean(soup.find_all(class_ = "whole")[0].text, type="MSA")
    median = clean(soup.find_all(class_ = "whole")[1].text, type="price")

    #Retrieve the income Limits
    table = soup.find_all(class_ = "sum")[0]
    rows = table.find_all("tr")

    incomes = {"Very Low Income Limits": [], "Extremely Low Income Limits": [], "Low Income Limits": []}

    #loop through all the td tags and add the prices (as doubles) to our python dictionary
    for i in range(2, len(rows)):
        limits = rows[i].find_all("td")
        for j in range(0, len(limits)):
            if i == 2:
                incomes["Very Low Income Limits"].append(clean(limits[j].text, type="price"))
            elif i == 3:
                incomes["Extremely Low Income Limits"].append(clean(limits[j].text, type="price"))
            elif i == 4:
                incomes["Low Income Limits"].append(clean(limits[j].text, type="price"))
    incomes["Very Low Income Limits"] = incomes["Very Low Income Limits"][1:] #exclude the first element because it groups the <td> from the median into this array

    #diagnostic data (now formatted into a table)
    # print(f"County = {county_data}")
    # print(f"MSA = {msa}")
    # print(f"Median = {median}")
    # print(f"Income Limits = {incomes}")
    # print(f"Year = {year}")

    if delay:
        time.sleep(VIEWTIME)

    #Log the the parsed data in the RAM
    tidy_table = {"County": [county_data]*8, "MSA": [msa]*8, "Median": [median]*8, "FamilySize": list(range(1,9)),
    "VeryLow": incomes["Very Low Income Limits"], "ExtremelyLow": incomes["Extremely Low Income Limits"], "Low": incomes["Low Income Limits"], "Year": [year]*8}
    #This is a tidy table as outlined several lines above

    catch_data(pandas.DataFrame(tidy_table))


    #After parsing the html go back and keep running through the program
    driver.back()

    #Data has been collected
    #Send signal back to User.py to continue its iteration

    #increment the county index by one to continue:
    User.phase_2(year, delay=delay, i=state["index"], county_index=county["index"]+1)

#save the data periodically (can be called from the User.py class or from wherver)
#The goal is the save the data when the DATA gets too large;
#   i.e. a good time to save our progess would be after we iterated over the 3,000+ counties in each state
def save_progress():
    global DATA #same variable referenced in the catch_data() function used to track the parsed data in the RAM

    current = None
    if os.path.exists("IncomeLimits.csv"):
        current = pandas.read_csv("IncomeLimits.csv")
        current = pandas.concat([current, DATA])
        current.to_csv("IncomeLimits.csv")
    else:
        DATA.to_csv("IncomeLimits.csv")

    print("Current progress saved to IncomeLimits.csv")
    print("Overwriting RAM...")
    DATA = None #overwrite the RAM for efficiency
    print()
