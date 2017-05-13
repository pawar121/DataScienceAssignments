#improting all the required packages
import logging
import csv
import os
import datetime
import numpy as np
import pandas as pd
import warnings
import luigi
from sklearn.preprocessing import MinMaxScaler
from clean_declined_loan_data import Clean_declined_loan_data
from clean_loan_data import Clean_loan_data
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

#function to write the data in chunks
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

#function to perform aggregations
def main():
    #defining the file-directory
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    #Logging started
    logFilePath = fileDir+'/Logs/merge_datasets.log'
    funCheckDir(logFilePath)
    logger = getLogger(logFilePath)
    logger.info("Application started....")

    #cleaning and filling missing loan data started
    applicationsFilePath = fileDir+'/CleanedData/Applications.csv'
    funCheckDir(applicationsFilePath)
    logger.info("Merging two data sets started")

    #defining data frame for the consolidated loan data
    dfApproved = pd.DataFrame()
    dfDeclined = pd.DataFrame()

    #reading declined loan data stats
    for directory, subdirectory, filenames in  os.walk(fileDir + '/CleanedData'):
        for filename in filenames:
            if filename == 'LoanData.csv':
                logger.info("Working on file: " + filename + '....')
                dfApproved = pd.read_csv(os.path.join(directory, filename), encoding = 'ISO-8859-1')
            elif filename == 'LoanDeclinedData.csv':
                logger.info("Working on file: " + filename + '....')
                dfDeclined = pd.read_csv(os.path.join(directory, filename), encoding = 'ISO-8859-1')

    #colums to be selected
    select_cols_Loans = ['loan_amnt', 'dti', 'addr_state', 'emp_length', 'issue_year','Credit_Score_Code']
    select_cols_rejLoans = ['Amount Requested', 'Debt-To-Income Ratio', 'State', 'Employment Length', 'Application Year', 'RiskCategories_Code']
    columns = ['AmountRequested', 'DTI', 'State', 'EMPLength', 'AppYear', 'CreditScore', 'LoanApproval']

    #subsetting the data frame to select few columns
    logger.info("Subsetting the data frame to select few columns..")
    dfApproved = dfApproved[select_cols_Loans]
    dfDeclined = dfDeclined[select_cols_rejLoans]

    #creating another column to indicate if loan was approved
    logger.info("Creating another column to indicate if loan was approved..")
    dfApproved['LoanApproval'] = 1
    dfDeclined['LoanApproval'] = 0

    #renaming the columns of DF
    logger.info("Renaming the columns of DF..")
    dfApproved.columns = columns
    dfDeclined.columns = columns

    #combining the two DFs
    logger.info("Combining all the records..")
    dfApplications = pd.concat([dfApproved, dfDeclined], ignore_index=True)

    #writing data frame to the LoanData.csv
    logger.info("Writing data frame to the Applications.csv")
    withHeaders = True
    for i in chunker(dfApplications,100000):
        if(withHeaders):
            i.to_csv(applicationsFilePath, index=False, mode='a')
            withHeaders = False
        else:
            i.to_csv(applicationsFilePath, index=False, mode='a', header = False)

    logger.info("Total number of records in applications loan data : "+str(len(dfApplications)))
    logger.info("Applications-loan data is available at "+decLoanFilePath)

    #Logging finished
    logger.info("Application finished....")
    logging.shutdown()


class Merge_datasets(luigi.Task):
    def requires(self):
        return {
        'input1' : Clean_loan_data(),
        'input2' : Clean_declined_loan_data() }

    def output(self):
        return luigi.LocalTarget('CleanedData/Applications.csv')

    def run(self):
        main()
