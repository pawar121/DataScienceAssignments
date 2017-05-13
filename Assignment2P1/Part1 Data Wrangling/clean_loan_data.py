#improting all the required packages
import logging
import csv
import os
import numpy as np
import pandas as pd
import luigi
from download_loan_data import Download_loan_data
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

#function to write the data in chunks
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def funConsolidateLoanData(loanDataCSVPath):

    #reading data from CSV
    df = pd.read_csv(loanDataCSVPath, skiprows=1, parse_dates=['earliest_cr_line', 'issue_d'])
    #return data frame
    return df

def funCleanNFillMissingLoanData(df):

    #'bad' statuses
    bad_indicators = ["Charged Off ",
                    "Default",
                    "Does not meet the credit policy. Status:Charged Off",
                    "In Grace Period",
                    "Default Receiver",
                    "Late (16-30 days)",
                    "Late (31-120 days)"]

    # df = df[df['id'].apply(lambda x: str(x).isdigit())]

    #creating a binary column for the bad Loan Status
    df['loan_status_binary'] = np.where(df['loan_status'].isin(bad_indicators) , 1, 0)

    #removing string 'months' from term and convertinng into int
    df['term'] = (df['term'].str.extract('(\d+)')).astype(int)

    #extracting number from emp_length and convertinng into int
    df['emp_length'] = df['emp_length'].str.extract('(\d+)')
    df['emp_length'] = df['emp_length'].fillna(0).astype(int)

    #removing '%' from int_rate and converting into float
    df['int_rate'] = df['int_rate'].apply(lambda x: float(x.rstrip("%")))

    #deriving issue_month and issue_year from the issue_d column
    df['issue_month'] = df['issue_d'].dt.month
    df['issue_year'] =  df['issue_d'].dt.year
    #del df['issue_d']

    #assuming 'Verified' and 'Verified Source' means the same
    df['verification_status'] = np.where(df['verification_status'] == 'Not Verified' , 0, 1)

    #filling NaN with 'Unknown'
    df['emp_title'] = df['emp_title'].fillna('Unknown')
    df['title'] = df['title'].fillna('Unknown')

    #filling NaN with 0
    df['delinq_2yrs'] = df['delinq_2yrs'].fillna(0)
    df['inq_last_6mths'] = df['inq_last_6mths'].fillna(0)

    #filling NaN with mode
    df['open_acc'] = df['open_acc'].fillna(df['open_acc'].mode())
    df['pub_rec'] = df['pub_rec'].fillna(df['pub_rec'].mode())
    df['total_acc'] = df['total_acc'].fillna(df['total_acc'].mode())
    df['collections_12_mths_ex_med'] = df['collections_12_mths_ex_med'].fillna(df['collections_12_mths_ex_med'].mode())
    df['acc_now_delinq'] = df['acc_now_delinq'].fillna(df['acc_now_delinq'].mode())
    df['tot_coll_amt'] = df['tot_coll_amt'].fillna(df['tot_coll_amt'].mode())
    df['tot_cur_bal'] = df['tot_cur_bal'].fillna(df['tot_cur_bal'].mode())
    df['total_rev_hi_lim'] = df['total_rev_hi_lim'].fillna(df['total_rev_hi_lim'].mode())
    df['acc_open_past_24mths'] = df['acc_open_past_24mths'].fillna(df['acc_open_past_24mths'].mode())
    df['avg_cur_bal'] = df['avg_cur_bal'].fillna(df['avg_cur_bal'].mode())
    df['bc_open_to_buy'] = df['bc_open_to_buy'].fillna(df['bc_open_to_buy'].mode())
    df['bc_util'] = df['bc_util'].fillna(df['bc_util'].mode())
    df['chargeoff_within_12_mths'] = df['chargeoff_within_12_mths'].fillna(df['chargeoff_within_12_mths'].mode())
    df['delinq_amnt'] = df['delinq_amnt'].fillna(df['delinq_amnt'].mode())
    df['mo_sin_old_il_acct'] = df['mo_sin_old_il_acct'].fillna(df['mo_sin_old_il_acct'].mode())
    df['mo_sin_old_rev_tl_op'] = df['mo_sin_old_rev_tl_op'].fillna(df['mo_sin_old_rev_tl_op'].mode())
    df['mo_sin_rcnt_rev_tl_op'] = df['mo_sin_rcnt_rev_tl_op'].fillna(df['mo_sin_rcnt_rev_tl_op'].mode())
    df['mo_sin_rcnt_tl'] = df['mo_sin_rcnt_tl'].fillna(df['mo_sin_rcnt_tl'].mode())
    df['mort_acc'] = df['mort_acc'].fillna(df['mort_acc'].mode())
    df['mths_since_recent_bc'] = df['mths_since_recent_bc'].fillna(df['mths_since_recent_bc'].mode())
    df['num_accts_ever_120_pd'] = df['num_accts_ever_120_pd'].fillna(df['num_accts_ever_120_pd'].mode())
    df['num_actv_bc_tl'] = df['num_actv_bc_tl'].fillna(df['num_actv_bc_tl'].mode())
    df['num_actv_rev_tl'] = df['num_actv_rev_tl'].fillna(df['num_actv_rev_tl'].mode())
    df['num_bc_sats'] = df['num_bc_sats'].fillna(df['num_bc_sats'].mode())
    df['num_bc_tl'] = df['num_bc_tl'].fillna(df['num_bc_tl'].mode())
    df['num_op_rev_tl'] = df['num_op_rev_tl'].fillna(df['num_op_rev_tl'].mode())
    df['num_rev_accts'] = df['num_rev_accts'].fillna(df['num_rev_accts'].mode())
    df['num_rev_tl_bal_gt_0'] = df['num_rev_tl_bal_gt_0'].fillna(df['num_rev_tl_bal_gt_0'].mode())
    df['num_sats'] = df['num_sats'].fillna(df['num_sats'].mode())
    df['num_tl_120dpd_2m'] = df['num_tl_120dpd_2m'].fillna(df['num_tl_120dpd_2m'].mode())
    df['num_tl_30dpd'] = df['num_tl_30dpd'].fillna(df['num_tl_30dpd'].mode())
    df['num_tl_90g_dpd_24m'] = df['num_tl_90g_dpd_24m'].fillna(df['num_tl_90g_dpd_24m'].mode())
    df['num_tl_op_past_12m'] = df['num_tl_op_past_12m'].fillna(df['num_tl_op_past_12m'].mode())
    df['pct_tl_nvr_dlq'] = df['pct_tl_nvr_dlq'].fillna(df['pct_tl_nvr_dlq'].mode())
    df['percent_bc_gt_75'] = df['percent_bc_gt_75'].fillna(df['percent_bc_gt_75'].mode())
    df['pub_rec_bankruptcies'] = df['pub_rec_bankruptcies'].fillna(df['pub_rec_bankruptcies'].mode())
    df['tax_liens'] = df['tax_liens'].fillna(df['tax_liens'].mode())
    df['tot_hi_cred_lim'] = df['tot_hi_cred_lim'].fillna(df['tot_hi_cred_lim'].mode())
    df['total_bal_ex_mort'] = df['total_bal_ex_mort'].fillna(df['total_bal_ex_mort'].mode())
    df['total_bc_limit'] = df['total_bc_limit'].fillna(df['total_bc_limit'].mode())
    df['total_il_high_credit_limit'] = df['total_il_high_credit_limit'].fillna(df['total_il_high_credit_limit'].mode())


    #filling NaN with mean
    df['annual_inc'] = df['annual_inc'].fillna(df['annual_inc'].mean())

    #deriving a column cr_line_history, to show how old is credit history
    df['earliest_cr_line'] = df['earliest_cr_line'].fillna(df['issue_d'])
    df['cr_line_history'] = df['issue_d'].dt.year - df['earliest_cr_line'].dt.year

    #filling NaN with mode
    #df = df.fillna(df.mode())

    #return data frame
    return df

