# Machine Learning

## Supervised vs unsupervised vs reinforcement learning
Supervised learning trains on labelled data to predict labels (classification and regression). Unsupervised learning finds structure in unlabelled data (clustering, dimensionality reduction, association rules). Reinforcement learning has an agent learn by interacting with an environment and receiving rewards or penalties.

## Overfitting and underfitting
Overfitting means the model learns the training data, including its noise, so it scores well on training data but poorly on unseen data (high variance). Underfitting means the model is too simple to capture the pattern, so it does poorly on both (high bias). Fix overfitting with more data, a simpler model, regularization, dropout, early stopping, feature selection or cross-validation.

## Bias-variance tradeoff
Bias is error from overly simple assumptions; variance is error from sensitivity to the particular training set. Making a model more complex lowers bias but raises variance, so the goal is a balance that minimises error on unseen data.

## Regularization: L1 vs L2
Regularization adds a penalty on large coefficients to the loss to reduce overfitting. L1 (Lasso) penalises the absolute values of coefficients and can shrink some to exactly zero, which performs feature selection. L2 (Ridge) penalises squared coefficients and shrinks them smoothly without making them zero. Elastic Net combines both.

## Train, validation and test sets and cross-validation
The training set fits the model, the validation set tunes hyperparameters, and the test set gives a final unbiased estimate that is used only once. In k-fold cross-validation the data is split into k folds and the model is trained k times, each time holding out a different fold for validation, and the scores are averaged.

## Classification metrics
Precision = TP / (TP + FP): of the items predicted positive, how many really are. Recall = TP / (TP + FN): of the real positives, how many were found. F1 is the harmonic mean of precision and recall. Accuracy = correct predictions / all predictions. The confusion matrix lists TP, FP, TN and FN. ROC-AUC measures how well the model ranks positives above negatives across thresholds.

## When accuracy is misleading
On imbalanced data a model that always predicts the majority class can have very high accuracy but be useless; for example, if 99 percent of transactions are legitimate, predicting "legitimate" always gives 99 percent accuracy. Use precision, recall, F1 or AUC, and handle imbalance with resampling (such as SMOTE), class weights or threshold tuning.

## Regression metrics
MAE is the mean absolute error, MSE the mean squared error (penalises large errors more), RMSE is the square root of MSE in the target's units, and R-squared is the proportion of variance explained by the model.

## Gradient descent
Gradient descent minimises a loss function by repeatedly moving the parameters a small step in the direction opposite to the gradient. The learning rate sets the step size: too large and training can diverge, too small and it is very slow. Variants: batch (all data per step), stochastic (one sample per step) and mini-batch (a small batch per step).

## Decision tree, random forest and boosting
A decision tree splits data on feature thresholds chosen to maximise information gain or reduce Gini impurity; it is easy to interpret but prone to overfitting. A random forest is an ensemble of many trees trained on bootstrap samples with random feature subsets (bagging) whose votes are combined, which reduces variance. Boosting (Gradient Boosting, XGBoost, AdaBoost) builds trees sequentially, each correcting the errors of the previous ones, which mainly reduces bias.

## Bagging vs boosting
Bagging trains models independently in parallel on resampled data and averages them to cut variance. Boosting trains models one after another, giving more weight to examples earlier models got wrong, to cut bias.

## K-means clustering
K-means partitions data into k clusters by repeatedly assigning each point to the nearest centroid and recomputing centroids until they stop moving, minimising within-cluster variance. You must choose k beforehand (elbow method, silhouette score), results depend on initialisation, and features should be scaled.

## K-nearest neighbours
KNN classifies a point by the majority label (or average value) of its k closest training points. It is a lazy learner: no training, but prediction is slow on large data, and it needs scaled features because it relies on distance.

## Linear and logistic regression
Linear regression models a continuous target as a weighted sum of features, assuming a linear relationship, independent errors, constant error variance (homoscedasticity), roughly normal residuals and little multicollinearity. Logistic regression is a classification model: it applies the sigmoid function to a linear combination of features to output a probability between 0 and 1.

## Support vector machine
An SVM finds the hyperplane that separates classes with the maximum margin; the points closest to it are the support vectors. The kernel trick lets it handle non-linear boundaries by implicitly mapping data to a higher dimension.

## Principal component analysis (PCA)
PCA reduces dimensionality by projecting data onto new orthogonal axes (principal components) that capture the largest variance, so you keep fewer features while retaining most of the information. Features should be scaled first.

## Feature scaling: normalization vs standardization
Normalization (min-max scaling) rescales values to a fixed range such as 0 to 1. Standardization (z-score) rescales to mean 0 and standard deviation 1. Scaling matters for distance-based and gradient-based models (KNN, SVM, K-means, neural networks, regularised regression) but not for tree-based models.

## Handling missing values
Options: drop rows or columns with too many missing values, impute with the mean, median or mode (median is robust to outliers), use model-based imputation such as KNN imputation, or add an indicator column that flags missingness. Choose based on why the data is missing.

## Data leakage
Data leakage is when information from outside the training set (the test set or the future) influences the model, giving unrealistically good results. Avoid it by splitting the data first and fitting scalers, encoders and imputers only on the training data.

## Hyperparameter vs parameter
Parameters (such as regression weights) are learned from data during training. Hyperparameters (such as learning rate, tree depth, k in KNN) are set before training and tuned with grid search, random search or Bayesian optimisation using validation data.
