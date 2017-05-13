
# coding: utf-8

# In[1]:


import requests
from requests import session
import os
from bs4 import BeautifulSoup
import re
from io import BytesIO
from zipfile import ZipFile
import logging
import sys
import pandas as pd
import multiprocessing
import glob
import shutil
import matplotlib
matplotlib.use('Agg')
import pylab as plt


# In[2]:

def getLogger(dir):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    handler = logging.FileHandler(fileDir+'/midtermPart1.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# In[3]:

def getResponse(action, payload, httpSession = None, base_url = 'https://freddiemac.embs.com/FLoan/'):
    if httpSession:
        response = httpSession.post(base_url+action, data=payload)
        return response, httpSession
    else:
        with session() as s:
            response = s.post(base_url+action, data=payload)
        return response, s


# In[4]:

def getLoginPayload(username, password):
    payload = {
        'action': 'auth.php',
        'username': username,
        'password': password
    }
    return payload


# In[5]:

def getTandCPayload():
    payload = {
        'action': 'acceptTandC',
        'accept': 'Yes',
        'acceptSubmit':'Continue'
    }
    return payload


# In[6]:

def funCheckDir(filepath):
    directory = os.path.dirname(filepath) # defining directory path
    if not os.path.exists(directory): # checking if directory already exists
        os.makedirs(directory) # making a directory
        return True
    else :
        return False


# In[7]:

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


# In[8]:

def downloadFiles(ele, logger, fileDir, httpSession):
    response, httpSession = getResponse(action = 'Data/'+ele['href'], payload=None, httpSession = httpSession)
    with ZipFile(BytesIO(response.content)) as zfile:
        logger.info("Downloading and unziping file "+ele.get_text())
        zfile.extractall(os.path.join(fileDir, 'downloads/'+ele.get_text()[7:11]+'/'))


# In[9]:

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


# In[10]:

def readOrigFile(file):
    headerNames = ['CreditScore','FirstPaymentDate','FirstTimeHomeBuyerFlag','MaturityDate','MSA','MIP','NumberOfUnits','OccupancyStatus','OCLTV','DTI','OriginalUPB','OLTV','OriginalInterestRate','Channel','PrepaymentPenaltyFlag','ProductType','PropertyState','PropertyType','PostalCode','LoanSequenceNumber','LoanPurpose','OriginalLoanTerm','NumberOfBorrowers','SellerName','ServicerName','SuperConformingFlag']
    with open(file) as f:
        table = pd.read_table(f, sep='|', low_memory=False, header=None,lineterminator='\n', names= headerNames, converters={'OCLTV': str,'OLTV': str,'DTI': str,'CreditScore': str, 'PostalCode': str, 'SuperConformingFlag' : str})
        return table        


# In[11]:

def leftJoin(dfOrig, dfSCVG):
    return pd.merge(dfOrig, dfSCVG, how='left', on='LoanSequenceNumber')


# In[12]:

def readSVCGFile(file):
    headerNames = ['LoanSequenceNumber','MonthlyReportingPeriod','CurrentActualUpb','CurrentLoadDelinquencyStatus','LoanAge','RemainingMonthsToLegalMaturity','RepurchaseFlag','ModificationFlag','ZeroBalanceCode','ZeroBalanceEffectiveDate','CurrentInterestRate','CurrentDeferredUpb','DueDateOfLastPaidInstallment','MiRecoveries','NetSalesProceeds','NonMiRecoveries','Expenses','LegalCosts','MaintenanceAndPreservationCosts','TaxesAndInsurance','MiscellaneousExpenses','ActualLossCalculation','Modification Cost']
    with open(file) as f:
        table = pd.read_table(f, sep='|', low_memory=False, header=None,lineterminator='\n', names= headerNames, converters={'ZeroBalanceCode':str, 'CurrentLoadDelinquencyStatus':str, 'ModificationFlag':str,'NetSalesProceeds':str, 'LegalCosts':str, 'MaintenanceAndPreservationCosts':str, 'TaxesAndInsurance':str, 'Expenses':str, 'MiscellaneousExpenses':str })
        return table        


# In[13]:

def cleanAndFillMissingOrigData(df, path):
#     try:
#         avgFICO = str(round((pd.to_numeric(df.CreditScore[~ df.CreditScore.str.contains(' ')], errors='ignore')).mean()))
#     except:
#         avgFICO = str(round((pd.to_numeric(df.CreditScore[df.CreditScore != '   '], errors='ignore')).mean()))
    df['CreditScore'].replace({'^\s{1,}':'300'}, regex=True, inplace=True)
    df['DTI'].replace({'   ':'66'}, inplace=True)
    df['OLTV'].replace({'   ':'106'}, inplace=True)
    df['OCLTV'].replace({'   ':'201'}, inplace=True)
    df['SuperConformingFlag'].replace({'':None}, inplace=True)
    df['SuperConformingFlag'].replace({' ':'N'}, inplace=True)
    df.fillna('Unknown', inplace=True)
    if funCheckDir(path):
        withHeaders = True
        for i in chunker(df,10000):
            if(withHeaders):
                i.to_csv(path+'Original.csv', index=False, mode='a')
                withHeaders = False
            else:
                i.to_csv(path+'Original.csv', index=False, mode='a', header = False)
    return df


# In[14]:

def cleanAndFillMissingMaintData(dfSCVG, path):
    dfSCVG['CurrentLoadDelinquencyStatus'].replace({'   ':'UA'}, inplace=True)
    dfSCVG['RepurchaseFlag'].replace({' ':'NA'}, inplace=True)
    dfSCVG['ModificationFlag'].replace({' ':'N'}, inplace=True)
    dfSCVG['ZeroBalanceCode'].replace({'  ':'NA'}, inplace=True)
    #dfSCVG['ZeroBalanceEffectiveDate'].replace({'^\s{1,}':'NA'}, regex=True, inplace=True)
    dfSCVG.loc[~ dfSCVG.ZeroBalanceCode.isin(['3', '9']), 'NetSalesProceeds'] = 'NA'
    dfSCVG.loc[~ dfSCVG.ZeroBalanceCode.isin(['3', '9']), 'LegalCosts'] = 'NA'
    dfSCVG.loc[~ dfSCVG.ZeroBalanceCode.isin(['3', '9']), 'MaintenanceAndPreservationCosts'] = 'NA'
    dfSCVG.loc[~ dfSCVG.ZeroBalanceCode.isin(['3', '9']), 'TaxesAndInsurance'] = 'NA'
    dfSCVG.loc[~ dfSCVG.ZeroBalanceCode.isin(['3', '9']), 'MiscellaneousExpenses'] = 'NA'
#     dfSCVG.replace({'^\s{1,}':'NA'}, regex=True, inplace=True)
    # dfSCVG.replace({'':'UA'}, inplace=True)
    # dfSCVG.fillna('UA', inplace=True)
    if not funCheckDir(path):
        withHeaders = True
        for i in chunker(dfSCVG,50000):
            if(withHeaders):
                i.to_csv(path+'SCVG.csv',  mode='a', index=False)
                withHeaders = False
            else:
                i.to_csv(path+'SCVG.csv',  mode='a', index=False, header = False)
    return dfSCVG


# In[15]:

def createOrigSummaryMetric(df, path):
    # Define the aggregation calculations
    aggregations = {
        'Quarter':{
            '': lambda x:x.value_counts().index[0]
        },
        'CreditCategories':{
            '': lambda x:x.value_counts().index[0]
        },
        'LoanSequenceNumber':{
            'TotalLoansOriginated': 'count'
        },
        'OriginalUPB':{
            'MaxUPB': 'max',
            'AverageUPB': 'mean',
            'MinUPB': 'min'
        },
        'OriginalInterestRate':{
            'MaxRate': 'max',
            'AverageRate': 'mean',
            'MinRate': 'min'
        },
        'OLTV':{
            'MaxLoanToValue': 'max',
#             'AverageLoanToValue': 'mean',
            'MinLoanToValue': 'min'
        },
        'OriginalLoanTerm':{
            'MaxLoanTerm': 'max',
            'AverageLoanTerm': 'mean',
            'MinLoanLoanTerm': 'min'
        },
        'OccupancyStatus':{
            'MostLikelyOccupancyStatus': lambda x:x.value_counts().index[0]
        }
        ,
        'FirstTimeHomeBuyerFlag':{
            'FirstTimeHomeBuyer': lambda x: x[x.str.contains('Y')].count()
        },
        'PrepaymentPenaltyFlag':{
            'PrepaymentPenaltyIncurred': lambda x: x[x.str.contains('Y')].count()
        },
        'Channel':{
            'MostLikelyChannel': lambda x:x.value_counts().index[0]
        }
    }

    f = df.groupby(['Quarter','CreditCategories']).agg(aggregations)
    
    try:
        fig = plt.figure(figsize=(25, 7))
        ax = f[f.CreditCategories != 'Invalid']['LoanSequenceNumber']['TotalLoansOriginated'].plot(kind="bar", alpha=0.6)
        plt.xlabel('')
        plt.xticks(rotation=0)
        plt.ticklabel_format()
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f[f.CreditCategories != 'Invalid']['OriginalUPB']['AverageUPB'],marker='o', c='navy', linewidth=2)
        plt.title('Average UPB vs Total number of loans per FICO per quarter')
        plt.ylabel('UPB')
        plt.legend(['Avg-UPB'], loc='upper left')
        plt.savefig(path+'UPBVsFICO.png')
        
        fig = plt.figure(figsize=(25, 7))
        ax = f[f.CreditCategories != 'Invalid']['LoanSequenceNumber']['TotalLoansOriginated'].plot(kind="bar", alpha=0.6)
        plt.xlabel('')
        plt.xticks(rotation=0)
        plt.ticklabel_format()
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f[f.CreditCategories != 'Invalid']['OriginalInterestRate']['AverageRate'],marker='o', c='navy', linewidth=2)
        plt.title('Average ROI vs Total number of loans per FICO per quarter')
        plt.ylabel('ROI')
        plt.legend(['Avg-ROI'], loc='upper left')
        plt.savefig(path+'ROIVsFICO.png')
        
        
        fig = plt.figure(figsize=(25, 7))
        ax = f[f.CreditCategories != 'Invalid']['LoanSequenceNumber']['TotalLoansOriginated'].plot(kind="bar", alpha=0.6)
        plt.xlabel('')
        plt.xticks(rotation=0)
        plt.ticklabel_format()
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f[f.CreditCategories != 'Invalid']['OriginalLoanTerm']['AverageLoanTerm'],marker='o', c='navy', linewidth=2)
        plt.title('Average Loan-term vs Total number of loans per FICO per quarter')
        plt.ylabel('Months')
        plt.legend(['Avg-Loan-term'], loc='upper left')
        plt.savefig(path+'LoanTermVsFICO.png')
    
    except:
        logger.error("No numeric data found. Cant process graphs.")
    
    if not funCheckDir(path):
        f.to_csv(path+'OrigSummary.csv',header ='column_names',index=False)