#function to categorize the columns
def funCategorizeLoanData(df):

    #creating bins based on quantiles and converting to category
    df['cat_loan_amnt'] = (pd.qcut(df['loan_amnt'], 5)).astype('category')
    df['cat_annual_inc'] = (pd.qcut(df['annual_inc'], 5)).astype('category')

    #converting to category
    df['application_type'] = (df['application_type']).astype('category')
    df['home_ownership'] = (df['home_ownership']).astype('category')

    #converting all the category columns to int by taking category-code
    cat_columns = df.select_dtypes(['category']).columns
    df[cat_columns] = df[cat_columns].apply(lambda x: x.cat.codes)

    #return data frame
    return df


#

#function to perform aggregations
def main():
    #defining the file-directory
    fileDir = os.path.dirname(os.path.realpath('__file__'))

    #Logging started
    logFilePath = fileDir+'/Logs/missing_data_analysis.log'
    funCheckDir(logFilePath)
    logger = getLogger(logFilePath)
    logger.info("Application started....")

    #cleaning and filling missing loan data started
    loanFilePath = fileDir+'/CleanedData/LoanData.csv'
    funCheckDir(loanFilePath)
    logger.info("Cleaning and filling missing loan data started")

    #defining data frame for the consolidated loan data
    dfLoanData = pd.DataFrame()

    #reading loan data stats
    for directory, subdirectory, filenames in  os.walk(fileDir + '/Downloads/LoanData/'):
        for filename in filenames:
            logger.info("Working on file: " + filename + '....')
            #print("Working on file: " + filename + '....')
            df = funConsolidateLoanData(os.path.join(directory, filename))
            dfLoanData =  pd.concat([df, dfLoanData], ignore_index=True)


    #dropping columns having more than 10% of rows as NaN
    logger.info("Dropping columns having more than '10%' of rows as NaN")
    dfLoanData.dropna(how = 'all', inplace = True)
    dfLoanData.dropna(thresh = 2, inplace = True)
    dfLoanData = dfLoanData.dropna(thresh=len(dfLoanData) * 0.9, axis=1)
    try:
        #removing the comments from the CSV file
        dfLoanData = dfLoanData.drop(['zip_code'], axis = 1)
        dfLoanData = dfLoanData.drop(['desc'], axis = 1)
        dfLoanData = dfLoanData.drop(['url'], axis = 1)
    except:
        pass
    logger.info("Total number of columns under consideration : " + str(len(dfLoanData.columns)))

    #cleaning and filling missing data
    logger.info("Cleaning and filling missing data")
    dfLoanData = funCleanNFillMissingLoanData(dfLoanData)

    #categorizing the columns
    logger.info("Categorizing the columns of loan data")
    dfLoanData = funCategorizeLoanData(dfLoanData)

    #writing data frame to the LoanData.csv
    logger.info("Writing data frame to the LoanData.csv")
    withHeaders = True
    for i in chunker(dfLoanData,50000):
        if(withHeaders):
            i.to_csv(loanFilePath, index=False, mode='a')
            withHeaders = False
        else:
            i.to_csv(loanFilePath, index=False, mode='a', header = False)
    logger.info("Total number of records in loan data : "+str(len(dfLoanData)))
    logger.info("Cleaned Loan data is available at "+loanFilePath)

    #Logging finished
    logger.info("Application finished....")
    logging.shutdown()

class Clean_loan_data(luigi.Task):
    def requires(self):
        return Download_loan_data()

    def output(self):
        return luigi.LocalTarget('CleanedData/LoanData.csv')

    def run(self):
        main()
