# Income Limits Research

This project uses python and javascript to scrape data from the Department of Housing and Urban Development to retrieve data on the matrix of thresholds set each year that determine eligibility for Section 8 Housing vouchers. The data can be found at [huduser.gov](https://www.huduser.gov/portal/datasets/il.html).

This program iterates over each year, state, and county, parses over the HTML data and formats the data into a readable table format with the pandas library in python.

In addition to the Pandas library, this project heavily relies on the Selenium library to stimulate user actions to bypass dynamic HTML forms that are used to send requests to the server and are then subsequently sent back to the "user" (our selenium driver) as data.

Once the data is able to be fetched from the server as HTML, the HTML can be combed through using BeautifulSoup and then formatted using the pandas library.

# Scripts

### main.py

This is the script that pulls in all other scripts and fires off the program. The years can be adjusted in the class instance declaration when a new instance is created to adjust how much data (what range of years) is parsed. The argument delay in the program.run function can be set to False or True to slow down the Selenium driver. Run this script to run the program.

### User.py

This python script contains all the user-simulated actions and events fired off via the Selenium library. To run this script (and thus the program) on your local machine, some installation of a web driver is required. Any web driver can be used (try to make it match your version of browser you're using), such as Firefox, but I use Chrome for the purposes of this project.

The script runs through essentially three main processes, with each process bypassing a dynamic form. Normally, a human user would fill out a "form" (this is literally an HTML form tag) and sends this request to the server. The server responds by sending by processing the user's data on the back end and returns data that's stored on the server. We don't have immediate access to this data so we simulate user actions to force a server response to obtain the same information.

### forms.js

This JavaScript file is used for JavaScript injection to process the first form. The website relies on a user interaction to become visible to Selenium, thus rendering Selenium essentially useless; it's much more effective to have the Selenium driver to fire off some JavaScript code (this script) that can direct immediately with the DOM instead of vicariously.

The *changeInputs(year)* function changes the hidden inputs on the first HTML form and changes the destination of where the form will be process. The script then submits the form with the *submit(n=0)* function.

### DataScraper.py

This python script parses the HTML mess on the page once the table of data is finally loaded and formats it into a readable format.

### help.js

Before *forms.js* was created, this function was created to debug why the Selenium driver wasn't able to detect the form and inputs. This served as a base script for the final *forms.js*. This now serves as a sandbox for experimenting with the DOM in case I ever need to run a test in the DOM environment quickly and I don't have time to run through the entire python program again.
