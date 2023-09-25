# The FY 2014 Consolidated Appropriations Act changed the definition
# of extremely low-income to be the greater of 30/50ths (60 percent)
# of the Section 8 very low-income limit or the poverty guideline as
# established by the Department of Health and Human Services (HHS),
# provided that this amount is not greater than the Section 8 50% very
# low-income limit. Consequently, the extremely low income limits may
# equal the very low (50%) income limits.

#The LEVELS map out how each dataset is mapped out on the website
#Subsequently, each range of years will affect how we will parse/retrieve the data.
#The MODERN range is the most up to date and consistent range
#Simply tab through the datasets in the different years to see what I'm talking about.
LEVELS = {
    #We can use similar web scraping techniques for all of these ranges.
    #The only difference between these ranges is how the data is retrieved (i.e. difference urls & different selenium clicks)
    #And most notably how the html is organized and thus how it is scraped

    #This script was based off this range. Though years 2014-2015 require an additional form injection (see forms.js)
    "MODERN": list(range(2014,2023+1)),

    #Use premodern.py to scrape the data
    "PREMODERN": list(range(2010, 2013+1)),

    "PREMODERN_2": list(range(2007, 2009+1)),

    #2001-2006 is also available in Excel
    #If we can eliminate the headers and the extraneous data we can read the data in like a text file and parse it like a table
    #This approach will be similar to what we do with what I do with the .txt files they have for the early years.
    "MSWORD": list(range(2001, 2006+1)) + list(range(1994, 1995+1)),

    #Datasets where the data is stored in .txt files
    "TXT": list(range(1990, 1993+1)) + list(range(1996, 1999+1))
    #1999 is a special case though because there's a regular version and then there's a "revised" version
    #These years might be easier to parse because the data is readily accessible (no forms),
    #The data just needs cleaning

}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import threading
import time
import datetime
from bs4 import BeautifulSoup
import urllib.parse

import time
import DataScraper
import premodern
import analysis
from analysis import time_vector


PATH = "Driver\chromedriver113.exe"
#service = Service(ChromeDriverManager().install())

def start_driver():
    options = Options()

    chrome_service = Service(PATH)
    driver = webdriver.Chrome(service=chrome_service, options=options)
    #driver = webdriver.Chrome(service=service, options=options)

    return driver

driver = start_driver()
actions = ActionChains(driver)
wait = WebDriverWait(driver, 10)

VIEWTIME = 3

EXECUTION_TIMES = []
def get_ET():
    return EXECUTION_TIMES
MEAN_TIMES = []

#This conditional is used to see whether we need to create a new scraper object
FLAG = False

def locate_execution_time(year, state):
    #Locates the time vector in the EXECUTION_TIMES array; returns false otherwise
    target = (year, state)
    for i in range(len(EXECUTION_TIMES)):
        times = EXECUTION_TIMES[i]
        data = times.getData()
        year_state_key = (data["year"], data["state"])
        if target == year_state_key:
            return i
    return -1

#There will only be one scraper object in here at any given time
SCRAPERS = []

THREADS = []

def measure_time(start_time, threshold=10.1):
    global FLAG
    scraper_ = SCRAPERS[0]
    #Since the thread is only updating every 100 ms, bump up the threshold to 10.1 sec to make certain the data has 10 sec to be scraped
    counting = True
    while counting and not scraper_.getDataScraped():
        current = time.perf_counter() - start_time
        #print(current)
        if current >= threshold:
            indices = DataScraper.get_indices()

            counting = False
            now = datetime.datetime.now()
            error_message = f"{now}: Scraper took too long: {current}; \nCURRENT INDICES: {indices}"
            with open("errors.txt", "a") as f:
                f.write(error_message + "\n\n")

            FLAG = True
        time.sleep(0.1)

