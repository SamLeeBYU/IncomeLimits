import DataScraper
import pandas
from bs4 import BeautifulSoup
import time
import re
from selenium import webdriver

VIEWTIME = 2
from DataScraper import clean
from DataScraper import save_progress
from DataScraper import catch_data

def parseData(year, county, html, driver, delay=False, save=False, NoData=False):
    print("Premodern scraper...")

    print(f"Reading data for {county}...")

    soup = BeautifulSoup(html, 'html.parser')

    #Here's an example how our table is going to look

    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| County  |       MSA        |   Median Family Income Limit | Family Size |  Very Low Income Limit |  Extremely Low Income Limit  |  Low Income Limit  |   Year  |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       1      |          26450         |            15900            |        42300       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       2      |          30200         |            18310            |        48350       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       3      |          34000         |            23030            |        54400       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       4      |          37750         |            27750            |        60400       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       5      |          40800         |            32470            |        65250       |   2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       6      |          42300         |            37190            |        70100      |    2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       7      |          43800         |            41910            |        74900      |    2022   |
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #| AUTAUGA |  MONTGOMERY, AL  |             75000           |       8      |          46850         |            46630            |        79750      |    2022   |
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
    try:
        if year == 2013:
            msa = soup.find_all(class_ = "area_explanation")[0].find("p")
            if msa is not None:
                msa = msa.find("strong").text
        else: #2010-2013
            #We need to find all <b> tags that are direct children of <p> tags
            msa = [b.text for b in soup.select('p > b')][0]
    except Exception as e:
        msa = None
    if msa is None or not ("MSA" in msa or "Area" in msa): #These are valid MSAs
        #Then the county is the only one in its 'MSA' area
        if not NoData:
            if year == 2013:
                msa = soup.find_all("tr")[2].find_all("th")[0].text
            else:
                msa = soup.find_all("tr")[0].find_all("th")[0].text
        else:
            msa = ""
    msa = clean(msa, type="MSA")
    median = ""
    if not NoData:
        if year == 2013:
            median = clean(soup.find_all("tr")[2].find("td").text, type="price")
        else:
            median = clean(soup.find("table").find("td").text, type="price")

    #Retrieve the income Limits
    table = soup.find("table")
    rows = table.find_all("tr")

    incomes = {"Very Low Income Limits": [], "Extremely Low Income Limits": [], "Low Income Limits": []}
    
    #loop through all the td tags and add the prices (as doubles) to our python dictionary
    for i in range(2, len(rows)):
        if year == 2013:
            limits = rows[i].find_all("td")
            for j in range(0, len(limits)):
                if i == 2:
                    incomes["Very Low Income Limits"].append(clean(limits[j].text, type="price"))
                elif i == 3:
                    incomes["Extremely Low Income Limits"].append(clean(limits[j].text, type="price"))
                elif i == 4:
                    incomes["Low Income Limits"].append(clean(limits[j].text, type="price"))
        else: #This html is formatted a little differently
            fonts = rows[i].find_all("font")
            #select the last 8 elements
            limits = fonts[(len(fonts)-8):len(fonts)]
            if i == 3:
                incomes["Very Low Income Limits"] = [clean(limit.text, type="price") for limit in limits]
            elif i == 4:
                incomes["Extremely Low Income Limits"] = [clean(limit.text, type="price") for limit in limits]
            elif i == 5:
                incomes["Low Income Limits"] = [clean(limit.text, type="price") for limit in limits]

    if NoData:
        incomes["Very Low Income Limits"] = [""]*8
        incomes["Extremely Low Income Limits"] = [""]*8
        incomes["Low Income Limits"] = [""]*8
    elif year == 2013:
        incomes["Very Low Income Limits"] = incomes["Very Low Income Limits"][1:] 
        #exclude the first element because it groups the <td> from the median into this array

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