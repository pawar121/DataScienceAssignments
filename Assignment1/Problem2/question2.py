
# coding: utf-8

# In[1]:

import time
import urllib.response
import urllib.request
from bs4 import BeautifulSoup
import datetime
import logging
from urllib.request import urlopen
import re
from io import BytesIO
from zipfile import ZipFile
import os
import sys
import pandas as pd
import numpy as np
import zipfile
import boto
import boto.s3
import sys
from boto.s3.key import Key
import time
from tqdm import *


# In[2]:

def getUrl(year,base_url = "https://www.sec.gov/files/edgar" ):
    new_url = base_url + str(year) + ".html"
    return new_url


# In[3]:

def getLogger(dir):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    # create a file handler
    handler = logging.FileHandler(fileDir+'/ques2.log')
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)
    return logger


# In[4]:

def validateYear(year, logger):
    logger.info("Validating an year "+str(year))
    url = "https://www.sec.gov/data/edgar-log-file-data-set.html"
    html = urlopen(url)
    soup = BeautifulSoup(html,"html.parser")
    logger.info("Reading data from https://www.sec.gov/data/edgar-log-file-data-set.html")
    headDiv = soup.find('div', id = 'asyncAccordion')
    anchorList = headDiv.findAll('a')
    yearsList = []
    for anchor in anchorList :
        yearsList.append(anchor.text)
    if year.isdigit() and year in yearsList:
        logger.info(str(year)+" year is validated.")
        return True
    else:
        logger.error(str(year)+" year is not valid.")
        return False


# In[5]:

def funCheckDir(filepath, logger):
    directory = os.path.dirname(filepath) # defining directory path
    logger.info("Checking if files are already present in cache!")
    if not os.path.exists(directory): # checking if directory already exists
        logger.info("Files need to be downloaded.")
        return True
    else :
        return False


# In[6]:

def handleMissingValues(file,i):
    file['Anomaly'] = 0

    #handling missing values for size
    #if size is blank fill it by mean size of each code group 
    if len(file.loc[file['size'].isnull()]) > 0:  
        logger.info("Rows with missing size:" + str(len(file.loc[file['size'].isnull()])))
        file['size'] = file.groupby("code")['size'].transform(lambda x: x.fillna(x.mean()))
        # if mean is 0 : value is again NaN, set size as 0 to handle NaN mean
        file['size'].fillna(0,inplace=True)  
        #display(file)
    
    
    #Handling missing data in browser
    #display rows where noagent = 0 and browser is null
    #set browser as oth in such case

    if len(file.loc[(file['noagent']==0) & (file['browser'].isnull())]) > 0:  
        logger.info("Rows with browser as null and noagent = 0:" + str(len(file.loc[(file['noagent']==0) & (file['browser'].isnull())])))
        file.ix[file['noagent'] == 0, 'browser'] = file.ix[file['noagent'] == 0, 'browser'].fillna("oth")
        #display(file.loc[file['noagent']==0])

        
    # if no agent = 1 , and browser is null fill blanks as NoBrowser
    if len(file.loc[file['noagent']==1 & file['browser'].isnull()])>0:
        logger.info("Rows with browser as null and noagent = 1:" + str(len(file.loc[file['noagent']==1 & file['browser'].isnull()])))
        file.ix[file['noagent']==1, 'browser'] = file.ix[file['noagent'] == 1, 'browser'].fillna("NoBrowser")
        #display(file.loc[file['noagent']==1])
        
    return file


# In[7]:

def checkForAnomalies(file,i):
    #CHECK 1 FOR ANOMALIES :  if extention ends with index.htm -> idx = 1 
    # if idx is 0 for extention ending with index.htm then set Anomaly as 1

    if len(file.loc[ (file['idx'] == 0.0) & (file['extention'] == '-index.htm') ]) > 0:
        #display(file.loc[ (file['idx'] == 0.0) & (file['extention'] == '-index.htm') ])
        #update idx to 1 where extention is index.htm
        file['Anomaly'] = 1
        logger.info(len(file.loc[ (file['idx'] == 0.0) & (file['extention'] == '-index.htm') ]) +" Anomalies found when in columns : extention and idx")
    else:
        logger.info("No anomalies found in columns : extention and idx.")

    #Anomaly Detection for Status code crawler column
    if len(file.loc[(file['code'] == 404.0) & (file['crawler'] != 1)]) > 0:
        print("File "+str(i)+" Anomalies found when in columns : code and crawler")
        logger.info("Anomalies found when in columns : code and crawler")
        file['Anomaly'] = 1
        logger.info(file.loc[(file['code'] == 404.0) & (file['crawler'] != 1)])
    else:
        logger.info("No anomalies found when in columns : code and crawler")


    #Anomaly Detection for HTTP status code format
    if len(file.loc[~(file['code'].apply(str).str.contains(r'[1-5][0-9][0-9]',regex=True))])>0:
        file['Anomaly'] = 1
        #print(file.loc[~(file['code'].apply(str).str.contains(r'[1-5][0-9][0-9]',regex=True))])
        logger.info("Anomalies found when in columns : HTTP code.")
    else:
        logger.info("No anomalies found when in columns : HTTP code.")

        
    #Anomaly Detection for IP address format
    # if len(logfile.loc[~(logfile['ip'].str.contains(r'\d[1-9]{1,3}.\d[0-9]{1,3}.\d[0-9]{1,3}.[a-z]{3}',regex=True))])>0: 
    #     print(logfile.loc[~(logfile['ip'].str.contains(r'\d{1,3}.\d{2,3}.\d{2,3}.[a-z]{3}',regex=True))])
    #     file['Anomaly'] = 1
    #     print("Anomalies found when in columns : IP address")
    # else:
    #     print("No Anomalies found in columns : IP address")     
    
    return file