# In[16]:

def createPerfDelSummaryMetric(df, path):
    # Define the aggregation calculations
    aggregations = {
        'Quarter':{
            '': lambda x:x.value_counts().index[0]
        },
        'LoanSequenceNumber':{
            'TotalNumberOfDelequentLoans': 'nunique'
        },
        'CurrentActualUpb':{
            'MaxCurrentUPB': 'max',
            'AverageCurrentUPB': 'mean',
            'MinCurrentUPB': 'min'
        },
        'LoanAge':{
            'MostLikelyLoanAgeWhenLoanGoneDelequent1stTime': lambda x:x.value_counts().index[0]
        },
        'CurrentInterestRate':{
            'MostLikelyInterestRateWhenLoanGoneDelequent1stTime': lambda x:x.value_counts().index[0]
        }
    }

    f = df[df.FirstTimeDelinquency == df.MonthlyReportingPeriod].groupby(['Quarter']).agg(aggregations)
    try:
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['CurrentActualUpb']['AverageCurrentUPB'],marker='o', c='navy', linewidth=2)
        plt.title('Average-UPB Per Loan per quarter(when loan noted delequent for the 1st time)')
        plt.ylabel('UPB value')
        plt.legend(['Avg-UPB'], loc='upper left')
        plt.savefig(path+'UPBVsDelLoans.png')
        
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['LoanAge']['MostLikelyLoanAgeWhenLoanGoneDelequent1stTime'],marker='o', c='navy', linewidth=2)
        plt.title('Loan-age Per Loan per quarter(when loan noted delequent for the 1st time)')
        plt.ylabel('Age value')
        plt.legend(['Loan-age'], loc='upper left')
        plt.savefig(path+'AgeVsDelLoans.png')
        
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['CurrentInterestRate']['MostLikelyInterestRateWhenLoanGoneDelequent1stTime'],marker='o', c='navy', linewidth=2)
        plt.title('Current-ROI Per Loan per quarter(when loan noted delequent for the 1st time)')
        plt.ylabel('ROI value')
        plt.legend(['ROI'], loc='upper left')
        plt.savefig(path+'ROIVsDelLoans.png')
    except:
        logger.error("No numeric data found. Cant process graphs.")

    if not funCheckDir(path):
        f.to_csv(path+'PerfDelqSummary.csv',header ='column_names',index=False)


