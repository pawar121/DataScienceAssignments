#improting all the required packages
from __future__ import print_function
import argparse
import mechanicalsoup
from getpass import getpass
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
        try:
            os.remove(filepath)
        except OSError:
            pass
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
    url = 'https://www.lendingclub.com/account/gotoLogin.action'
    # url = 'https://www.lendingclub.com/account/login.action?'

    #ask for login credentials
    username = "spawargautam@gmail.com"
    #username = input("Please provide lending-club username : ")
    password = "Pawar@121"
    #password = input("Please provide lending-club password : ")

    #trying to loging to the lending-club
    logger.info("Trying to loging to the lending-club..")
    browser = mechanicalsoup.Browser()
    login_page = browser.get(url)
    login_form = login_page.soup.find('form', {"id":"member-login"})
    login_form.find("input", {"name" : "login_email"})["value"] = username
    login_form.find("input", {"name" : "login_password"})["value"] = password
    response = browser.submit(login_form, login_page.url)

    if (response.url == 'https://www.lendingclub.com/account/summary.action'):
        logger.info(username + " logged in successfully!")

        url = 'https://www.lendingclub.com/info/download-data.action'
        baseURL = 'https://resources.lendingclub.com/'

        #opening an url and creating a soup
        logger.info("Opening an url and creating a soup..")
        html = browser.get(url)
        soup = BeautifulSoup(html.text,"html.parser")

        #working on Loan Stats Data
        logger.info("Looking for loan-stats data..")
        #getting file extentions
        loanStatFileExtn = soup.find( 'div' , { 'id' : 'loanStatsFileNamesJS' }).text
        loanStatFileExtn = loanStatFileExtn.split('|')
        #getting file names
        loanStatNames = [str(x.text) for x in soup.find(id="loanStatsDropdown").find_all('option')]
        #combining names and files
        loanStats = list(zip(loanStatFileExtn, loanStatNames))
        logger.info("Total number of loan-stats data files : " + str(len(loanStats)))


        #downloading Loan Stats Data
        logger.info("Downloading loan-stats data files...")
        for (extn, name) in loanStats:
            path = os.path.join(fileDir, 'Downloads/LoanData/'+str(name)+'/')
            if funCheckDir(path):
                continue
            else:
                logger.info("Downloading data file for " + str(name))
                with urlopen(baseURL + extn) as zipresp:
                    with ZipFile(BytesIO(zipresp.read())) as zfile:
                        zfile.extractall(path)

        logger.info("Loan data location - " + os.path.join(fileDir, 'Downloads/LoanData/'))

        luigi_completion_text_file = fileDir+'/Luigi/download_loan_data_completed.txt'
        funCheckDir(luigi_completion_text_file)
        text_file = open(luigi_completion_text_file, "w")
        text_file.write("Downloaded declined-loan-stats data files.")
        text_file.close()

        #Logging finished
        logger.info("Application finished....")
        logging.shutdown()

    else:
        logger.info("Either username or password or both are wrong..")
        #Logging finished
        logger.info("Application finished....")
        logging.shutdown()

        try:
            luigi_completion_text_file = fileDir+'/Luigi/download_loan_data_completed.txt'
            os.remove(luigi_completion_text_file)
        except OSError:
            pass

class Download_loan_data(luigi.Task):
    def requires(self):
        return None

    def output(self):
        return luigi.LocalTarget('Luigi/download_loan_data_completed.txt')

    def run(self):
        main()
