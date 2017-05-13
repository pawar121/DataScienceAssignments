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
    df.dropna(how = 'all', inplace = True)
    df.dropna(thresh = 2, inplace = True)
    del df['Zip Code']
    df = df[pd.notnull(df['State'])]

    #deriving issue_month and issue_year from the issue_d column
    df['Application Year'] = df['Application Date'].dt.year
    df['Application Month'] = df['Application Date'].dt.month

    df['Debt-To-Income Ratio'] = df['Debt-To-Income Ratio'].apply(lambda x: float(x.rstrip("%")))
    df['Employment Length'] = df['Employment Length'].str.extract('(\d+)')
    df['Employment Length'] = df['Employment Length'].fillna(0).astype(int)
    df['Risk_Score'] = df['Risk_Score'].fillna(111).astype(int)
    df['Risk_Score'].replace(0, 111,inplace=True)
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
            # logger.info("Working on file: " + filename + '....')
            print("Working on file: " + filename + '....')
            df = funCleanNFillMissingDeclinedData(os.path.join(directory, filename))
            dfLoanDecData =  pd.concat([df, dfLoanDecData], ignore_index=True)

    logger.info("Mapping FICO & Vantage Scores..")
    logger.info("Working on records after : " + str(datetime.date(year=2013,month=11,day=5)))
    dfVantage = dfLoanDecData[(dfLoanDecData['Application Date'] >= datetime.date(year=2013,month=11,day=5))]
    bins = [0,500,570,590,610,630,650,670,690,710,730,750,770,790,810,830,850,870,890,910,930,990]
    groupNames = ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']
    dfVantage['RiskCategories_Code'] = pd.cut(pd.to_numeric(dfVantage['Risk_Score'], errors='coerce'), bins, labels=groupNames)
    dfVantage['RiskCategories_Code'] = (dfVantage['RiskCategories_Code']).astype(int)
    dfVantage['RiskCategory'] = pd.cut(pd.to_numeric(dfVantage['Risk_Score'], errors='coerce'), bins)
    dfVantage['RiskCategory'] = (dfVantage['RiskCategory']).astype(str)
    dfVantage['RiskCategory'] = dfVantage['RiskCategory'].map(lambda x: x.lstrip('(').rstrip(']'))
    dfVantage['RiskCategory'] = dfVantage['RiskCategory'].str.split(',')
    dfVantage['Risk_Score_From'] = (dfVantage['RiskCategory'].str[0]).astype(int)
    dfVantage['Risk_Score_To'] = ((dfVantage['RiskCategory'].str[1]).map(lambda x: x.strip())).astype(int)
    del dfVantage['RiskCategory']

    logger.info("Working on records before : " + str(datetime.date(year=2013,month=11,day=5)))
    dfFico = dfLoanDecData[(dfLoanDecData['Application Date'] < datetime.date(year=2013,month=11,day=5))]
    bins = [0,299,508,527,545,563,581,599,617,635,654,672,690,708,726,744,762,780,799,817,835,850]
    groupNames = ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']
    dfFico['RiskCategories_Code'] = pd.cut(pd.to_numeric(dfFico['Risk_Score'], errors='coerce'), bins, labels=groupNames)
    dfFico['RiskCategories_Code'] = (dfFico['RiskCategories_Code']).astype(int)
    dfFico['RiskCategory'] = pd.cut(pd.to_numeric(dfFico['Risk_Score'], errors='coerce'), bins)
    dfFico['RiskCategory'] = (dfFico['RiskCategory']).astype(str)
    dfFico['RiskCategory'] = dfFico['RiskCategory'].map(lambda x: x.lstrip('(').rstrip(']'))
    dfFico['RiskCategory'] = dfFico['RiskCategory'].str.split(',')
    dfFico['Risk_Score_From'] = (dfFico['RiskCategory'].str[0]).astype(int)
    dfFico['Risk_Score_To'] = ((dfFico['RiskCategory'].str[1]).map(lambda x: x.strip())).astype(int)
    del dfFico['RiskCategory']

    logger.info("Combining all the records..")
    dfLoanDecData =  pd.concat([dfVantage, dfFico], ignore_index=True)

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
