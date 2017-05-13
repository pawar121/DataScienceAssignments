
library(randomForest)
library(sqldf)
library(ggplot2)
library(MASS)
library(pROC)
library(ROCR)

args <- commandArgs(trailingOnly = TRUE)
quarter <- args[1]

setwd("C:/Users/Gautam/Desktop/sumit1")
# setwd("results/historical/quarter/")   
set.seed(123)
print(getwd())

basepath = "results/historical/quarter+/"
print(basepath)

traindata <- read.csv(file="results/historical/quarter1/historical_data1_timeQ12005.csv")
testdata <- read.csv(file= "basepath + 'historical_data1_timeQ12005'+quarter+ '.csv'") 

#Converting columns into factors for testing data
testdata$RepurchaseFlag <- as.factor(testdata$RepurchaseFlag)
testdata$ModificationFlag <- as.factor(testdata$ModificationFlag)
testdata$ZeroBalanceCode <- as.factor(testdata$ZeroBalanceCode)
testdata$CurrentLoadDelinquencyStatus <- as.factor(testdata$CurrentLoadDelinquencyStatus)

#Converting columns into factors for training data
traindata$RepurchaseFlag <- as.factor(traindata$RepurchaseFlag)
traindata$ModificationFlag <- as.factor(traindata$ModificationFlag)
traindata$ZeroBalanceCode <- as.factor(traindata$ZeroBalanceCode)
traindata$CurrentLoadDelinquencyStatus <- as.factor(traindata$CurrentLoadDelinquencyStatus)

#Building modelfor the tree 
model_random<- randomForest(CurrentLoadDelinquencyStatus ~ CurrentActualUpb + LoanAge + RemainingMonthsToLegalMaturity +
                RepurchaseFlag + ModificationFlag + ZeroBalanceCode + CurrentInterestRate,
                data = traindata, ntree=20)

PredictionWithClass<- predict(model_random,traindata,type='class')
t<- table(predictions = PredictionWithClass, actual = traindata$CurrentLoadDelinquencyStatus)
t

matrixframe = data.frame(Quarter = character(), NumberofActualDelinquents = character(), NumberofPredictedDelinquents =  character(), 
                         NumberofRecords =  character(), NumberofDel.ProperClassified = character(), 
                         NumberofDeliquentsimproperclassified = character())

 col1 <- quarter
 col2 <- t[1,2] + t[2,2]
 col3 <- t[2,1] + t[2,2]
 col4 <- nrow(testdata)
 col5 <- t[2,2]
 col6 <- t[2,1]

newrow = c(col1,col2,col3,col4,col5,col6)
matrixframe = rbind(matrixframe, newrow)

names(matrixframe) <- c("Quarter","NumberofActualDelinquents","NumberofPredictedDelinquents","NumberofRecords","NumberofDel.ProperClassified",
                       "NumberofDeliquentsimproperclassified")

matrixframe
