import numpy as np
from scipy import stats
import os
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import seaborn as sns
import pandas

VERSION = "2.1.0"

class time_vector:

    def __init__(self, year, state):
        self.year = year
        self.state = state
        self.times = np.array([])
        self.t_statistic = None
        self.p_value = None

    def getData(self):
        return {"year": self.year, "state": self.state, "times": self.times, "t_statistic": self.t_statistic, "p_value": self.p_value}
    
    def addTime(self, t):
        self.times = np.append(self.times, t)

    def getMean(self):
        return np.mean(self.times)

    def compareTimes(self, times2):
        #Run a two-sample t-test on two time vectors to see if there is a significant difference between execution times
        # Perform the two-sample t-test
        self.t_statistic, self.p_value = stats.ttest_ind(self.times, times2, alternative='greater')

        # Print the results
        print("T-statistic:", self.t_statistic)
        print("P-value:", self.p_value)

        return self.t_statistic, self.p_value

def plot_execution_times(execution_times, total_seconds):
    #build a dataframe from the execution_times
    execution_times_list = [time_vector.getData() for time_vector in execution_times]
    ET = pandas.DataFrame(execution_times_list)
    ET = ET.explode("times").reset_index(drop=True)

    rate = ((ET.shape[0]*8)/total_seconds)
    time_report = f"Total counties scraped: {ET.shape[0]}. Total rows added since started scraping: {ET.shape[0]*8}. That's about {(rate):.4f} rows of data addded to IncomeLimits.csv per second."
    print(time_report)

    last_row = ET.tail(1)
    y = last_row["year"].values[0]
    s = last_row["state"].values[0]
    state_times = ET[(ET["year"] == y) & (ET["state"] == s)]

    cumulative_rate = ET.shape[0]*8/total_seconds
    state_rate = state_times["times"].sum()
    if state_rate > -1:
        state_rate = state_times.shape[0]*8/state_rate

    total_seconds = state_times["times"].sum()
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    # Create a time object
    state_time = datetime.time(hour=int(hours), minute=int(minutes), second=int(seconds))
    print(f"Time to scrape data from {s} for {y}: {state_time}")
    rates = {"version": [VERSION], "year": [y], "state": [s], "cumulative_scrape_rate": [cumulative_rate], "state_scrape_rate": [state_rate], "cumulative_rows_scraped": [ET.shape[0]*8], "state_rows_scraped": [state_times.shape[0]*8], "time_to_scrape": state_time}
    rates = pandas.DataFrame(rates)
    print("\nHere's some informative data on the pace of the scraper:")
    print(rates)
    if os.path.exists("Rates.csv"):
        rates.to_csv("Rates.csv", mode='a', index=False, header=False)
    else:
        rates.to_csv("Rates.csv", index=False)
    print()

    ET.fillna("").to_csv("Execution Times.csv", index=False)

    #Group by mean and state to calculate the mean for each iteration
    ET_summary = ET.groupby(["year", "state"])["times"].mean().reset_index()
    #ET_summary["times"] = pandas.to_numeric(ET_summary["times"]) #May not be necessary
    print(ET_summary.sort_values(["times", "state"], ascending=False).head())
    print()

    ET_summary['state_abbr'] = ET_summary['state'].str.split('-').str[-1].str.strip()
    ET_summary["year_state"] = ET_summary["year"].astype(str) + " - " + ET_summary["state_abbr"]
    mean_times = ET_summary["times"].mean()
    ET_summary["SS"] = (ET_summary["times"] - mean_times)**2

    #Select the top 25 scrapes that will maximize variance
    target_n = len(ET_summary)
    if target_n > 25:
        target_n = 25
    ET_condensed_summary = ET_summary.sort_values(["SS"], ascending=False).head(target_n).sort_values(
        by=["year", "state"],
        ascending=[False, True]
    ).reset_index(drop=True)

    # Use seaborn's barplot or Matplotlib's bar function to create the bar plot
    # Here, we're using a seaborn bar plot for simplicity
    plt.clf()
    graph = ET_condensed_summary[["year_state","times"]].copy()
    sns.barplot(data=graph, x="year_state", y="times", errorbar=None)
    plt.title("Mean Times by Year and State")
    plt.xlabel("Scrape")
    plt.ylabel("Mean Times")
    plt.xticks(rotation=90, ha="center")  # Rotates x-axis labels for readability
    plt.tight_layout()  # Adjusts the layout to prevent overlapping labels

    plt.savefig("Maximized Variance Execution Times.png")

