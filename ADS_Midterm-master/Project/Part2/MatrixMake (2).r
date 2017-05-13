
library(randomForest)
library(sqldf)
library(ggplot2)
library(MASS)
library(pROC)
library(ROCR)

args <- commandArgs(trailingOnly = TRUE)
quarterinput <- args[1]
setwd("C:/Users/Gautam/Desktop/sumit1/results/historical")
# setwd("results/historical/quarter")   
set.seed(123)
print(getwd())
print(quarterinput)

quarter <- toupper(substr(quarterinput,1,2))
year <- substr(quarterinput,3,6) 
print(quarter)
print(year)
 if(quarter == 'Q4'){
    quarter1 <-'Q1'
    year1 <- as.numeric(year) + 1
	} else {
	nextyear<- toString((as.numeric(substr(quarter,2,3)))+1)
	quarter1 <- paste("Q",nextyear,sep="")
	year1 <- year
	}
 print(quarter1)	
 print(year1) 
#basepath = "/results/historical/quarter+/"
#print(basepath)

trainpath  <- paste(quarterinput,"/historical_data1_time",quarterinput,".csv", sep="")
print(trainpath)
traindata <- read.csv(file= trainpath, nrow = 50000)

testpath  <- paste(quarter1,year1,"/historical_data1_time",quarter1,year1,".csv", sep="")
print(testpath)
testdata <- read.csv(file= testpath, nrow = 50000)	

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

#Building model for the tree 
model_random<- randomForest(CurrentLoadDelinquencyStatus ~ CurrentActualUpb + LoanAge + RemainingMonthsToLegalMaturity +
                RepurchaseFlag + ModificationFlag + ZeroBalanceCode + CurrentInterestRate,
                data = traindata, ntree=20)

#Confusion Matrix				
PredictionWithClass<- predict(model_random,traindata,type='class')
t<- table(predictions = PredictionWithClass, actual = traindata$CurrentLoadDelinquencyStatus)
print(t)				

matrixframe = data.frame(Quarter = character(), NumberofActualDelinquents = character(), NumberofPredictedDelinquents =  character(), 
                         NumberofRecords =  character(), NumberofDel.ProperClassified = character(), 
                         NumberofDeliquentsimproperclassified = character())

 #Fetching data from matrix
 col1 <- quarter
 print(class(t))
 col2 <- t[1,2] + t[2,2]
 col3 <- t[2,1] + t[2,2]
 col4 <- nrow(testdata)
 col5 <- t[2,2]
 col6 <- t[2,1]

newrow = c(col1,col2,col3,col4,col5,col6)
matrixframe = rbind(matrixframe, newrow)

names(matrixframe) <- c("Quarter","NumberofActualDelinquents","NumberofPredictedDelinquents","NumberofRecords","NumberofDel.ProperClassified",
                       "NumberofDeliquentsimproperclassified")

print(matrixframe)
source("MatrixNext.R")
call(quarterinput)