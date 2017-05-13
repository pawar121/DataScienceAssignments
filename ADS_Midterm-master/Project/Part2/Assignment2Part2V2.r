
library(forecast)
library(leaps)
library(neuralnet)
library(sqldf)
require(class)
#install.packages("randomForest",repos = 'http://cran.us.r-project.org')
library(randomForest)
#install.packages('sqldf',repos = 'http://cran.us.r-project.org')
#install.packages('neuralnet',repos = 'http://cran.us.r-project.org')
#install.packages('nnet',repos = 'http://cran.us.r-project.org')

a<-getwd()
location1<-paste(a,'/paramater_train.txt',sep='')
location2<-paste(a,'/paramater_test.txt',sep='')
# location1
# location2

q1 <-readLines(location1, warn = FALSE)
q2 <- readLines(location2, warn = FALSE)
location_train <- paste(a,q1,sep='')
location_test <- paste(a,q2,sep='')
# location_train
# location_test

train = read.csv(location_train)
test = read.csv(location_test)

#Exhaustive Search

#Perform all subset regression, and choose “nbest” model(s) for each number of predictors up to nvmax.

regsubsets.out <-
    regsubsets(OriginalInterestRate ~.,
               data = train,
               nbest = 1,       # 1 best model for each number of predictors
               nvmax = 5,    # NULL for no limit on number of variables
               force.in = NULL, force.out = NULL,
               method = "exhaustive")

summary_exhaustive <- summary(regsubsets.out)
print(summary_exhaustive)

## Plotting and choosing the subset
par(mfrow=c(2,2)) 
plot(summary_exhaustive$rss ,xlab="Number of Variables ",ylab="RSS", type="l") 
plot(summary_exhaustive$adjr2 ,xlab="Number of Variables ", ylab="Adjusted RSq",type="l")
coef(regsubsets.out, 5)

#Graphically find the best subsets according to adjusted r^2
## Adjusted R2
plot(regsubsets.out, scale = "adjr2", main = "Adjusted R^2")

lm.fit1=lm(OriginalInterestRate ~ CreditScore+MIP+OriginalUPB+OriginalLoanTerm+Channel
          ,data=train)
print(summary(lm.fit1))
pred1 = predict(lm.fit1, test)
accuracy(pred1,train$OriginalInterestRate)
a <- accuracy(pred1,train$OriginalInterestRate)
rmse_forward <- a[2]
MSE.lm <- sum((test$OriginalInterestRate-pred1)^2)/nrow(test)
print(MSE.lm)


#forward selection
regfit.fwd=regsubsets(OriginalInterestRate ~.,data=train,nvmax=6, method="forward") 
F=summary(regfit.fwd)
F
## Plotting and choosing the subset
par(mfrow=c(2,2)) 
plot(F$rss ,xlab="Number of Variables ",ylab="RSS", type="l") 
plot(F$adjr2 ,xlab="Number of Variables ", ylab="Adjusted RSq",type="l")
coef(regfit.fwd, 5)
#best variables
plot(regfit.fwd, scale = "adjr2", main = "Adjusted R^2")

#forward selection
#running with best 5 variables with highest adjusted r^2 values (top black box)
lm.fit2=lm(OriginalInterestRate ~ CreditScore+OriginalUPB+OriginalLoanTerm+Channel+MIP
          ,data=train)
summary(lm.fit2)
pred2 = predict(lm.fit2, test)
accuracy(pred2,train$OriginalInterestRate)
b <- accuracy(pred2,train$OriginalInterestRate)
rmse_forward <- b[2]
MSE.forward <- sum((test$OriginalInterestRate-pred2)^2)/nrow(test)
print(MSE.lm)


#### Backward selection
regfit.bwd=regsubsets(OriginalInterestRate ~.,data=train,nvmax=6 , method="backward") 
B=summary(regfit.bwd)
B
## Plotting and choosing the subset
par(mfrow=c(2,2)) 
plot(B$rss ,xlab="Number of Variables ",ylab="RSS", type="l") 
plot(B$adjr2 ,xlab="Number of Variables ", ylab="Adjusted RSq",type="l")
coef(regfit.bwd, 6)
#best variables
plot(regfit.bwd, scale = "adjr2", main = "Adjusted R^2")

#running with backward 
#running with best 6 variables with highest adjusted r^2 values (top black box)
lm.fit3=lm(OriginalInterestRate ~ CreditScore+OriginalUPB+OriginalLoanTerm+Channel+MIP+OccupancyStatus,data=train)   
summary(lm.fit3)
pred3 = predict(lm.fit3, test)
accuracy(pred3,train$OriginalInterestRate)
c <- accuracy(pred3,train$OriginalInterestRate)
rmse_backward <- c[2]