# In[17]:

def createPerfNonDelSummaryMetric(df, path):
    # Define the aggregation calculations
    aggregations = {
        'Quarter':{
            '': lambda x:x.value_counts().index[0]
        },
        'LoanSequenceNumber':{
            'TotalNumberOfNonDelequentLoans': 'nunique'
        },
        'CurrentActualUpb':{
            'MaxCurrentUPB': 'max',
            'AverageCurrentUPB': 'mean',
            'MinCurrentUPB': 'min'
        },
        'LoanAge':{
            'MaxLoanAge': 'max',
            'AvgLoanAge': 'mean',
            'MinLoanAge': 'min'
        },
        'CurrentInterestRate':{
            'MaxInterestRate': 'max',
            'AvgInterestRate': 'mean',
            'MinInterestRate': 'min'
        }
    }

    f = df[df.FirstTimeDelinquency == -1].groupby(['Quarter']).agg(aggregations)
    
    try:
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfNonDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['CurrentActualUpb']['AverageCurrentUPB'],marker='o', c='navy', linewidth=2)
        plt.title('Average-Current-UPB Per Non-delequent Loan per quarter')
        plt.ylabel('UPB value')
        plt.legend(['UPB'], loc='upper left')
        plt.savefig(path+'UPBVsNonDelLoans.png')
        
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfNonDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['LoanAge']['AvgLoanAge'],marker='o', c='navy', linewidth=2)
        plt.title('Average-Loan-Age Per Non-delequent Loan per quarter')
        plt.ylabel('Age value')
        plt.legend(['Loan-Age'], loc='upper left')
        plt.savefig(path+'AgeVsNonDelLoans.png')
        
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfNonDelequentLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['CurrentInterestRate']['AvgInterestRate'],marker='o', c='navy', linewidth=2)
        plt.title('Average-Rate-Of-Interest Per Non-delequent Loan per quarter')
        plt.ylabel('Rate of Interest value')
        plt.legend(['ROI'], loc='upper left')
        plt.savefig(path+'ROIVsNonDelLoans.png')
    except:
        logger.error("No numeric data found. Cant process graphs.")

    if not funCheckDir(path):
        f.to_csv(path+'PerfNonDelqSummary.csv',header ='column_names',index=False)


