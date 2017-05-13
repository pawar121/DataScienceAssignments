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
    df = pd.read_csv(loanDataCSVPath, skiprows=1)

    #return data frame
    return df

def funCleanNFillMissingLoanData(df):

    #removing string 'months' from term and convertinng into int
    df['term'] = (df['term'].str.extract('(\d+)')).astype(int)

    #extracting number from emp_length and convertinng into int
    df['emp_length'] = df['emp_length'].str.extract('(\d+)')
    df['emp_length'] = df['emp_length'].fillna(0).astype(int)

    #removing '%' from int_rate and converting into float
    df['int_rate'] = df['int_rate'].apply(lambda x: float(x.rstrip("%")))

    #removing '%' from int_rate and converting into float
    df['revol_util'] = df['revol_util'].astype(str)
    df['revol_util'] = df['revol_util'].apply(lambda x: float(x.rstrip("%")))

    #deriving a column cr_line_history, to show how old is credit history
    df['earliest_cr_line'] = df['earliest_cr_line'].fillna(df['issue_d'])

    df['earliest_cr_line'] = df['earliest_cr_line'].str.split('-')
    df['cr_line_month'] = df['earliest_cr_line'].str[0]
    df['cr_line_year'] = (df['earliest_cr_line'].str[1]).astype(int)
    del df['earliest_cr_line']

    #deriving issue_month and issue_year from the issue_d column
    df['issue_d'] = df['issue_d'].str.split('-')
    df['issue_month'] = df['issue_d'].str[0]
    df['issue_year'] = (df['issue_d'].str[1]).astype(int)
    del df['issue_d']

    #filling NaN with 'Unknown'
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

    df['cr_line_history'] = df['issue_year'] - df['cr_line_year']

    df['fico_range_avg'] = (df[['fico_range_high', 'fico_range_low']].mean(axis=1)).round()

    df['last_fico_avg'] = (df[['last_fico_range_high', 'last_fico_range_low']].mean(axis=1)).round()
    df['last_fico_avg'].fillna(df['fico_range_avg'], inplace=True)
    df['last_fico_avg'] = np.where(df['last_fico_avg'] == 0, df['fico_range_avg'], df['last_fico_avg'])

    #return data frame
    return df