def compare_years(execution_times, year, comparison_year=None, from_file=False):
    ET = pandas.DataFrame()
    if from_file:
        ET = pandas.read_csv("Execution Times.csv")
    else:
        execution_times_list = [time_vector.getData() for time_vector in execution_times]
        ET = pandas.DataFrame(execution_times_list)
        ET = ET.explode("times").reset_index(drop=True)
    
    ET_year_summary = ET.groupby("year", sort=False)["times"].mean()
    years = ET_year_summary.index.tolist()

    base_year = None
    compared_year = None
    paired_text = ""
    if len(years) > 1:
        if comparison_year is None:
            #Get the year that was scraped first
            comparison_year = years[0]
            
        means = ET.groupby(["year", "state"])["times"].mean().reset_index()
        #Paired t-test
        base_year = means[means["year"] == comparison_year][["state", "times"]]
        compared_year = means[means["year"] == year][["state", "times"]]
        merged = pandas.merge(compared_year, base_year, on="state", how='inner')
        merged["diff"] = merged["times_x"] - merged["times_y"]
        merged = merged.dropna()
        sample = merged["diff"].values
        
        paired_text += "If we ran a paired t-test:\n"
        paired_text += f"Mean of the differences: {np.mean(sample):.6f}\n"
        if(len(sample) > 1):
            sample = sample.astype(float)
            t_statistic, p_value = stats.ttest_1samp(sample, 0)
            paired_text += f"Here is the test statistic for the paired test: {t_statistic:.6f}.\n"
            paired_text += f"The corresponding p-value is {p_value:.6f}\n"
            
            if p_value < 0.05:
                paired_text += "The p-value is significant under the paired t-test.\n"
            else:
                paired_text += "The p-value is NOT significant under the paired t-test.\n"
        else:
            paired_text += "There are not enough samples to perform the statistical test.\n"
            
        print(paired_text)
    
    year_comparison_text = "Let's check out how long it took to scrape each county, on average, over this entire year:\n"
    print(year_comparison_text)
    
    if len(years) > 1:
        s1 = f"Here are the means of the two years for {year} when compared to {comparison_year}.\n"
    else:
        s1 = f"Here is the mean of {year}.\n"
    
    print(s1)
    year_comparison_text += s1
    ET_year_vector = ET[ET["year"] == year]["times"].values
    if compared_year is not None:
        ET_year_vector = compared_year["times"].values
    year_mean = np.mean(ET_year_vector)
    
    ET_compared_vector = None
    compared_mean = None
    if base_year is not None:
        ET_compared_vector = base_year["times"].values
        compared_mean = np.mean(ET_compared_vector)
    
    if ET_compared_vector is not None:
        s2 = f"Mean for {year}: {year_mean:.6f}.\nMean for {comparison_year}: {compared_mean:.6f}\n"
    else:
        s2 = f"Mean for {year}: {year_mean:.6f}.\n"
    print(s2)
    year_comparison_text += s2
    
    if ET_compared_vector is not None:
        s3 = f"We will run a test to see if this year was significantly slower than {comparison_year}.\n"
        print(s3)
        year_comparison_text += s3

        ET_compared_vector = ET_compared_vector.astype(float)
        ET_year_vector = ET_year_vector.astype(float)
        
        t_statistic, p_value = stats.ttest_ind(ET_year_vector, ET_compared_vector, alternative='greater')
        
        s4 = f"Here is the test statistic: {t_statistic:.6f}.\nThe corresponding p-value is {p_value:.6f}\n"
        print(s4)
        year_comparison_text += s4
        
        s5 = f"The p-value was significant! This year scraped data significantly slower than {comparison_year}."
        if p_value < 0.05:
            print(s5)
            year_comparison_text += s5
    
    with open("Yearly Comparisons.txt", "a") as f:
        f.write(paired_text+year_comparison_text + "\n\n")
    
    print("\n")