# In[18]:

def createPerfExpensesSummaryMetric(df, path):
    # Define the aggregation calculations
    aggregations = {
        'Quarter':{
            '': lambda x:x.value_counts().index[0]
        },
        'LoanSequenceNumber':{
            'TotalNumberOfLoans': 'nunique'
        },
        'Expenses':{
            'AvgExpensesIncurredPerLoan': 'mean',
            'MaxExpensesIncurred': 'max',
            'MinExpensesIncurred': 'min'
        },
        'ActualLossCalculation':{
            'AvgActualLossIncurredPerLoan': 'mean',
            'MaxActualLossIncurred': 'max',
            'MinActualLossIncurred': 'min'
        }
    }

    f = df.groupby(['Quarter']).agg(aggregations)
    
    try:
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['Expenses']['AvgExpensesIncurredPerLoan'],marker='o', c='navy', linewidth=2)
        plt.title('Expenses vs Total number of loans per quarter')
        plt.ylabel('Expenses')
        plt.legend(['Avg Expenses'], loc='upper left')
        plt.savefig(path+'ExpensesVsLoans.png')
        
        
        fig = plt.figure()
        ax = f['LoanSequenceNumber']['TotalNumberOfLoans'].plot(kind="bar", alpha=0.7)
        plt.xticks(rotation=0)
        ax2 = ax.twinx()
        ax2.plot(ax.get_xticks(),f['ActualLossCalculation']['AvgActualLossIncurredPerLoan'],marker='o', c='navy', linewidth=2)
        plt.title('Average-Actual-Loss Incurred PerLoan per quarter')
        plt.ylabel('Loss value')
        plt.legend(['Actual-Loss'], loc='upper left')
        plt.savefig(path+'LossVsLoans.png')
    except:
        logger.error("No numeric data found. Cant process graphs.")
    
    if not funCheckDir(path):
        f.to_csv(path+'PerfExpensesSummary.csv',header ='column_names',index=False)


