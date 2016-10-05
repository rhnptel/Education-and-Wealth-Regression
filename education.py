from bs4 import BeautifulSoup
import requests
import pandas as pd 
import matplotlib.pyplot
import csv
import numpy as np 
import sqlite3 as lite
import math
import statsmodels.api as sm

url = "http://web.archive.org/web/20110514112442/http://unstats.un.org/unsd/demographic/products/socind/education.htm"
r = requests.get(url)
soup = BeautifulSoup(r.content)

#get all elements with tcont and remove the last few
thelist = soup.findAll('tr', attrs=('class', 'tcont'))
thelist = thelist[:93]

#get the fields we need for analysis (country, year, male school years, female school years)
fields = []
for el in thelist:
	fields.append([el.contents[1].string, el.contents[3].string, el.contents[15].string, el.contents[21].string])

df = pd.DataFrame(fields)
df.columns = ['Country', 'Year', 'Male_Years', 'Female_Years']

#convert school years to integers
df['Male_Years'] = df['Male_Years'].map(lambda x: int(x))
df['Female_Years'] = df['Female_Years'].map(lambda x: int(x))

#create sqlite database and table to insert school data
con = lite.connect('gdpEducation.db')
cur = con.cursor()
df.to_csv('school_years.csv', header=True, index=False)

with con:
	cur.execute('CREATE TABLE school_years (Country, Year, Male_Years, Female_Years)')

with open('school_years.csv') as inputFile:            
    header= next(inputFile)
    inputReader = csv.reader(inputFile)                                                                       
    for line in inputReader:
        to_db = [line[0], line[1], line[2], line[3]]         
        with con:
            cur.execute('INSERT INTO school_years (Country, Year, Male_Years, Female_Years) VALUES (?, ?, ?, ?);', to_db)

#create gdp table and insert gdp data from csv
with con:
	cur.execute('CREATE TABLE gdp (Country text, _1999 numeric, _2000 numeric, _2001 numeric, _2002 numeric, _2003 numeric, _2004 numeric, _2005 numeric, _2006 numeric, _2007 numeric, _2008 numeric, _2009 numeric, _2010 numeric)')

with open('/Users/rohanpatel/Downloads/world_bank_data/GDP.csv','rU') as inputFile:
    next(inputFile)
    next(inputFile)
    header = next(inputFile)
    inputReader = csv.reader(inputFile)
    for line in inputReader:
        with con:
            cur.execute('INSERT INTO gdp (country_name, _1999, _2000, _2001, _2002, _2003, _2004, _2005, _2006, _2007, _2008, _2009, _2010) VALUES ("' + line[0] + '","' + '","'.join(line[42:-5]) + '");')

#create new table that holds both school years data and gdp data
with con:
    cur.execute('CREATE TABLE GDPandEducation (Country, GDP, Male_Years, Female_Years)')

with con:
    cur.execute('INSERT INTO GDPandEducation (Country, GDP, Male_Years, Female_Years) SELECT gdp.Country, _2005, Male_Years, Female_Years FROM gdp JOIN school_years ON gdp.Country = school_years.Country;')

#put the data back into a pandas dataframe
finaldf = pd.read_sql_query("SELECT * FROM GDPandEducation", con, index_col = "Country")

#take out any rows that do not have data
finaldf.dropna(inplace=True)
finaldf = finaldf[finaldf['GDP'] != ' ']

GDP = finaldf['GDP'].map(lambda x: float(x))
Male_Years = finaldf['Male_Years'].map(lambda x: int(x))
Female_Years = finaldf['Female_Years'].map(lambda x: int(x))

#convert gdp to log(gdp)
log_GDP = GDP.map(lambda x: np.log(x))

y = np.matrix(log_GDP).transpose()
x = np.matrix(Male_Years).transpose()

X = sm.add_constant(x)
model = sm.OLS(y,X)
results = model.fit()

y = np.matrix(log_GDP).transpose()
x = np.matrix(Female_Years).transpose()

X = sm.add_constant(x)
model2 = sm.OLS(y,X)
results2 = model2.fit()




