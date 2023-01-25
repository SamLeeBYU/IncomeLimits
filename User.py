from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

PATH = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"
driver = driver = webdriver.Chrome(PATH)
actions = ActionChains(driver)
wait = WebDriverWait(driver, 10)

VIEWTIME = 3


## TODO:

#Create phase 2
# Select the state
# Select the county
# Send html data to DataScraper.py
# Submit form

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

def phase_2(year):
    print("Phase 2 - Bypassing Form 2")
    print("Selecting a state/territory...")

    states = driver.find_elements(By.CSS_SELECTOR, "select[name='STATES']")[0]
    options = states.find_elements(By.TAG_NAME, "option")

    #loop through options
    for i in range(0, len(options)):
        states = driver.find_elements(By.CSS_SELECTOR, "select[name='STATES']")[0]
        options = states.find_elements(By.TAG_NAME, "option")

        #Make sure the option is visible before the "user" selects it
        actions.move_to_element(options[i])
        actions.perform()

        print("Fetching Data for " + options[i].text + "...")

        #Select the option
        driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
        #Execute the website's own GetCounties() function to request the county list from the database
        driver.execute_script("GetCounties();", states)

        time.sleep(1)

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

    phase_2(year)

    if(delay):
        time.sleep(VIEWTIME)

# html = driver.page_source
# send html data to DataScraper functions
#
# # parse the HTML using BeautifulSoup
# soup = BeautifulSoup(html, 'html.parser')
