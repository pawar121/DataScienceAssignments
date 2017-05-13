
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

def validateQuarter(inputQuarter):
    pattern = re.compile("Q\d{5}")
    inputQuarter = str(inputQuarter)
    if not re.match(pattern, inputQuarter.upper()):
        return False
    else :
        return True


# In[8]:

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


# In[9]:

def downloadFiles(ele, logger, fileDir, httpSession):
    response, httpSession = getResponse(action = 'Data/'+ele['href'], payload=None, httpSession = httpSession)
    with ZipFile(BytesIO(response.content)) as zfile:
        logger.info("Downloading and unziping file "+ele.get_text())
        zfile.extractall(os.path.join(fileDir, 'downloads/historical/'+ele.get_text()[-10:-4]+'/'))


# In[10]:

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


# In[11]:

def readOrigFile(file):
    headerNames = ['CreditScore','FirstPaymentDate','FirstTimeHomeBuyerFlag','MaturityDate','MSA','MIP','NumberOfUnits','OccupancyStatus','OCLTV','DTI','OriginalUPB','OLTV','OriginalInterestRate','Channel','PrepaymentPenaltyFlag','ProductType','PropertyState','PropertyType','PostalCode','LoanSequenceNumber','LoanPurpose','OriginalLoanTerm','NumberOfBorrowers','SellerName','ServicerName','SuperConformingFlag']
    with open(file) as f:
        table = pd.read_table(f, sep='|', low_memory=False, header=None,lineterminator='\n', names= headerNames, converters={'PostalCode': str, 'SuperConformingFlag' : str})
        return table


# In[12]:

def cleanAndFillMissingOrigData(df):
        if df['CreditScore'].dtype == object:
            df['CreditScore'].replace({'   ':None}, inplace=True)
            df.CreditScore = pd.to_numeric(df.CreditScore, errors='coerce')
        df = df[pd.notnull(df['CreditScore'])] # no null rows 
        if df['MIP'].dtype == object:
            df['MIP'].replace({'   ':None}, inplace=True)
            df['MIP'].replace({'000':'0'}, inplace=True)
            df.MIP = pd.to_numeric(df.MIP, errors='coerce')
        df['MIP'] = df['MIP'].fillna(df.groupby('CreditScore')['MIP'].transform('mean')) #replaced by mean of credit score group
        df.MIP = df['MIP'].fillna(0)
        df['NumberOfUnits'] = df['NumberOfUnits'].fillna(df['NumberOfUnits'].mode()[0]) #replaced by mode 
        df['IsInMSA'] = df.apply(lambda row: 1 if pd.notnull(row.MSA) else 0, axis=1)
        if df['DTI'].dtype == object:
            df['DTI'].replace({'   ':None}, inplace=True)
            df.DTI = pd.to_numeric(df.DTI, errors='coerce')
        df.DTI = df['DTI'].fillna(df.groupby('CreditScore')['DTI'].transform('mean')) #replaced by mean of credit score group
        df.DTI = df['DTI'].fillna(0) #if group's mean is na - fill with 0
        df['OccupancyStatus'] = df['OccupancyStatus'].fillna(df['OccupancyStatus'].mode()[0]) #replaced by mode
        df['OccupancyStatus'].replace({'O':0}, inplace=True)
        df['OccupancyStatus'].replace({'I':1}, inplace=True)
        df['OccupancyStatus'].replace({'S':2}, inplace=True)
        df['OCLTV'] = df['OCLTV'].fillna(df.groupby('CreditScore')['OCLTV'].transform('mean')) #replaced by mean of credit score group
        df.OCLTV = df['OCLTV'].fillna(0) #if group's mean is na - fill with 0
        df['OLTV'] = df['OLTV'].fillna(df.groupby('CreditScore')['OLTV'].transform('mean')) #replaced by mean of credit score group
        df.OLTV = df['OLTV'].fillna(0) #if group's mean is na - fill with 0
        df['FirstTimeHomeBuyerFlag'] = df['FirstTimeHomeBuyerFlag'].fillna(df['FirstTimeHomeBuyerFlag'].mode()[0]) #replaced by mode
        df['FirstTimeHomeBuyerFlag'].replace({'Y':1}, inplace=True)
        df['FirstTimeHomeBuyerFlag'].replace({'N':0}, inplace=True)
        df['Channel'] = df['Channel'].fillna(df['Channel'].mode()[0]) #replaced by mode
        df['Channel'].replace({'R':0}, inplace=True)
        df['Channel'].replace({'B':1}, inplace=True)
        df['Channel'].replace({'C':2}, inplace=True)
        df['Channel'].replace({'T':3}, inplace=True)
        df['PrepaymentPenaltyFlag'] = df['PrepaymentPenaltyFlag'].fillna(df['PrepaymentPenaltyFlag'].mode()[0]) #replaced by mode
        df['PrepaymentPenaltyFlag'].replace({'Y':1}, inplace=True)
        df['PrepaymentPenaltyFlag'].replace({'N':0}, inplace=True)
        df['LoanPurpose'] = df['LoanPurpose'].fillna(df['LoanPurpose'].mode()[0]) #replaced by mode
        df['LoanPurpose'].replace({'P':0}, inplace=True)
        df['LoanPurpose'].replace({'C':1}, inplace=True)
        df['LoanPurpose'].replace({'N':2}, inplace=True)
        df['NumberOfBorrowers'] = df['NumberOfBorrowers'].fillna(df['NumberOfBorrowers'].mode()[0]) #replaced by mode


        return df

#df = df[np.isfinite(df['EPS'])]


# In[13]:

