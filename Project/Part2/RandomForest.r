
install.packages("caret",repos = "http://cran.us.r-project.org")
install.packages("randomForest",repos = "http://cran.us.r-project.org")
install.packages("sqldf",repos = "http://cran.us.r-project.org")

library(randomForest)
library(sqldf)
library(ggplot2)
library(MASS)
library(pROC)
library(ROCR)

setwd("results/historical/quarter/")   
# setwd("C:/Users/Gautam/Desktop/sumit1/results/historical/Q22005")   
set.seed(123)

args[2]



abc="historical_data1_timeQ12005.csv" 
bcd="historical_data1_timeQ22005.csv"

#  traindata <- read.csv.sql(file = abc, sql = "select * from file order by random() limit 500000")
   testdata <- read.csv.sql(file = bcd, sql = "select * from file order by random() limit 50000")

#Converting columns into factors for training data
traindata$RepurchaseFlag <- as.factor(traindata$RepurchaseFlag)
traindata$ModificationFlag <- as.factor(traindata$ModificationFlag)
traindata$ZeroBalanceCode <- as.factor(traindata$ZeroBalanceCode)
traindata$CurrentLoadDelinquencyStatus <- as.factor(traindata$CurrentLoadDelinquencyStatus)

#Converting columns into factors for testing data
testdata$RepurchaseFlag <- as.factor(testdata$RepurchaseFlag)
testdata$ModificationFlag <- as.factor(testdata$ModificationFlag)
testdata$ZeroBalanceCode <- as.factor(testdata$ZeroBalanceCode)
testdata$CurrentLoadDelinquencyStatus <- as.factor(testdata$CurrentLoadDelinquencyStatus)

#Building modelfor the tree 
model_random<- randomForest(CurrentLoadDelinquencyStatus ~ CurrentActualUpb + LoanAge + RemainingMonthsToLegalMaturity +
                RepurchaseFlag + ModificationFlag + ZeroBalanceCode + CurrentInterestRate,
                data = traindata, ntree=70)

model_random

importance(model_random)
varImpPlot(model_random)

# Predicting the train data for the response.
PredictionWithClass<- predict(model_random,traindata,type='class')
t<- table(predictions = PredictionWithClass, actual = traindata$CurrentLoadDelinquencyStatus)
t
#Calculating Accuracy through classification matrix
sum(diag(t))/sum(t)

# Predicting the test data for the response.
PredictionWithClass<- predict(model_random,testdata,type='class')
t<- table(predictions = PredictionWithClass, actual = testdata$CurrentLoadDelinquencyStatus)
t

#Calculating Accuracy through classification matrix
sum(diag(t))/sum(t)

# ROC Curve for Train Data 
predictions=as.vector(model_random$votes[,1])
pred=prediction(predictions,traindata$CurrentLoadDelinquencyStatus)
perf_AUC=performance(pred,"auc") #Calculate the AUC value
AUC=perf_AUC@y.values[[1]]
perf_ROC=performance(pred,"tpr","fpr") #plot the actual ROC curve
plot(perf_ROC, main="ROC plot")
text(0.5,0.5,paste("AUC = ",format(AUC, digits=1, scientific=FALSE)))

# ROC Curve for Train Data 
predictions=as.vector(model_random$votes[,1])
pred=prediction(predictions,testdata$CurrentLoadDelinquencyStatus)
perf_AUC=performance(pred,"auc") #Calculate the AUC value
AUC=perf_AUC@y.values[[1]]
perf_ROC=performance(pred,"tpr","fpr") #plot the actual ROC curve
plot(perf_ROC, main="ROC plot")
text(0.5,0.5,paste("AUC = ",format(AUC, digits=1, scientific=FALSE)))
