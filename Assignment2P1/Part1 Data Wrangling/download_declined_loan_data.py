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
import warnings
import luigi
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
    logFilePath = fileDir+'/Logs/download_declined_loan_data.log'
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

    #working on declined-loan Stats Data
    logger.info("Working on Declined-Loan Stats Data")
    #getting file extentions
    rejLoanStatFileExtn = soup.find( 'div' , { 'id' : 'rejectedLoanStatsFileNamesJS' }).text
    rejLoanStatFileExtn = rejLoanStatFileExtn.split('|')
    #getting file names
    rejLoanStatNames = [str(x.text) for x in soup.find(id="rejectStatsDropdown").find_all('option')]
    #combining names and files
    rejLoanStats = list(zip(rejLoanStatFileExtn, rejLoanStatNames))

    #downloading Loan Stats Data
    logger.info("Downloading Loan Stats Data...")
    for (extn, name) in rejLoanStats:
        path = os.path.join(fileDir, 'Downloads/DeclinedLoans/'+str(name)+'/')
        if funCheckDir(path):
            continue
        else:
            logger.info("Downloading data for " + str(name))
            with urlopen(baseURL + extn) as zipresp:
                with ZipFile(BytesIO(zipresp.read())) as zfile:
                    zfile.extractall(path)

    logger.info("Declined-Loan data location - " + os.path.join(fileDir, 'Downloads/DeclinedLoans/'))

    #Logging finished
    logger.info("Application finished....")
    logging.shutdown()

class Download_declined_loan_data(luigi.Task):
    def requires(self):
        return None

    def output(self):
        return {
        'output1' : luigi.LocalTarget('Downloads/DeclinedLoans/2007 - 2012/RejectStatsA.csv'),\
        'output2' : luigi.LocalTarget('Downloads/DeclinedLoans/2013 - 2014/RejectStatsB.csv'),\
        'output3' : luigi.LocalTarget('Downloads/DeclinedLoans/2015/RejectStatsD.csv'),\
        'output4' : luigi.LocalTarget('Downloads/DeclinedLoans/2016 Q1/RejectStats_2016Q1.csv'),\
        'output5' : luigi.LocalTarget('Downloads/DeclinedLoans/2016 Q2/RejectStats_2016Q2.csv'),\
        'output6' : luigi.LocalTarget('Downloads/DeclinedLoans/2016 Q3/RejectStats_2016Q3.csv'),\
        'output7' : luigi.LocalTarget('Downloads/DeclinedLoans/2016 Q4/RejectStats_2016Q4.csv')
        }

    def run(self):
        main()