#BEST RESULT WITH 5 VARIABLES - FORWARD SEARCH :CreditScore+OriginalUPB+OriginalLoanTerm+Channel+MIP
plot(test$OriginalInterestRate,pred2,col='red',main='Real vs predicted NN',pch=18,cex=0.7)
abline(0,1,lwd=2)
legend('bottomright',legend='NN',pch=18,col='red', bty='n')

train

#Aritificial Neural Network Algorithm
train_ann = train[,c(1,3,9,10,11,14)]
test_ann = test[,c(1,3,9,10,11,14)]
n <- names(train_ann)
f <- as.formula(paste("OriginalInterestRate ~", paste(n[!n %in% "OriginalInterestRate"], collapse = " + ")))
f

nn <- neuralnet(formula = f,data=train_ann,hidden=c(3,2),linear.output=TRUE)
#nn$result.matrix
predict_ann <- compute(nn,test_ann[-2])
plot(nn,rep="best")
MSE.nn <- sum((test_ann$OriginalInterestRate - predict_ann$net.result)^2)/nrow(test_ann)

#table(test_ann$OriginalInterestRate,predict_ann$net.result)
#print(head(predict_ann$net.result))

# #plotting
# plot(test_ann$OriginalInterestRate,predict_ann$net.result,col='red',main='Real vs predicted NN',pch=18,cex=0.7)
# abline(0,1,lwd=2)
# legend('bottomright',legend='NN',pch=18,col='red', bty='n')
# #Comparison
# plot(test_ann$OriginalInterestRate,predict_ann$net.result,col='red',main='Real vs predicted NN',pch=18,cex=0.7)
# points(test_ann$OriginalInterestRate,pred2,col='blue',pch=18,cex=0.7)
# abline(0,1,lwd=2)
# legend('bottomright',legend=c('NN','LM'),pch=18,col=c('red','blue'))

#KNN Algorithm 
#selecting 100000 rows randomly from train and test files for train and test
train_knn <- sqldf('select * from train order by random() limit 100000')
test_knn <- sqldf('select * from test order by random() limit 100000')

#KNN Algorithm 
train_knn$OriginalInterestRate <- floor(train_knn$OriginalInterestRate)
test_knn$OriginalInterestRate <- floor(test_knn$OriginalInterestRate)


normalize <- function(x) {
  return ((x - min(x)) / (max(x) - min(x)))
}


ntrain_knn <- as.data.frame(lapply(train_knn[,c("CreditScore", "OriginalUPB", "Channel","OriginalLoanTerm")], normalize))
ntest_knn <- as.data.frame(lapply(test_knn[,c("CreditScore", "OriginalUPB", "Channel","OriginalLoanTerm")], normalize))


train_knn_target <- floor(train_knn[,9])
test_knn_target <- floor(test_knn[,9])

table(train_knn_target)
table(test_knn_target)


#KNN Algorithm model and output
m1 <- knn(train = ntrain_knn, test = ntest_knn, cl = train_knn_target, k = 3)

(table(test_knn_target, m1))
sum(diag(t))/sum(t)
#KNN Algorithm ends

names(train)

#Random Forest Algorithm 
#selecting 100000 rows randomly from train and test files for train and test
train_for <- sqldf('select * from train order by random() limit 100000')
test_for <- sqldf('select * from test order by random() limit 100000')

train_for <- train_for[,c(1,3,9,10,11,14)]
test_for <- test_for[,c(1,3,9,10,11,14)]

train_for$OriginalInterestRate <- floor(train_for$OriginalInterestRate)
test_for$OriginalInterestRate <- floor(test_for$OriginalInterestRate)

cols <- c("Channel", "OriginalInterestRate")

for(i in cols){
  train_for[,i] = as.factor(train_for[,i])
}

for(i in cols){
  test_for[,i] = as.factor(test_for[,i])
}


str(train_for)
str(test_for)

model_random <- randomForest(OriginalInterestRate ~ ., data = train_for, ntree = 20)

model_random

importance(model_random)
varImpPlot(model_random)

predictionwithclass <- predict(model_random, test_for, type = 'class')
t <- table(predictions=predictionwithclass, actual=test_for$OriginalInterestRate)
t
sum(diag(t))/sum(t)



MSE.nn
MSE.forward
