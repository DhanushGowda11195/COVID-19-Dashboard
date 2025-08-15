
# Coronavirus (COVID-19) Dashboard

This dashboard provides insights on the spread of Coronavirus in diffrent countries as well as in different states of India.
There are 2 tabs-
1. Global 
- Which provides insights on the spread of Coronavirus at country level.
- The data is updated with 1 day delay i.e the dashboards has data upto yesterday.

2. India
- Which provides insights on the spread of Coronavirus at state level.
- The data is updated on a daily basis and we have access to current data.

The dashboard provides information on the latest data available on COVID-19, such as new cases, deaths, recovered, and other valuable data to gauge the transmission and response to the pandemic. 

### Video
![App Screenshot](https://github.com/bharathngowda/COVID_19_Dashboard/blob/master/video.gif)

### Screenshots

#### Global Tab

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-6.png)

#### India Tab

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-7.png)


  
## API Reference

#### Global - Historical Data for all countries in the world daywise

```http
  GET https://corona.lmao.ninja/v2/historical?lastdays=all
```

#### India - Historical Data for all states in India daywise

```http
  GET https://api.rootnet.in/covid19-in/stats/history
```
  
## Features

1. #### Stats
It contains 4 indicators - Confirmed, Active, Recovered, Deaths.
- Confirmed - is the running total of all cases tested and confirmed around the world.
- Active - is the current total active cases as on last refreshed date. It is calculated as Active=Confirmed-Recovered-Deaths
- Recovered - is the total number of patients who have recovered from the infection as on last refreshed date.
- Deaths - is the running total of all COVID-19 releated deaths

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-1.png)


2. #### Top 10 Affected Countries/states

It provides the information on Top 10 countries/states with highest active cases in a tabbular format.
The table contains details of Country/ State Name, Confirmed, Active, Recovered and Deaths

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-2.png)

3. #### Chropleth Map

This Figure provides the Active cases across the world/country. The darker the color the higher the infection rate in such countries or states.

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-3.png)

4. #### Global/India Trendlines 

This Figure provides the trend of active cases, deaths and recovered over the period of time.

Available Filters - 
- Date Filter - to adjust the date range for which the trends are required.
- Quick Date Filter - to quickly adjust the date range i.e. Last 7 Das, Previous Month, Previous Week etc.
- Span - the span for the trend line i.e., Weekly,Monthly, Yearly and daily.
- Category Filter - which has options to choose between Active, Recovered and Deaths.
- Thresholds - it includes Maximum, Average, 7 Day Simple Moving Average, & Day Exponential Moving Average
- Scale - option to choose between linear and log

All the above filters affects the Trendlines based on the selected data.

5. #### Country/State Level Trendlines

This Figure provides trend of active cases, deaths and recovered over the period of time for selected country/state.

All the above filters affects the Trendlines based on the selected data.

6. #### New cases

This Figure provides information on the new active cases, recovered, deaths recorded as on the last refreshed date.

Logic used - new cases are calculated by subtracting the data available for max date in the selected date range with the data for max date -1 


![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-4.png)

7. #### Top 10 Affected Countries/states

This Figure provides the information on Top 10 countries/states with highest active cases.
The figure contains details of Country/ State Name, Confirmed, Active, Recovered and Deaths

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-5.png)



## Programming Language and Packages

The dashboard is built using Python 3.6+.

The main Packages used are - 
- Plotly - to make the charts
- Dash - to build the interactive dashboard
- Requests - to make requests for getting new data
- Pandas & Numpy - to process the data and convert it into a format that is required by the dashboard.


### Installation

To run this notebook interactively:

1. Download this repository in a zip file by clicking on this [link](https://github.com/bharathngowda/COVID_19_Dashboard/archive/refs/heads/master.zip) or execute this from the terminal:
`https://github.com/bharathngowda/COVID_19_Dashboard.git`

2. Install [virtualenv](http://virtualenv.readthedocs.org/en/latest/installation.html).
3. Navigate to the directory where you unzipped or cloned the repo and create a virtual environment with `virtualenv env`.
4. Activate the environment with `source env/bin/activate`
5. Install the required dependencies with `pip install -r requirements.txt`.
6. Execute `python COVID-19_Dashboard.py` from the command line or terminal.
7. Copy the link `http://localhost:8888` from command prompt and paste in browser and the dashboard will load.
8. When you're done deactivate the virtual environment with `deactivate`.