def processOrigSummary(quarter, logger, fileDir):
    logger.info("Reading from "+str(quarter)+" files..")
    origFiles = glob.glob(fileDir+'/downloads/historical/'+str(quarter)+'/historical_data1_'+str(quarter)+'.txt')
    dfOrig= readOrigFile(origFiles[0])
    resultsPath = fileDir+'/results/historical/'+str(quarter)+'/'
    
    logger.info("Cleaning and Missing data analysis..")
    dfOrig = cleanAndFillMissingOrigData(dfOrig)
    dfOrig=dfOrig[['CreditScore','FirstTimeHomeBuyerFlag','MIP','NumberOfUnits','OccupancyStatus','OCLTV','OLTV','DTI','OriginalInterestRate','OriginalUPB','Channel','PrepaymentPenaltyFlag','LoanPurpose','OriginalLoanTerm','NumberOfBorrowers']]

    if not funCheckDir(resultsPath):
        withHeaders = True
        for i in chunker(dfOrig,10000):
            if(withHeaders):
                i.to_csv(resultsPath+'historical_data1_'+str(quarter)+'.csv', index=False, mode='a')
                withHeaders = False
            else:
                i.to_csv(resultsPath+'historical_data1_'+str(quarter)+'.csv', index=False, mode='a', header = False)
    logger.info("Cleaned data is available at ~results/historical/"+str(quarter)+"/")


# In[19]:

fileDir = os.path.dirname(os.path.realpath('__file__'))
logger = getLogger(fileDir)
logger.info("Application started....")
#if len(sys.argv) == 4 and validateQuarter(sys.argv[3]):
if True:
    allSET = False
    #username = sys.argv[1]
    username = input('Please enter username :')
    #password = sys.argv[2]
    password = input('Please enter password :')
    payload = getLoginPayload(username, password)
    logger.info("Payload created..")
    response, httpSession = getResponse(action = 'secure/auth.php', payload=payload)
    if(response.status_code == 200):
        soup = BeautifulSoup(response.content, "html.parser")
        h2Text = (soup.find('h2')).get_text()
        if (h2Text == 'Loan-Level Dataset'):
            logger.info(username+" logged in successfully..")
            
            #inputQuarter = sys.argv[3]
            inputQuarter = input('Please enter valid quarter :')
            a = inputQuarter
            payload = getTandCPayload()
            logger.info("Payload changed..")
            response, httpSession = getResponse(action = 'Data/download.php', payload=payload, httpSession = httpSession)
            soup = BeautifulSoup(response.content, "html.parser")
            links_list = soup.findAll('a', text = 'historical_data1_'+str(inputQuarter)+'.zip')
            if len(links_list) == 1:
                logger.info('historical_data1_'+str(inputQuarter)+'.zip file found.')
                if funCheckDir(fileDir+'/downloads/historical/'+str(inputQuarter)+'/'):
                    downloadFiles(links_list[0], logger, fileDir, httpSession)
                else:
                    logger.info('historical_data1_'+str(inputQuarter)+'.zip file available in cache.')
                quarter = str(inputQuarter).upper()[:2]
                year = str(inputQuarter)[-4:]
                if quarter == 'Q4':
                    quarter = 'Q1'
                    year = str(int(year)+1)
                else:
                    quarter = 'Q' + str(int(quarter[-1:])+1)
                b = '/results/historical/'+str(inputQuarter)+'/'+'historical_data1_'+str(inputQuarter)+'.csv'    
                c = '/results/historical/'+quarter+year+'/historical_data1_'+quarter+year+'.csv'    
                links_list = soup.findAll('a', text = 'historical_data1_'+quarter+year+'.zip')
                if len(links_list) == 1:
                    logger.info('historical_data1_'+str(quarter+year)+'.zip file found.')
                    if funCheckDir(fileDir+'/downloads/historical/'+str(quarter+year)+'/'):
                        downloadFiles(links_list[0], logger, fileDir, httpSession)
                    else:
                        logger.info('historical_data1_'+str(quarter+year)+'.zip file available in cache.')
                    allSET = True
                else:
                    logger.info("Files not available for "+str(quarter+year)+". Try another quarter!")
                logger.info("Files are present in ~downloads/historical/")
                #write to this file
                file = open('paramater_train.txt','w') 
                file.write(b) 
                file.close() 
                file = open('paramater_test.txt','w') 
                file.write(c) 
                file.close() 
            else:
                logger.info("Files not available for "+str(inputQuarter))
            if allSET:
                if funCheckDir(fileDir+'/results/historical/'+str(inputQuarter)+'/'):
                    processOrigSummary(str(inputQuarter), logger, fileDir)
                else:
                    logger.info("Clean file is present in ~results/historical/"+str(inputQuarter))
                if funCheckDir(fileDir+'/results/historical/'+str(quarter+year)+'/'):
                    processOrigSummary(str(quarter+year), logger, fileDir)
                else:
                    logger.info("Clean file is present in ~results/historical/"+str(quarter+year))
        else:
            print('Either username or password or both are wrong..')
    else:
        print('Network error')
else:
    logger.error("You have entered wrong python command.")
    logger.info("Please pass a command as : python <python_script_name>.py <username> <password> <quarter>")
logger.info("Application finished....")
logging.shutdown()


# In[ ]:

# import rpy2
# from rpy2.robjects.packages import importr
# import rpy2.robjects as ro
# import pandas.rpy.common as com


# In[ ]:

# stats = importr('stats')
# base = importr('base')
# datasets = importr('datasets')
# library = importr('library')


# In[ ]:

# forecast =importr('forecast')
# leaps = importr('leaps')


# In[ ]:

# print(a)
# print(b)
# print(c)