class scraper:
    def __init__(self, start_time):
        self.FROZEN = False
        self.FINISHED = False
        self.DataScraped = False
        self.EXECUTE = True

        #initalize the starting and stopping points
        self.ending_year = 0
        self.starting_year = 0

        #A conditional to see whether we are scraping the last state of a year
        self.last_state = False

        self.start_time = start_time
    
    def calculateTime(self):
        self.end_time = time.perf_counter()
        total_seconds = self.end_time - self.start_time

        hours = total_seconds // 3600
        remaining_seconds = total_seconds % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        print(f"\nTotal seconds elapsed: {total_seconds:.4f}")
        print(f"That's {hours} hours, {minutes} minutes, and {seconds:.4f} seconds.\n")

        return total_seconds
    
    def getDataScraped(self):
        return self.DataScraped

    def getFINISHED(self):
        return self.FINISHED

    def antifreeze(self):
        if self.FROZEN:
            self.FROZEN = False
        else:
            self.FROZEN = True

        #Store a dictionary with the current year, and state and county indices
        indices = DataScraper.get_indices()
        return indices

    def phase_1(self, year):
        global FLAG

        print("Phase 1 - Bypassing Form 1")

        #JavaScript can interact with the DOM quite easily
        #Selenium is going to load our .js file and then use a couple functions to fill out the hidden form and then take us to phase 2

        try:
            #print("Reading the js code.")
            with open('forms.js', 'r') as file:
                js_code = file.read()

            #Execute the js code with Selenium

            #print("Loading the js code...")
            driver.execute_script(js_code)
            time.sleep(1)

            #print("Executing js code")
            driver.execute_script("window.changeInputs(arguments[0]);", year)
            driver.execute_script("window.submit(arguments[0]);", year)
        except Exception as e:
            now = datetime.datetime.now()
            indices = DataScraper.get_indices()
            error_message = f"{now}: {str(e)};\nThere was an error with the JavaScript.\nCURRENT INDICES: {indices}"
            with open("errors.txt", "a") as f:
                f.write(error_message + "\n\n")
            FLAG = True

        #Give the page enough time to load
        time.sleep(2)

    def phase_2(self, year, state=0, county=0, delay=False):
        global FLAG

        # print(f"Year: {year}, State: {state}, County: {county}")

        print("Phase 2 - Bypassing Form 2")
        print("Selecting a state/territory...")
        print()
        
        selector = "select[name='statename']" if year in range(2007, 2009+1) else "select[name='STATES']"
        states = driver.find_elements(By.CSS_SELECTOR, selector)[0]

        #Index out of range error
        options = states.find_elements(By.TAG_NAME, "option")

        i = 0

        if self.FROZEN:
            i = state

        stateName = options[i].text        

        #Include support for scraping years 2007-2009
        if year in range(2007, 2009+1):
            #This is a dropdown menu where we have to manually select the state
            dropdown = Select(states)
            dropdown.select_by_index(i)
            #We have to submit the form request to get the county data
            submit_state = driver.find_element(By.CSS_SELECTOR, "input[value='Select State']")
            submit_state.submit()
        else:
            #Otherwise, we can just scroll it into view for Selenium to click on it

            #Make sure the option is visible before the "user" selects it
            actions.move_to_element(options[i])
            actions.perform()

        #int(year >= 2010) Is there because in years 2010-2023, the menu includes the U.S. metropolitan area in the list of options,
        #Years 2007-2009 don't. In order to identify which state is the last state we're scraping, we have to take this into account.
        while i < len(options)-int(year >= 2010) and not self.FINISHED and not FLAG:
            self.DataScraped = False

            #Time how long it takes for Selenium to move from one state to the next to run...
            start_time = time.perf_counter()

            # Create and start the thread for measuring time
            THREADS.append(threading.Thread(target=measure_time, args=(start_time,)))
            THREADS[len(THREADS)-1].start()

            #Reestablish the dom elements to keep it from coming stale
            selector = "select[name='statename']" if year in range(2007, 2009+1) else "select[name='STATES']"
            states = driver.find_elements(By.CSS_SELECTOR, selector)[0]

            #Index out of range for the states 
            options = states.find_elements(By.TAG_NAME, "option")

            stateName = options[i].text

            #Include support for scraping years 2007-2009
            if i > 0:
                if year in range(2007, 2009+1):
                    #This is a dropdown menu where we have to manually select the state
                    dropdown = Select(states)
                    dropdown.select_by_index(i)
                    #We have to submit the form request to get the county data
                    submit_state = driver.find_element(By.CSS_SELECTOR, "input[value='Select State']")
                    submit_state.submit()
                else:
                    #Otherwise, we can just scroll it into view for Selenium to click on it

                    #Make sure the option is visible before the "user" selects it
                    actions.move_to_element(options[i])
                    actions.perform()

            print("Fetching data for " + stateName + "...")

            if locate_execution_time(year, stateName) < 0:
                EXECUTION_TIMES.append(time_vector(year, stateName))

            if year >= 2010:
                #Select the option
                driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
                #Execute the website's own GetCounties() function to request the county list from the database
                driver.execute_script("GetCounties();", states)

                if delay:
                    time.sleep(VIEWTIME/3)

            self.DataScraped = True

            end_time = time.perf_counter()

            execution_time = end_time - start_time
            EXECUTION_TIMES[locate_execution_time(year, stateName)].addTime(execution_time)
            print(f"Execution time: {execution_time:.6f} seconds")
            print()

            # Wait for the time thread to finish
            THREADS[len(THREADS)-1].join()
            
            try: 
                #Minus 2 (for years 2010+) because we do not need the U.S. Non-Metropolitan Median
                if i == len(options)-1-int(year >= 2010):
                    self.last_state = True
                self.phase_3(year, stateName, stateIndex=i, county=county, delay=delay)
            except Exception as e:
                #Antifreezing mechanism to escape 504 gateway errors
                now = datetime.datetime.now()
                indices = DataScraper.get_indices()
                error_message = f"{now}: {str(e)};\nThere was an error in Phase 3.\nCURRENT INDICES: {indices}"
                with open("errors.txt", "a") as f:
                    f.write(error_message + "\n\n")
                FLAG = True

            i += 1

    def phase_3(self, year, state, stateIndex=0, county=0, delay=False):
        global FLAG

        print(f"Phase 3 - Bypassing Form 3 ({state})")
        print("Selecting a county...\n")

        counties = driver.find_elements(By.CSS_SELECTOR, "select[name='INPUTNAME']")[0]
        options = counties.find_elements(By.TAG_NAME, "option")

        i = 0

        if self.FROZEN:
            i = county
            self.antifreeze()

        while i < len(options) and not self.FINISHED and not FLAG:
            self.DataScraped = False

            #Time how long it takes for the DataScraper to run...
            start_time = time.perf_counter()

            # Create and start the thread for measuring time
            THREADS.append(threading.Thread(target=measure_time, args=(start_time,)))
            THREADS[len(THREADS)-1].start()

            counties = driver.find_elements(By.CSS_SELECTOR, "select[name='INPUTNAME']")[0]
            options = counties.find_elements(By.TAG_NAME, "option")

            DataScraper.save_index({"year": year, "state": stateIndex, "county": i})

            try:
                #Make sure the option is visible before the "user" selects it
                actions.move_to_element(options[i])
                actions.perform()

                countyName = options[i].text

                print("Fetching data for " + countyName + "...")

                #Select the option
                driver.execute_script("arguments[0].setAttribute('selected', 'true');", options[i])
                
                #Support for scraping data from 2007-2009
                if year in range(2007, 2009+1):
                    #2007 requires a different form submission
                    form_action = f"{year}summary.odn" if year in range(2008, 2009+1) else f"{year}summary.odb"
                    county_form = driver.find_element(By.CSS_SELECTOR, f"form[action='{form_action}']")
                    hidden_attr = [input.get_attribute("value") for input in county_form.find_elements(By.TAG_NAME, "input")]
                    #Essentially we're hacking the url instead of making selenium trying to click through the form elements
                    driver.get(f"""https://www.huduser.gov/portal/datasets/il/il{year}/{form_action}?
                                INPUTNAME={urllib.parse.quote(options[0].get_attribute('value'), safe='*').replace('%20', '+')}&
                                selection_type={hidden_attr[0]}&
                                stname={hidden_attr[1]}&
                                statefp={hidden_attr[2]}&
                                year={hidden_attr[3]}""".replace(' ', '').replace('\n', ''))
                else:
                    #Execute the website's own GetCounties() function to request the county list from the database
                    driver.execute_script("CollectAreas();", counties)

            except:
                print(f"The index was {i}")
                print(f"Here's how many options there are: {len(options)}")
                FLAG = True

            if year >= 2010:
                if delay:
                    time.sleep(VIEWTIME/3)

                #Submit the form after selecting the county
                submit = driver.find_elements(By.CSS_SELECTOR, "input[name='SubmitButton']")[0]

                submit.submit()

                #Final page with data
                #We will read the page and send the HTML data to our DataScraper.py script

                if delay:
                    time.sleep(VIEWTIME)

            #Wait for data to load before passing html to data parser
            try:
                NoData = False
                try:
                    #Wait up to 8 seconds to see if the data is loaded in the table. Otherwise, assume NoData (the scraper won't read the table)
                    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'td'), ','))
                except Exception as e:
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    if len(soup.find_all("td")) <= 0:
                        #There is no data even after waiting for it to load
                        print("No data found.")
                        NoData = True
                html = driver.page_source

                #td_element = driver.find_element(By.XPATH, "//table//tbody//tr[5]//td[8]")
                #print(td_element.text)

                if i == len(options)-1:
                    #Make sure we parse the data for the last county and save it
                    if year >= 2014:
                        DataScraper.parseData(year, countyName, html, driver, delay=delay, save=True, NoData=NoData)
                    elif year in range(2007, 2013+1):
                        premodern.parseData(year, countyName, html, driver, delay=delay, save=True, NoData=NoData)
                else:
                    if year >= 2014:
                        #Outsource the data to our DataScraper.py function
                        DataScraper.parseData(year, countyName, html, driver, delay=delay, NoData=NoData)
                    elif year in range(2007, 2013+1):
                        premodern.parseData(year, countyName, html, driver, delay=delay, NoData=NoData)

                self.DataScraped = True

            except Exception as e:
                #Antifreezing mechanism to escape 504 gateway errors
                now = datetime.datetime.now()
                indices = DataScraper.get_indices() #antifreeze()
                error_message = f"{now}: {str(e)}; \nCURRENT INDICES: {indices}"
                with open("errors.txt", "a") as f:
                    f.write(error_message + "\n\n")
                FLAG = True

            end_time = time.perf_counter()

            execution_time = end_time - start_time
            #The last scrape is an outlier because it has to save the data externally to a file
            EXECUTION_TIMES[locate_execution_time(year, state)].addTime(execution_time)
            print(f"Execution time: {execution_time:.6f} seconds")
            print()

            if i == len(options)-1:
                print(f"Completed fetching data for {state}.\n")

                mean_time = EXECUTION_TIMES[locate_execution_time(year, state)].getMean()
                MEAN_TIMES.append(mean_time)
                print(f"Mean scrape time per county: {mean_time:.6f} seconds.")
                if len(EXECUTION_TIMES) > 1:
                    print(f"Here's how fast the scraper was able to parse through {state} for {year} compared to the times in the beginning:")
                    EXECUTION_TIMES[locate_execution_time(year, state)].compareTimes(EXECUTION_TIMES[0].getData()["times"])
                    analysis.plot_execution_times(EXECUTION_TIMES, self.calculateTime())
                print()

                if self.last_state:
                    print(f"Completed Data Retrieval for {year}.")

                    analysis.compare_years(EXECUTION_TIMES, year)
                    self.EXECUTE = True

                    #Is this the last county of the state of the last year?
                    if year == self.ending_year:
                        print("The scraper has finished scraping all the data it was assigned to scrape.")
                        #Terminate the program if we finished scraping all the data from all the years
                        self.FINISHED = True
                        FLAG = True

                    #Reset this conditional to false again
                    self.last_state = False

            # Wait for the time thread to finish
            THREADS[len(THREADS)-1].join()

            i += 1

    def run(self, url, year, state=0, county=0, delay=False):
        driver.get(url)
        driver.refresh()

        #Step 1: Load the data for the year
        #First we must submit the form on the first page

        if(delay):
            time.sleep(VIEWTIME) #Time used to see what the Selenium driver is doing

        print("Executing Phase 1.")
        self.phase_1(year) #Bypass the first form with JS injection

        #Progress data to be logged to the console
        print("Fetching HUD Income Limits for: " + str(year))
        print()

        #phases 2 and 3 are conjoined (i.e. phase 2 will call phase 3)
        self.phase_2(year, state=state, county=county, delay=delay)

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

    def start_at(self, starting_year, ending_year, base_url, state, county, freeze=False, delay=False):
        global FLAG

        self.delay = delay
        self.starting_year = starting_year
        self.ending_year = ending_year
        if freeze:
            self.antifreeze()

        #We set this to true, meaning the program will have to come back here in order to run again or it will have to finish scraping a year
        self.EXECUTE = True
        while self.starting_year >= self.ending_year and not self.FINISHED and not FLAG:
            try:
                #print("Running the main loop.")
                if self.EXECUTE:
                    self.EXECUTE = False
                    self.run(base_url + str(self.starting_year), self.starting_year, state, county, delay=self.delay)
            except TimeoutError as e:
                now = datetime.datetime.now()
                indices = DataScraper.get_indices() #antifreeze()
                error_message = f"{now}: {str(e)};\nThere was an error in the main loop.\nCURRENT INDICES: {indices}"
                with open("errors.txt", "a") as f:
                    f.write(error_message + "\n\n")
                FLAG = True
            except Exception as e:
                #Antifreezing mechanisms to escape timeout errors from the selenium driver
                now = datetime.datetime.now()
                indices = DataScraper.get_indices() #antifreeze()
                error_message = f"{now}: {str(e)};\nThere was an error in the main loop.\nCURRENT INDICES: {indices}"
                with open("errors.txt", "a") as f:
                    f.write(error_message + "\n\n")
                FLAG = True
            self.starting_year -= 1        