# In[8]:

def createSummaryMetric(file, p):
    # Define the aggregation calculations
    aggregations = {
        'date' : {'':'max'},
        'ip' : {'':'max'},
        'cik': { # work on the "duration" column
            'total_accessed_cik': 'count',
            'mostly_accessed_cik': 'max'
        },
        'extention': { # work on the "duration" column
            'total_accessed_extention': 'count',
            'mostly_accessed_extention': 'max'
        },
        'size': {     # Now work on the "date" column
            'max_size': 'max',   # Find the max, call the result "max_date"
            'min_size': 'min',
            'avg_size': 'mean'  # Calculate the date range per group
        },
        'browser': {'max_used_browser':'max'},
    }
    
    f=file.groupby(['date','ip']).agg(aggregations)
    f.to_csv(p,header ='column_names',index=False)
    
# In[9]:

fileDir = os.path.dirname(os.path.realpath('__file__'))
# clearLoggingHandlers()
logger = getLogger(fileDir)
logger.info("Application started....")
#if True :
if len(sys.argv) == 5 and sys.argv[4] in ['0','1']:
    year = sys.argv[1]
    #year = '2003'
    if(validateYear(year, logger)):
        if funCheckDir(os.path.join(fileDir, ('downloads/'+str(year)+'/')), logger) or sys.argv[4] == '0':
            url = getUrl(year)
            html = urlopen(url)
            soup = BeautifulSoup(html,"html.parser")
            logger.info("Downloading files from "+url)
            links_list = soup.findAll('a', text = re.compile("log\d{6}01.zip"))
            for ele in links_list:
                with urlopen(ele['href']) as zipresp:
                    with ZipFile(BytesIO(zipresp.read())) as zfile:
                        t = trange(100)
                        for i in t:
                            t.set_description(ele['href'])
                            zfile.extractall(os.path.join(fileDir, 'downloads/'+str(year)+'/'))
            logger.info("Files are present in ~downloads/"+str(year)+'/')
            
            #################################################################################################
            logger.info("Working on missingdata analysis and anomaly detection.")
            path = os.path.join(fileDir, ('downloads/'+str(year)+'/'))
            if not os.path.exists(path+'results/'):
                os.makedirs(path+'results/') # making a directory
            files = os.listdir(path)
            i = 1
            p = path + "results/Summary.csv"
            s = path + "results/SummaryMetrics.csv"
            for file in files:
                if file.endswith(".csv"):
                    f = pd.read_csv(path + file)
                    logger.info("Working on "+ file)
                    f = handleMissingValues(f,i)
                    f = checkForAnomalies(f,i)
                    if i==1: 
                        f.to_csv(p,header ='column_names',index=False)
                    else:
                        f.to_csv(p,mode = 'a',header=False,index=False)
                    #createSummaryMetric(f,i,s)
                    logger.info("Finished working on "+ file)
                    i = i+1
            logger.info("Creating a summary matrix..")
            # Load data from csv file
            data = pd.read_csv(p)
            t = trange(100)
            for i in t:
                t.set_description("Creating a summary matrix")
            createSummaryMetric(data, s)
            ###################################################################################################
            
            # code to zip the file
            zipFileName = str(year)+'_results.zip'
            logger.info("Creating a zip file" + zipFileName)
            newZip = zipfile.ZipFile(zipFileName,'a')
            pathForOutPut = os.path.join(fileDir, ('downloads/'+str(year)+'/results/'))
            for i in os.listdir(pathForOutPut):
                newZip.write(pathForOutPut+i,compress_type=zipfile.ZIP_DEFLATED)
            newZip.close()
            logger.info("Zip file created.")
            
        else :
            logger.info("Files are present in ~downloads/"+str(year)+'/')
        
        try:
            #AWS_ACCESS_KEY_ID = 'AKIAJXFO7F5Z572AAFZQ'
            AWS_ACCESS_KEY_ID = sys.argv[2]
            #AWS_SECRET_ACCESS_KEY = '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'
            AWS_SECRET_ACCESS_KEY = sys.argv[3]

            bucket_name = str(year) + '_results_'+str(int(round(time.time()))) + '-dump'
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
                    AWS_SECRET_ACCESS_KEY)


            bucket = conn.create_bucket(bucket_name,
                location=boto.s3.connection.Location.DEFAULT)
            logger.info("Uploading zip file "+ 'zipFileName' + " on AWS S3..")

            k = Key(bucket)
            k.key = 'table_data'
            k.set_contents_from_filename(str(year)+'_results.zip')
            logger.info("Table data can be found in - bucket_name : "+bucket_name+" and key : "+k.key)

            k = Key(bucket)
            k.key = 'log_data'
            k.set_contents_from_filename('ques2.log')

            logger.info("Logs can be found in - bucket_name : "+bucket_name+" and key : "+k.key)
            conn.close()
        except:
            logger.error("Either AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY or both are invalid!")
            conn.close()
    else :
        logger.warning("Please enter valid year")
else  :
    logger.error("You have entered wrong python command.")
    logger.info("Please pass a command as : python <python_script_name>.py <year> <AWS_ACCESS_KEY_ID> <AWS_SECRET_ACCESS_KEY> <use cache[0/1]>")
logger.info("Application finished....")
logging.shutdown()

