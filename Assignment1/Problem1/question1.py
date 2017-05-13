
# coding: utf-8

# In[1]:

import urllib.response
import urllib.request
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import logging
import csv
import string
from string import punctuation
import sys
import os
import zipfile
import glob
import boto
import boto.s3
import sys
from boto.s3.key import Key
import time


# In[2]:

def validateCIK(cik):
    cik = str(cik)
    if not cik.isdigit() or len(cik) > 10:
        return False
    else :
        return True


# In[3]:

def getLogger(dir):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    # create a file handler
    handler = logging.FileHandler(fileDir+'/ques1.log')
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)
    return logger


# In[4]:

def validateAccession(accession):
    patternAcc = re.compile("\d{10}-\d{2}-\d{6}")
    accession = str(accession)
    if not re.match(patternAcc, accession):
        return False
    else :
        return True


# In[5]:

def generateURL(cik_number, accession_number, base_url = "https://www.sec.gov/Archives/edgar/data/"):
    patternAcc = re.compile("\d{10}-\d{2}-\d{6}")
    cik = str(cik_number)
    accession = str(accession_number)
    accession = ''.join(ch.strip('-') for ch in accession)
    new_url = base_url + cik.lstrip("0") + "/" + accession+ "/"+ accession_number + "-index.htm" 
    return new_url


# In[6]:

def generateFormUrl(url):
    html = urlopen(url) 
    soup = BeautifulSoup(html,"html.parser")  
    table = soup.find( "table", {"class":"tableFile" , "summary": "Document Format Files"} )
    rows = {}
    for table_row in table.findAll("tr"):
        cells = table_row.findAll('td')
        if len(cells) > 0:    
            d = cells[1].text
            doc = cells[2].text
            t = cells[3].text
            r = {'description':d , 'document':doc ,'type':t}
            if r['type'] == '10-Q' and (r['document'][-4:] == '.htm' or r['document'][-5:] == '.html'):
                logger.info("10-Q format tables found")
                rows = r
                break 
            elif r['type'] == '10-K' and (r['document'][-4:] == '.htm' or r['document'][-5:] == '.html'):
                logger.info("10-K format tables found")
                rows = r 
                break 

    if(rows) :
        a = rows['document']
        url_new = url.rpartition('/')[0] + "/" + a
        return url_new
    else :
        logger.warning("Tables are neither in 10Q nor in 10k format.") 
        return "bad_url"


# In[7]:

def funCheckDir(filepath):
    directory = os.path.dirname(filepath) # defining directory path
    logger.info("Checking if files are already present in cache!")
    if not os.path.exists(directory): # checking if directory already exists
        logger.info("Files need to be downloaded.")
        os.makedirs(directory) # making a directory
        return True
    else :
        return False


# In[8]:

#url = generateURL("51143","0000051143-13-000007")
# 0001652044-17-000008   1652044
# calling function to generate 10Q and 10K URL
#cik = input("Please enter a valid CIK : ")
fileDir = os.path.dirname(os.path.realpath('__file__'))
logger = getLogger(fileDir)
logger.info("Application started....")
if len(sys.argv) == 6 and sys.argv[5] in ['0','1']:
#if True:
    cik = sys.argv[1]
    #cik = '1038773'
    if validateCIK(cik):
        accession = sys.argv[2]
        #accession = '0001426588-15-000006'
        if validateAccession(accession):
            url = generateURL(cik,accession)
            logger.info("URL generated : "+url)
            url2 = generateFormUrl(url)
            logger.info("URL generated : "+url2)
        else :
            logger.error(accession+" accession number is not valid!")
    else :
        logger.error(str(cik)+"CIK is not valid!")
else :
    logger.error("You have entered wrong python command.")
    logger.error("Please pass a command as : python <python_script_name>.py <CIK> <accession_number> <use cache[0/1]>")


# In[9]:

accession = ''.join(ch.strip('-') for ch in accession)   


# In[10]:

if url2 != 'bad_url':
    if funCheckDir(os.path.join(fileDir, ('downloads/'+str(cik)+'/'+accession+'/'))) or sys.argv[5] == '0':
        html = urlopen(url2)
        soup = BeautifulSoup(html,"html.parser")


        logger.info("Parsing above url to find table..")

        all_tables = soup.find_all("table")
        tables = []
        for table in all_tables:
            columns = table.find_all('td')
            for column in columns:
                if (str(column.attrs.get('style')) != "None" and 'background' in str(column.attrs.get('style'))) or column.text.find('$') > -1 or column.text.find('%') > -1:
                    tables.append(table)
                    break
        logger.info(str(len(tables))+" tables found..")
        i = 1
        for table in tables:
            data = []
            all_rows = table.find_all('tr')
            for row in all_rows:
                cols = row.find_all('td')
                cols = [(''.join(ch.strip('[\n,$]') for ch in ele.text if ch not in string.punctuation)).strip() for ele in cols]
                data.append([ele for ele in cols if ele]) 
            write_file = open(os.path.join(fileDir, ('downloads/'+str(cik)+'/'+accession+'/'))+'csv' +str(i)+ '.csv', 'w')
            i = i + 1
            for row in data:
                for column in row:
                    write_file.write(column)
                    write_file.write(',')
                write_file.write('\n')
            write_file.close()
        logger.info("Files are present in ~downloads/"+str(cik)+'/'+accession+'/')

        # code to zip the file
        zipFileName = cik+'_'+accession+'.zip'
        logger.info("Creating a zip file" + zipFileName)
        newZip = zipfile.ZipFile(zipFileName,'a')
        pathForOutPut = os.path.join(fileDir, ('downloads/'+str(cik)+'/'+accession+'/'))
        for i in os.listdir(pathForOutPut):
            newZip.write(pathForOutPut+i,compress_type=zipfile.ZIP_DEFLATED)
        newZip.close()
        logger.info("Zip file created.")
    else :
        logger.info("Files are present in ~downloads/"+str(cik)+'/'+accession+'/')
    try:
        #AWS_ACCESS_KEY_ID = 'AKIAJXFO7F5Z572AAFZQ'
        AWS_ACCESS_KEY_ID = sys.argv[3]
        #AWS_SECRET_ACCESS_KEY = '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'
        AWS_SECRET_ACCESS_KEY = sys.argv[4]

        bucket_name = cik+'_'+accession +'_'+ str(int(round(time.time()))) + '-dump'
        conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
                AWS_SECRET_ACCESS_KEY)


        bucket = conn.create_bucket(bucket_name,
            location=boto.s3.connection.Location.DEFAULT)
        logger.info("Uploading zip file "+ 'zipFileName' + " on AWS S3..")

        k = Key(bucket)
        k.key = 'table_data'
        k.set_contents_from_filename(cik+'_'+accession+'.zip')
        logger.info("Table data can be found in - bucket_name : "+bucket_name+" and key : "+k.key)

        k = Key(bucket)
        k.key = 'log_data'
        k.set_contents_from_filename('ques1.log')

        logger.info("Logs can be found in - bucket_name : "+bucket_name+" and key : "+k.key)
        conn.close()
    except:
        logger.error("Either AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY or both are invalid!")
        conn.close()
    logger.info("Application finished....")
    logging.shutdown()
else :
    logger.error("Since table format is not matching...exiting")
    logger.info("Application finished....")
    logging.shutdown()

