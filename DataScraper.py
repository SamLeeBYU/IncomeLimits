import os
import pandas
from bs4 import BeautifulSoup
import time
import re
from selenium import webdriver

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

        try:
            # Define a regular expression pattern to match digits (0-9) and optional commas
            pattern = r'[0-9,]+'
            # Use re.findall to find all occurrences of the pattern in the string
            matches = re.findall(pattern, s)
            # Join the matches together and remove commas
            cleaned = ''.join(matches).replace(',', '')
            return cleaned
        except Exception as e:
            print(f"There was an error cleaning the string: {e}. This was the cleaned string: {cleaned}. This was the original string: {repr(s)}")

    else: #we are cleaning a county

        return parts[0].replace(" COUNTY", "")

DATA = None #This variable will store the data in the RAM until we tell it otherwise
def catch_data(data):

    #This function will keep track of the parsed data we send to it from parsedData(...)

    global DATA
    if DATA is None:
        DATA = data
    else:
        DATA = pandas.concat([DATA, data]).reset_index(drop=True)
    #print(DATA)

    print("End of Phase 3.")


def parseData(year, county, html, driver, delay=False, save=False, NoData=False):

    print(f"Reading data for {county}...")

    soup = BeautifulSoup(html, 'html.parser')

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

    #* Generally, extremely low-income families are defined to be very low-income families whose incomes are the greater of the Poverty Guidelines as published
    #  and periodically updated by the Department of Health and Human Services or the 30 percent income limits calculated by HUD. However, Puerto Rico and other 
    #  territories are specifically excluded from this adjustment. Instead, in Puerto Rico the Extremely Low Income Limit is set at the Very Low Income Limit.

    #Scrape the data and send the data back to the User
    #The user will take the data and save the data after it has successfully parsed its way through each state
    #Permanently saving the data each time we scrape the data just off one table is too costly, and saving the data at the very end:

    #Here's all the data we need for every iteration (in order to complete the table above)
    county_data = clean(county, type="county")
    msa = ""
    median = ""
    if not NoData:
        msa = clean(soup.find_all(class_ = "whole")[0].text, type="MSA")
        median = clean(soup.find_all(class_ = "whole")[1].text, type="price")
    else:
        msa = clean(soup.select("p > strong")[1].text, type="MSA")

    #Retrieve the income Limits
    incomes = {"Very Low Income Limits": [], "Extremely Low Income Limits": [], "Low Income Limits": []}
    if not NoData:
        table = soup.find_all(class_ = "sum")[0]
        rows = table.find_all("tr")

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
    else:
        incomes["Very Low Income Limits"] = [""]*8
        incomes["Extremely Low Income Limits"] = [""]*8
        incomes["Low Income Limits"] = [""]*8

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

    if save:
        save_progress()

    driver.back()

INDICES = {"year": 2023, "state": 0, "county": 0}
def save_index(indices):
    global INDICES
    INDICES = indices

def get_indices():
    #print(INDICES)
    return INDICES

#save the data periodically (can be called from the User.py class or from wherever)
#The goal is the save the data when the DATA gets too large;
#   i.e. a good time to save our progess would be after we iterated over the 3,000+ counties in each state
def save_progress():
    global DATA #same variable referenced in the catch_data() function used to track the parsed data in the RAM
    print(DATA)
    DATA = DATA.drop_duplicates().reset_index(drop=True)

    if os.path.exists("IncomeLimits.csv"):
        DATA.to_csv('IncomeLimits.csv', mode='a', index=False, header=False)
    else:
        DATA.to_csv("IncomeLimits.csv", index=False)

    print("Current progress saved to IncomeLimits.csv")
    print("Overwriting RAM...")
    DATA = None #overwrite the RAM for efficiency
    print()

# incomeLimits = pandas.read_csv("IncomeLimits.csv")
# incomeLimits = incomeLimits.drop_duplicates().reset_index(drop=True)
# incomeLimits.to_csv("IncomeLimits2022-2016.csv", index=False)