class main:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.start_time = time.perf_counter()

    def matchURL(self, year):
        return "https://www.huduser.gov/portal/datasets/il.html#"

    def scrape_limits(self, index):
        global FLAG
        iterations = 0
        while not SCRAPERS[index].getFINISHED():
            if FLAG:
                iterations = 0
                for thread in THREADS:
                    thread.join()
                del SCRAPERS[index]
                SCRAPERS.append(scraper(self.start_time))
                indices = DataScraper.get_indices()
                FLAG = False
                SCRAPERS[0].start_at(indices["year"], self.end, self.matchURL(indices["year"]), indices["state"],  indices["county"], freeze=True, delay=self.delay)
            if iterations > 1:
                #This means the while loop is stuck without any of the conditionals changing,
                #Normally this shouldn't happen if I thought of every exception, but just in case
                break
            iterations += 1


    def start_at(self, starting_year, ending_year, base_url, state, county, freeze=False, delay=False):
        self.delay = delay
        self.start = starting_year
        self.end = ending_year
        SCRAPERS.append(scraper(self.start_time))
        SCRAPERS[0].start_at(starting_year, ending_year, self.matchURL(self.start), state, county, freeze=freeze, delay=self.delay)
        self.scrape_limits(0)

    def run(self, delay=False):
        self.delay = delay
        SCRAPERS.append(scraper(self.start_time))
        SCRAPERS[0].start_at(self.start, self.end, self.matchURL(self.start), 0, 0, freeze=True, delay=self.delay)
        self.scrape_limits(0)

program = main(start=2009, end=2007)

if __name__ == "__main__":
    #program.start_at(2007, 2007, program.matchURL(2016), 53, 0, freeze=True)
    program.run(delay=False)

#NoData at program.start_at(2015, 2010, program.matchURL(2016), 19, 94, freeze=True)

#Use these in the DOM for finding the index of the state and counties:
# document.getElementsByName("STATES")[0].getElementsByTagName("option")[38]
# document.getElementsByTagName("select")[1].getElementsByTagName("option")[87]