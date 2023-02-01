from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import DataScraper

PATH = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"
driver = webdriver.Chrome(PATH)
actions = ActionChains(driver)
wait = WebDriverWait(driver, 10)

VIEWTIME = 3

## TODO:

def phase_1(year):

    print("Phase 1 - Bypassing Form 1")

    #JavaScript can interact with the DOM quite easily
    #Selenium is going to load our .js file and then use a couple functions to fill out the hidden form and then take us to phase 2

    with open('forms.js', 'r') as file:
        js_code = file.read()

    #Execute the js code with Selenium

    driver.execute_script(js_code)
    driver.execute_script("window.changeInputs(arguments[0]);", year)
    driver.execute_script("window.submit();")

def phase_2(year, delay=False, i=0, county_index=0):
    print("Phase 2 - Bypassing Form 2")
    print("Selecting a state/territory...")

    states = driver.find_elements(By.CSS_SELECTOR, "select[name='STATES']")[0]
    options = states.find_elements(By.TAG_NAME, "option")

    #By definiting i through the function definition, we can keep track of where we are in the DataScraper.py
    #   such that User.py doesn't get ahead of the DataScraper as both of the scripts are doing their own things.
    #In essense, we're creating a codependency.

    #Make sure the option is visible before the "user" selects it
    actions.move_to_element(options[i])
    actions.perform()

    stateName = options[i].text
    state_index = i

    print("Fetching data for " + stateName + "...")
    print()

    #Select the option
    driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
    #Execute the website's own GetCounties() function to request the county list from the database
    driver.execute_script("GetCounties();", states)

    if delay:
        time.sleep(VIEWTIME/3)


    if stateName != "U.S. Non-Metropolitan Median":
        #we don't want this generalized value, we only want counties and MSAs

        #Start iterating over the counties generated

        #We pass the index through the function too (through a dictionary) so we can keep track of the data we are iterating over
        phase_3(year, {"name": stateName, "index": state_index}, delay, i=county_index)

    else:
        #We've reached the end of the rope and that's the end of phase 2
        print(f"Completed Data Retrieval for {year}.")

    # #loop through options
    # for i in range(0, len(options)):
    #
    #     #redefine the DOM elements for the Selenium driver so the element doesn't become stale
    #     states = driver.find_elements(By.CSS_SELECTOR, "select[name='STATES']")[0]
    #     options = states.find_elements(By.TAG_NAME, "option")
    #
    #     #Make sure the option is visible before the "user" selects it
    #     actions.move_to_element(options[i])
    #     actions.perform()
    #
    #     stateName = options[i].text
    #     state_index = i
    #
    #     print("Fetching data for " + stateName + "...")
    #     print()
    #
    #     #Select the option
    #     driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
    #     #Execute the website's own GetCounties() function to request the county list from the database
    #     driver.execute_script("GetCounties();", states)
    #
    #     if delay:
    #         time.sleep(VIEWTIME/3)
    #
    #
    #     if stateName != "U.S. Non-Metropolitan Median":
    #         #we don't want this generalized value, we only want counties and MSAs
    #
    #         #Start iterating over the counties generated
    #
    #         #We pass the index through the function too (through a dictionary) so we can keep track of the data we are iterating over
    #         phase_3(year, {"name": stateName, "index": state_index}, delay)

