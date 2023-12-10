from pathlib import Path
from analysis import Security,Portfolio,Comparisons
import statsmodels.api as sm
from scipy import optimize
#https://www.kaggle.com/code/vijipai/lesson-6-sharpe-ratio-based-portfolio-optimization#Sharpe-Ratio-based-Portfolio-Optimization

#setting root directory for relative file paths
root_dir = Path(__file__).resolve().parent.parent

tickers =["IBM","AAPL"]

secDict={ticker: Security(ticker,debug=True) for ticker in tickers}
portfolio=Portfolio("portfolio",list(secDict.values()))



newWeights=[.4,.6]
newWeightDict=dict(zip(tickers,newWeights))

   

for ticker,weight in newWeightDict.items():
    portfolio.updateWeights({ticker:weight})

portfolio.mean-.02
    
rf= portfolio.returnFrame
rf.set_index("Date",inplace=True)

covm=rf.iloc[:,1:].cov()
#annualizing the numbers
covm=covm*12

covm.columns=[sn.name for sn in portfolio.securities]
covm.index=[sn.name for sn in portfolio.securities]

rMul=portfolio.secWeights
cMul=rMul
#multiply by 1 weight
covm=(covm*rMul)
#multiply by second weight
covm=(covm.mul(cMul,axis="columns"))
covm["totals"]=covm.sum(axis=1)
pvar=covm["totals"].sum()
pstd=pvar**(1/2)



#Remember, this is a nonlinear optimization problem
#Objective: Maximize Sharp
#Constraint: sum of new weights must equal 1
#Constraint: all items in newWeights > 1
#Maximize((w1*r1+w2*r2)-rf)/sqrt(w1**2*v1+w2**2*v2+2*w1*w2*cov(s1,s2))
#maximize(portfolio.mean/pstd)

#weights are the only thing that is going to change for each computation.
#get list or dict of all covariances, multiply each by the weights and 2.
#get list of all variances, multiple each by weights.
#get list of all returns, multiply each by weights