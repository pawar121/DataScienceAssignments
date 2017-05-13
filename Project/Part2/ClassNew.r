
install.packages("AER",repos = "http://cran.us.r-project.org")
install.packages("ROCR",repos = "http://cran.us.r-project.org")
install.packages("caret",repos = "http://cran.us.r-project.org")
install.packages(\"Amelia\",repos = \"http://cran.us.r-project.org
install.packages('e1071', repos = "http://cran.us.r-project.org", dependencies=TRUE)
install.packages("caret",
                 repos = "http://cran.r-project.org", 
                 dependencies = c("Depends", "Imports", "Suggests"))

require(data.table)
        library(ff)
        library(AER)
        library(sqldf)
        library(chunked)
        library(Amelia)
        library(caret)
        library(ROCR)

#Setting Path of directory.
setwd("C:/Users/Gautam/Desktop/sumit1/results/historical/Q22005")   

# Saving csv data in a variable
#  abc="historical_data1_timeQ12005.csv" 
bcd="historical_data1_timeQ22005.csv"

# #Reading training and test data from downloaded csv.
# traindata <- fread("historical_data1_timeQ12005.csv", nrow=5000000)
# testdata <- fread("historical_data1_timeQ22005.csv", nrow=5000000)

# traindata <- read.csv.sql(file = abc, sql = "select * from file order by random() limit 50000")
testdata <- read.csv.sql(file = bcd, sql = "select * from file order by random() limit 50000")


# Setting factors of the target variable(CurrentLoadDelinquencyStatus) as 0 and 1 for trainig data.
traindata$CurrentLoadDelinquencyStatus <- factor(traindata$CurrentLoadDelinquencyStatus,
                                   levels=c(0,1),
                                   labels=c("No","Yes"))
table(traindata$CurrentLoadDelinquencyStatus) 

# Setting factors of the target variable(CurrentLoadDelinquencyStatus) as 0 and 1 for testing data.
testdata$CurrentLoadDelinquencyStatus <- factor(testdata$CurrentLoadDelinquencyStatus,
                                   levels=c(0,1),
                                   labels=c("No","Yes"))
table(testdata$CurrentLoadDelinquencyStatus) 

#Building Logistic Regression Model
trainfit <- glm(CurrentLoadDelinquencyStatus ~ CurrentActualUpb + LoanAge + RemainingMonthsToLegalMaturity +
                RepurchaseFlag + ModificationFlag + ZeroBalanceCode + CurrentInterestRate,
                data=traindata, family=binomial(link="logit"))
summary(trainfit)

#ROC curve for traindata
test.probs <- predict(trainfit, traindata, type="response")
prediction <- prediction(test.probs, traindata$CurrentLoadDelinquencyStatus)
performance <- performance(prediction, measure = "tpr", x.measure = "fpr")
plot(performance, main = "ROC Curve for train data", xlab  = "1-Specificity", ylab = "Sensitivity")

#ROC for testdata
test.probs <- predict(trainfit, testdata, type="response")
prediction <- prediction(test.probs, testdata$CurrentLoadDelinquencyStatus)
performance <- performance(prediction, measure = "tpr", x.measure = "fpr")
plot(performance, main = "ROC Curve for test data", xlab  = "1-Specificity", ylab = "Sensitivity")

#Confusion Matrix for Train Data
test.probs <- predict(trainfit, traindata, type="response")
pred <- rep("No", length(test.probs))
pred[test.probs>=0.5] <- "Yes"
table <- table(as.factor(traindata$CurrentLoadDelinquencyStatus), as.factor(pred))
table
sum(diag(table))/sum(table)

#Confusion Matrix for Test Data
test.probs <- predict(trainfit, testdata, type="response")
pred <- rep("No", length(test.probs))
pred[test.probs>=0.5] <- "Yes"
table <- table(as.factor(testdata$CurrentLoadDelinquencyStatus), as.factor(pred))
table

sum(diag(table))/sum(table)