def phase_3(year, state, delay, i=0):

    print(f"Phase 3 - Bypassing Form 3 ({state.get('name')})")
    print("Selecting a county...")

    counties = driver.find_elements(By.CSS_SELECTOR, "select[name='INPUTNAME']")[0]
    options = counties.find_elements(By.TAG_NAME, "option")

    #Similar to phase 2, by definiting i through the function definition, we can keep track of where we are in the DataScraper.py
    #   such that User.py doesn't get ahead of the DataScraper as both of the scripts are doing their own things.
    #In essense, we're creating a codependency.
    #**THIS KEEPS SELENIUM FROM FREEZING**

    #The alternative would be to use for loops to iterate over the states and counties in the HTML DOM,
    #   but this process would run independently of what happens in the DataScraper.py script;
    #   Before this script was changed, Selenium would freeze up because User.py was submitting requests faster than DataScraper.py could parse


    #Make sure the option is visible before the "user" selects it
    actions.move_to_element(options[i])
    actions.perform()

    countyName = options[i].text
    county_index = i

    print("Fetching data for " + countyName + "...")

    #Select the option
    driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
    #Execute the website's own GetCounties() function to request the county list from the database
    driver.execute_script("CollectAreas();", counties)

    if delay:
        time.sleep(VIEWTIME/3)

    #Submit the form after selecting the county
    submit = driver.find_elements(By.CSS_SELECTOR, "input[name='SubmitButton']")[0]
    submit.submit()

    #Final page with data
    #We will read the page and send the HTML data to our DataScraper.py script

    if delay:
        time.sleep(VIEWTIME)

    html = driver.page_source

    #Increment the state index if we've done all the counties--go to the next state
    if county_index == len(options)-1:
        state["index"] += 1
        county_index = 0 #reset the county index
        print(f"Completed fetching data for {state.get('name')}.")

        #Save our progress after iterating through every state
        DataScraper.save_progress()

    #Outsource the data to our DataScraper.py function
    DataScraper.parseData(year, state, {"name": countyName, "index": county_index}, html, driver, delay=delay)

    # #loop through options
    # for i in range(0, len(options)):
    #
    #     #redefine the DOM elements for the Selenium driver so the element doesn't become stale
    #     counties = driver.find_elements(By.CSS_SELECTOR, "select[name='INPUTNAME']")[0]
    #     options = counties.find_elements(By.TAG_NAME, "option")
    #
    #     #Make sure the option is visible before the "user" selects it
    #     actions.move_to_element(options[i])
    #     actions.perform()
    #
    #     countyName = options[i].text
    #     county_index = i
    #
    #     print("Fetching data for " + countyName + "...")
    #
    #     #Select the option
    #     driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
    #     #Execute the website's own GetCounties() function to request the county list from the database
    #     driver.execute_script("CollectAreas();", counties)
    #
    #     if delay:
    #         time.sleep(VIEWTIME/3)
    #
    #
    #     #Submit the form after selecting the county
    #     submit = driver.find_elements(By.CSS_SELECTOR, "input[name='SubmitButton']")[0]
    #     submit.submit()
    #
    #     #Final page with data
    #     #We will read the page and send the HTML data to our DataScraper.py script
    #
    #     if delay:
    #         time.sleep(VIEWTIME)
    #
    #     html = driver.page_source
    #
    #     #Outsource the data to our DataScraper.py function
    #     DataScraper.parseData(year, state, {"name": countyName, "index": county_index}, html, driver, delay=False)

def run(url, year, delay=False):

    driver.get(url)
    driver.refresh()

    #Step 1: Load the data for the year
    #First we must submit the form on the first page

    if(delay):
        time.sleep(VIEWTIME) #Time used to see what the Selenium driver is doing

    phase_1(year) #Bypass the first form with JS injection

    #Progress data to be logged to the console
    print("Fetching HUD Income Limits for: " + str(year))
    print()

    if(delay):
        time.sleep(VIEWTIME)

    phase_2(year, delay) #phases 2 and 3 are conjoined (i.e. phase 2 will call phase 3)

    #I do this to organize the code better; there are two separate form processes taking place here:

    #1) - Phase 2 -
    ## I) Iterate through the states and select them
    ## II) Click the State (scroll into view)
    ## III) Retrieve the counties as a result of the form submission (trigger phase_3())

    #2) - Phase 3 -
    ## I) Iterate through the counties and select them
    ## II) Click the county (scroll into view)
    ## III) Send that data to the final form and submit it

    if(delay):
        time.sleep(VIEWTIME)