# In[19]:

def processOrigSummary(year, logger, fileDir):
    logger.info("Reading from "+str(year)+" files..")
    origFiles = glob.glob(fileDir+'/downloads/'+year+'/*_orig_*.txt')
    dfOrig= readOrigFile(origFiles[0])
    resultsPath = fileDir+'/results/sampledata/'+str(year)+'/'
    
    logger.info("Cleaning and Missing data analysis..")
    dfOrig = cleanAndFillMissingOrigData(dfOrig, resultsPath)
    logger.info("Cleaned data is available at ~results/sampledata/"+str(year)+"/")
    
    dfOrig['Quarter'] = dfOrig.LoanSequenceNumber.str[4:6]
    dfOrig = dfOrig[dfOrig.CreditScore != 'Unknown']
    
    bins = [299,301, 550, 649, 699, 749, 850]
    groupNames = ['Invalid','Bad', 'Poor', 'Fair', 'Good', 'Excellent']
    categories = pd.cut(pd.to_numeric(dfOrig['CreditScore'], errors='coerce'), bins, labels=groupNames)
    dfOrig['CreditCategories'] = pd.cut(pd.to_numeric(dfOrig['CreditScore'], errors='coerce'), bins, labels=groupNames)
    
    logger.info("Creating summary metrics..")
    createOrigSummaryMetric(dfOrig, resultsPath)
    logger.info("Summary metric is available at ~results/sampledata/"+str(year)+"/")


# In[20]:

