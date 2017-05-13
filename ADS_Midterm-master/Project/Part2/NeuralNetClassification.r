
install.packages("neuralnet", repos = "http://cran.us.r-project.org")

library(neuralnet)
library(sqldf)
library(devtools)
library(nnet)
require(nnet)
library(RMSE)

setwd("C:/Users/Gautam/Desktop/sumit1/results/historical/Q22005")   

# Saving csv data in a variable
abc="historical_data1_timeQ12005.csv" 
bcd="historical_data1_timeQ22005.csv"

#Extracting Random Data
traindata <- read.csv.sql(file = abc, sql = "select * from file order by random() limit 50000")
testdata <- read.csv.sql(file = bcd, sql = "select * from file order by random() limit 50000")

#Normalize Funciton
normalize2 <- function(x) {
  return ((x - min(x)) / (max(x) - min(x))) }

#Dropping unused columns
drops <- c("MonthlyReportingPeriod","RepurchaseFlag","ModificationFlag","ZeroBalanceEffectiveDate")
traindata <- traindata[ , !(names(traindata) %in% drops)]
testdata <- testdata[ , !(names(testdata) %in% drops)]

#Functions to calculate RMSE and MAE
rmse <- function(error)
{
    sqrt(mean(error^2))
}
 
# Function that returns Mean Absolute Error
mae <- function(error)
{
    mean(abs(error))
}

#Normalizing Test and Train Data
datannet_n <- as.data.frame(lapply(traindata, normalize2))
datannet_n <- as.data.frame(lapply(testdata, normalize2))

nn <- neuralnet(CurrentLoadDelinquencyStatus ~ CurrentActualUpb + LoanAge + RemainingMonthsToLegalMaturity + ZeroBalanceCode + CurrentInterestRate,
                data=traindata, hidden = 2, err.fct = "sse",  linear.output = FALSE)

#Plotting neural networks
plot(nn)

#Predicting on Test Data
predict_ann <- compute(nn,testdata[, c("CurrentActualUpb","LoanAge","RemainingMonthsToLegalMaturity","ZeroBalanceCode","CurrentInterestRate")])

MSE.nn <- sum((testdata$CurrentLoadDelinquencyStatus - predict_ann$net.result)^2)/nrow(testdata)

error <- testdata$CurrentLoadDelinquencyStatus - predict_ann$net.result

print(paste("RMSE",rmse(error)))

print(mae(error))

ann_accuracy = c(rmse(error),mae(error),MSE.nn)

names(ann_accuracy) = c('RMSE','MAE','MSE')

ann_accuracy
