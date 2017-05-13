#improting all the required packages
import urllib.response
import urllib.request
from bs4 import BeautifulSoup
from urllib.request import urlopen
import logging
import csv
import os
from zipfile import ZipFile
from io import BytesIO
import luigi
import warnings
warnings.filterwarnings('ignore')

#function to generate the loggs
def getLogger(dir):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    handler = logging.FileHandler(dir)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

#function to check is directory exists
def funCheckDir(filepath):
    directory = os.path.dirname(filepath) # defining directory path
    if not os.path.exists(directory): # checking if directory already exists
        os.makedirs(directory) # making a directory
        return False
    else :
        return True


#function to perform aggregations
def main():
    #defining the file-directory
    fileDir = os.path.dirname(os.path.realpath('__file__'))

    #Logging started
    logFilePath = fileDir+'/Logs/download_loan_data.log'
    funCheckDir(logFilePath)
    logger = getLogger(logFilePath)
    logger.info("Application started....")

    #defining base ulrs
    url = 'https://www.lendingclub.com/info/download-data.action'
    baseURL = 'https://resources.lendingclub.com/'

    #opening an url and creating a soup
    logger.info("Opening an url and creating a soup")
    html = urlopen(url)
    soup = BeautifulSoup(html,"html.parser")

    #working on Loan Stats Data
    logger.info("Working on Loan Stats Data")
    #getting file extentions
    loanStatFileExtn = soup.find( 'div' , { 'id' : 'loanStatsFileNamesJS' }).text
    loanStatFileExtn = loanStatFileExtn.split('|')
    #getting file names
    loanStatNames = [str(x.text) for x in soup.find(id="loanStatsDropdown").find_all('option')]
    #combining names and files
    loanStats = list(zip(loanStatFileExtn, loanStatNames))
    logger.info("Total number of Loan Stats Data files : " + str(len(loanStats)))


    #downloading Loan Stats Data
    logger.info("Downloading Loan Stats Data...")
    for (extn, name) in loanStats:
        path = os.path.join(fileDir, 'Downloads/LoanData/'+str(name)+'/')
        if funCheckDir(path):
            continue
        else:
            logger.info("Downloading data for " + str(name))
            with urlopen(baseURL + extn) as zipresp:
                with ZipFile(BytesIO(zipresp.read())) as zfile:
                    zfile.extractall(path)

    logger.info("Loan data location - " + os.path.join(fileDir, 'Downloads/LoanData/'))

    #Logging finished
    logger.info("Application finished....")
    logging.shutdown()

class Download_loan_data(luigi.Task):
    def requires(self):
        return None

    def output(self):
        return{
        'output1' : luigi.LocalTarget('Downloads/LoanData/2007 - 2011/LoanStats3a.csv'),\
        'output2' : luigi.LocalTarget('Downloads/LoanData/2012 - 2013/LoanStats3b.csv'),\
        'output3' : luigi.LocalTarget('Downloads/LoanData/2014/LoanStats3c.csv'),\
        'output4' : luigi.LocalTarget('Downloads/LoanData/2015/LoanStats3d.csv'),\
        'output5' : luigi.LocalTarget('Downloads/LoanData/2016 Q1/LoanStats_2016Q1.csv'),\
        'output6' : luigi.LocalTarget('Downloads/LoanData/2016 Q2/LoanStats_2016Q2.csv'),\
        'output7' : luigi.LocalTarget('Downloads/LoanData/2016 Q3/LoanStats_2016Q3.csv'),\
        'output8' : luigi.LocalTarget('Downloads/LoanData/2016 Q4/LoanStats_2016Q4.csv')
        }

    def run(self):
        main()
