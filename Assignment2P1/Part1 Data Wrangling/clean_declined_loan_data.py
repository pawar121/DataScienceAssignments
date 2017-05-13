#improting all the required packages
import logging
import csv
import os
import numpy as np
import pandas as pd
import warnings
import luigi
from download_declined_loan_data import Download_declined_loan_data
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

def funCleanNFillMissingDeclinedData(declinedDataCSVPath):
    df = pd.read_csv(declinedDataCSVPath, skiprows=1, parse_dates=['Application Date'])
    del df['Zip Code']
    df = df[pd.notnull(df['State'])]
    df['Application Year'] = df['Application Date'].dt.year
    df['Application Month'] = df['Application Date'].dt.month
    df['Debt-To-Income Ratio'] = df['Debt-To-Income Ratio'].apply(lambda x: float(x.rstrip("%")))
    df['Employment Length'] = df['Employment Length'].str.extract('(\d+)')
    df['Employment Length'] = df['Employment Length'].fillna(0).astype(int)
    df['Risk_Score'] = df['Risk_Score'].fillna(111).astype(int)
    groupNames = ['Invalid','Very High','High','Moderate', 'Low', 'Very Low']
    bins = [110, 299, 400, 600, 700, 800, 991]
    df['RiskCategories'] = pd.cut(pd.to_numeric(df['Risk_Score'], errors='coerce'), bins, labels=groupNames)
    return df

#function to write the data in chunks
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

#function to perform aggregations
def main():
    #defining the file-directory
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    #Logging started
    logFilePath = fileDir+'/Logs/missing_declined_data_analysis.log'
    funCheckDir(logFilePath)
    logger = getLogger(logFilePath)
    logger.info("Application started....")

    #cleaning and filling missing loan data started
    decLoanFilePath = fileDir+'/CleanedData/LoanDeclinedData.csv'
    funCheckDir(decLoanFilePath)
    logger.info("Cleaning and filling missing loan decline data started")

    #defining data frame for the consolidated loan data
    dfLoanDecData = pd.DataFrame()

    #reading declined loan data stats
    for directory, subdirectory, filenames in  os.walk(fileDir + '/Downloads/DeclinedLoans/'):
        for filename in filenames:
            logger.info("Working on file: " + filename + '....')
            df = funCleanNFillMissingDeclinedData(os.path.join(directory, filename))
            dfLoanDecData =  pd.concat([df, dfLoanDecData], ignore_index=True)

    dfLoanDecData.dropna(how = 'all', inplace = True)
    dfLoanDecData.dropna(thresh = 2, inplace = True)

    #writing data frame to the LoanData.csv
    logger.info("Writing data frame to the LoanDeclinedData.csv")
    withHeaders = True
    for i in chunker(dfLoanDecData,50000):
        if(withHeaders):
            i.to_csv(decLoanFilePath, index=False, mode='a')
            withHeaders = False
        else:
            i.to_csv(decLoanFilePath, index=False, mode='a', header = False)

    logger.info("Total number of records in declined loan data : "+str(len(dfLoanDecData)))
    logger.info("Cleaned declined-loan data is available at "+decLoanFilePath)

    #Logging finished
    logger.info("Application finished....")
    logging.shutdown()


class Clean_declined_loan_data(luigi.Task):
    def requires(self):
        return Download_declined_loan_data()

    def output(self):
        return luigi.LocalTarget('CleanedData/LoanDeclinedData.csv')

    def run(self):
        main()