#function to categorize the columns
def funCategorizeLoanData(df):

    #'bad' loan_status
    bad_loan_status_indicators = ["Charged Off",
                    "Default",
                    "Does not meet the credit policy. Status:Charged Off",
                    "In Grace Period",
                    "Default Receiver",
                    "Late (16-30 days)",
                    "Late (31-120 days)"]
    #creating a binary column for the bad Loan Status
    df['loan_status_binary'] = np.where(df['loan_status'].isin(bad_loan_status_indicators) , 0, 1)

    #'bad' home_ownership
    bad_home_ownership_indicators = ["RENT",
                    "NONE",
                    "OTHER",
                    "ANY"]

    #creating a binary column for the bad Loan Status
    df['home_ownership_binary'] = np.where(df['home_ownership'].isin(bad_home_ownership_indicators) , 0, 1)

    #assuming 'Verified' and 'Verified Source' means the same
    df['verification_status_binary'] = np.where(df['verification_status'] == 'Not Verified' , 0, 1)

    #converting to category
    df['application_type_binary'] = (df['application_type']).astype('category')

    #creating bins based on quantiles and converting to category
    df['loan_amnt_category'] = (pd.qcut(df['loan_amnt'], 10)).astype(str)
    df['loan_amnt_category_code'] = (pd.qcut(df['loan_amnt'], 10)).astype('category')
    df['loan_amnt_category'] = df['loan_amnt_category'].map(lambda x: x.lstrip('(').rstrip(']').lstrip('['))
    df['loan_amnt_category'] = df['loan_amnt_category'].str.split(',')
    df['loan_amnt_From'] = (df['loan_amnt_category'].str[0])
    df['loan_amnt_To'] = ((df['loan_amnt_category'].str[1]).map(lambda x: x.strip()))
    del df['loan_amnt_category']

    df['annual_inc_category'] = (pd.qcut(df['annual_inc'], 10)).astype(str)
    df['annual_inc_category_code'] = (pd.qcut(df['annual_inc'], 10)).astype('category')
    df['annual_inc_category'] = df['annual_inc_category'].map(lambda x: x.lstrip('(').rstrip(']').lstrip('['))
    df['annual_inc_category'] = df['annual_inc_category'].str.split(',')
    df['annual_inc_From'] = (df['annual_inc_category'].str[0])
    df['annual_inc_To'] = ((df['annual_inc_category'].str[1]).map(lambda x: x.strip()))
    del df['annual_inc_category']

    bins = [0,299,508,527,545,563,581,599,617,635,654,672,690,708,726,744,762,780,799,817,835,850]
    groupNames = ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']
    df['Credit_Score_Code'] = pd.cut(pd.to_numeric(df['fico_range_avg'], errors='coerce'), bins, labels=groupNames)
    df['Credit_Score_Code'] = (df['Credit_Score_Code']).astype(int)
    df['Credit_Score_Category'] = pd.cut(pd.to_numeric(df['fico_range_avg'], errors='coerce'), bins)
    df['Credit_Score_Category'] = (df['Credit_Score_Category']).astype(str)
    df['Credit_Score_Category'] = df['Credit_Score_Category'].map(lambda x: x.lstrip('(').rstrip(']'))
    df['Credit_Score_Category'] = df['Credit_Score_Category'].str.split(',')
    df['Credit_Score_From'] = (df['Credit_Score_Category'].str[0]).astype(int)
    df['Credit_Score_To'] = ((df['Credit_Score_Category'].str[1]).map(lambda x: x.strip())).astype(int)
    del df['Credit_Score_Category']

    df['Last_Credit_Score_Code'] = pd.cut(pd.to_numeric(df['last_fico_avg'], errors='coerce'), bins, labels=groupNames)
    df['Last_Credit_Score_Code'] = (df['Last_Credit_Score_Code']).astype(int)

    #converting all the category columns to int by taking category-code
    cat_columns = df.select_dtypes(['category']).columns
    df[cat_columns] = df[cat_columns].apply(lambda x: x.cat.codes)

    #return data frame
    return df


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
            if filename == 'LoanStats3a_securev1.csv':
                logger.info("Working on file: " + filename + '....')
                # print("Working on file: " + filename + '....')
                df = funConsolidateLoanData(os.path.join(directory, filename))

                df.drop(['zip_code'], axis = 1, inplace = True)
                df.drop(['url'], axis = 1, inplace = True)
                df.drop(['desc'], axis = 1, inplace = True)
                df.drop(['emp_title'], axis = 1, inplace = True)

                idx = df[df['id'] == 'Loans that do not meet the credit policy'].index
                df = df[:39786]

                df.dropna(how = 'all', inplace = True)
                df.dropna(thresh = 2, inplace = True)

                dfLoanData =  pd.concat([df, dfLoanData], ignore_index=True)
            else:
                logger.info("Working on file: " + filename + '....')
                # print("Working on file: " + filename + '....')
                df = funConsolidateLoanData(os.path.join(directory, filename))
                df.drop(['zip_code'], axis = 1, inplace = True)
                df.drop(['url'], axis = 1, inplace = True)
                df.drop(['desc'], axis = 1, inplace = True)
                df.drop(['emp_title'], axis = 1, inplace = True)

                df.dropna(how = 'all', inplace = True)
                df.dropna(thresh = 2, inplace = True)
                dfLoanData =  pd.concat([df, dfLoanData], ignore_index=True)

    #dropping columns having more than 10% of rows as NaN
    logger.info("Dropping columns having more than '10%' of rows as NaN")
    dfLoanData = dfLoanData.dropna(thresh=len(dfLoanData) * 0.9, axis=1)

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