def processPerfSummary(year, logger, fileDir):
    logger.info("Reading from "+str(year)+" files..")
    svcgFiles = glob.glob(fileDir+'/downloads/'+year+'/*_svcg_*.txt')
    dfSCVG= readSVCGFile(svcgFiles[0])
    resultsPath = fileDir+'/results/sampledata/'+str(year)+'/'
    
    logger.info("Cleaning and Missing data analysis..")
    dfSCVG = cleanAndFillMissingMaintData(dfSCVG, resultsPath)
    logger.info("Cleaned data is available at ~results/sampledata/"+str(year)+"/")
    
    dfSCVG['Quarter'] = dfSCVG.LoanSequenceNumber.str[4:6]
    
    logger.info("Creating summary metrics..")
    logger.info("Creating summary metrics for delequent loans")
    dfSCVGDel = dfSCVG[~ dfSCVG['CurrentLoadDelinquencyStatus'].isin(['0'])]
    dfSCVGDelUniq = dfSCVGDel.groupby('LoanSequenceNumber')['MonthlyReportingPeriod'].min()
    dfSCVGDelUniq = pd.DataFrame({'LoanSequenceNumber':dfSCVGDelUniq.index, 'FirstTimeDelinquency':dfSCVGDelUniq.values})
    dfSCVG = leftJoin(dfSCVG, dfSCVGDelUniq)
    dfSCVG.fillna(-1, inplace=True)
    createPerfDelSummaryMetric(dfSCVG, resultsPath)
    
    logger.info("Creating summary metrics for non-delequent loans")
    createPerfNonDelSummaryMetric(dfSCVG, resultsPath)
    
    logger.info("Creating summary metrics for expenses incurred on loans")
    tempdf = (dfSCVG[(~ dfSCVG.Expenses.isin(['NA', 'UA'])) & (dfSCVG.ZeroBalanceCode.isin(['03', '09']))])
    tempdf.Expenses = pd.to_numeric(tempdf.Expenses)
    tempdf.ActualLossCalculation = pd.to_numeric(tempdf.ActualLossCalculation)
    createPerfExpensesSummaryMetric(tempdf, resultsPath)
    logger.info("Summary metric is available at ~results/sampledata/"+str(year)+"/")


# In[21]:

fileDir = os.path.dirname(os.path.realpath('__file__'))
logger = getLogger(fileDir)
logger.info("Application started....")
if len(sys.argv) == 4 and sys.argv[3] in ['0','1']:
    username = sys.argv[1]
    password = sys.argv[2]
    payload = getLoginPayload(username, password)
    logger.info("Payload created..")
    response, httpSession = getResponse(action = 'secure/auth.php', payload=payload)
    if(response.status_code == 200):
        soup = BeautifulSoup(response.content, "html.parser")
        h2Text = (soup.find('h2')).get_text()
        if (h2Text == 'Loan-Level Dataset'):
            logger.info(username+" logged in successfully..")
            if funCheckDir(os.path.join(fileDir,'downloads/')) or sys.argv[3] == '0':
                payload = getTandCPayload()
                logger.info("Payload changed..")
                response, httpSession = getResponse(action = 'Data/download.php', payload=payload, httpSession = httpSession)
                soup = BeautifulSoup(response.content, "html.parser")
                links_list = soup.findAll('a', text = re.compile("sample_\d{4}.zip"))
                logger.info(str(len(links_list))+" zip files found.")
                # if __name__ == '__main__':
                #     jobs = []
                #     for ele in links_list:
                #         p = multiprocessing.Process(target=downloadFiles(ele, logger, fileDir, httpSession))
                #         jobs.append(p)
                #         p.start()
                for ele in links_list:
                	downloadFiles(ele, logger, fileDir, httpSession)
                logger.info("Files are present in ~downloads/")
            else:
                logger.info("Files are present in ~downloads/")
            if not funCheckDir(os.path.join(fileDir,'results/')):
                shutil.rmtree(os.path.join(fileDir,'results/'), ignore_errors=True)
            years = get_immediate_subdirectories(fileDir+'/downloads/')
            # if __name__ == '__main__':
            #     jobs = []
            #     for year in years:
            #         logger.info("Accessing "+str(year)+" files..")
            #         p = multiprocessing.Process(target=processOrigSummary(year, logger, fileDir))
            #         jobs.append(p)
            #         p.start()
            # if __name__ == '__main__':
            #     jobs = []
            #     for year in years:
            #         logger.info("Accessing "+str(year)+" files..")
            #         p = multiprocessing.Process(target=processPerfSummary(year, logger, fileDir))
            #         jobs.append(p)
            #         p.start()
            for year in years:
                processOrigSummary(year, logger, fileDir)
                processPerfSummary(year, logger, fileDir)
            logger.info("Results are present in ~results/sampledata/")
        else:
            print('Either username or password or both are wrong..')
    else:
        print('Network error')
else:
    logger.error("You have entered wrong python command.")
    logger.info("Please pass a command as : python <python_script_name>.py <username> <password> <use cache[0/1]>")
logger.info("Application finished....")
logging.shutdown()

