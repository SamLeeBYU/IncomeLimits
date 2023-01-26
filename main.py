import User

#TODO:

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
    "MODERN": list(range(2014,2022+1)),
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


class main:

    def __init__(self, start, end):

        self.start = start
        self.end = end
        self.step = -1

        self.years = range(self.start, self.end-1, self.step)

    def run(self, delay=False):
        for year in self.years:

            User.run("https://www.huduser.gov/portal/datasets/il.html#" + str(year), year, delay)

program = main(start=2022, end=2014) #The end goal is scrape through all levels 1990-2022, but years 2014-2022 are in the most standardized format
program.run(delay=True)
