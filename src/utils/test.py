import pandas as pd
import json
import requests
import statsmodels.api as sm
from pathlib import Path
from utils.config import getConfigs


#setting root directory for relative file paths
root_dir = Path(__file__).resolve().parent.parent.parent

configs= getConfigs()
riskFree = configs["riskFree"]

#For testing. Acts as my API call.
AAPL = root_dir/"src"/"assets"/"data"/"AAPL.json"
IBM = root_dir/"src"/"assets"/"data"/"IBM.json"
SPY = root_dir/"src"/"assets"/"data"/"SPY.json"
files=[AAPL,IBM]#,SPY
def testFunc(ticker):
    for file in files:
        with open(file) as f:
            d = json.load(f)
            if d["Meta Data"]["2. Symbol"] == ticker:
                return(d)

#Actual API call
def getDat(ticker):
    api= configs["API_Key"]
    if configs["paid"] == True:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={api}"
    else:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={ticker}&apikey={api}"
    r = requests.get(url)
    data = r.json()
    return(data)



class Security:
    def __init__(self,name,debug=False):
        self.name = name
        self.debug=debug
        self.getPrices()
        self.getReturns()
        self.getTerminalWealth()
        self.getStats()


    def getPrices(self):
        name=self.name
        #Do api call to get data
        cp=[]
        if self.debug == True:
            data=testFunc(name)
            data = data["Monthly Time Series"]
            for date, dat in data.items():
                cp.append((date, dat['4. close']))
        else:
            data=getDat(name)
            if configs["paid"] == True:
                data = data["Monthly Adjusted Time Series"]
                for date, dat in data.items():
                    cp.append((date, dat['5. adjusted close']))
            else:
                data = data["Monthly Time Series"]
            for date, dat in data.items():
                cp.append((date, dat['4. close']))
        self.securityDF = pd.DataFrame(cp, columns = ["Date","Close_Price"])
        #converting string to time series so that we can merge with s&p
        self.securityDF["Close_Price"]=self.securityDF["Close_Price"].astype(float)
        self.securityDF ["Date"]=((self.securityDF["Date"].str[5:7]).apply(str)+"/"+"01"+"/"+(self.securityDF ["Date"].str[:4]).apply(str))
        self.securityDF ["Date"]=pd.to_datetime(self.securityDF ["Date"])
        self.securityDF.set_index("Date")
        self.securityDF.sort_values(by='Date', inplace=True)
        return(self.securityDF)

    def getReturns(self):
        colName = "Returns"
        self.securityDF[colName]=self.securityDF["Close_Price"].pct_change()
        #have to set this to 0 otherwise calcs will return nan values
        self.securityDF.loc[self.securityDF.index[0],"Returns"]=0
        return(self.securityDF)


    def getTerminalWealth(self):
        tw = 1
        colName ="T_Wealth"
        #done to prevent an incompatability between float and int
        self.securityDF[colName]=float(0)
        self.securityDF["multiplier"] = self.securityDF["Returns"]+1
        for index, row in self.securityDF.iterrows():
            tw = (tw*row['multiplier'])
            self.securityDF.loc[index,colName] = tw
        self.securityDF.drop(labels='multiplier', axis=1, inplace=True)
        return(self.securityDF)

    def getRiskComp(self, riskFree=riskFree, riskAversion=1):
        Y=(self.mean-riskFree)/(riskAversion*self.var)
        return(Y)

    def getStats(self):
        self.mean=self.securityDF["Returns"].mean()
        self.mean=self.mean*12
        self.stdev=self.securityDF["Returns"].std()
        self.stdev=self.stdev*3.4641  #sqrt of 12
        self.var = self.stdev**2
        self.sharp=self.mean/self.stdev
        self.Y=self.getRiskComp()
        statDict={"Mean":self.mean,"Stdev":self.stdev,"Var":self.var,"Sharp":self.sharp,"Y*":self.Y}
        self.statDF=pd.DataFrame.from_dict(statDict,orient='index')
        self.statDF.rename({0:self.name},axis=1,inplace=True)
        return(self.mean,self.stdev,self.var,self.sharp,self.Y,self.statDF)



class Portfolio(Security):
    def __init__(self, name, securities):
        self.name = name
        self.securities=securities
        self.initWeights()
        self.getPrices()
        self.getReturns()
        self.getTerminalWealth()
        self.getStats()
        self.mergeStats()
        self.getDashStats()

    def initWeights(self):
        sWeight = 1/(len(self.securities))
        self.wDict={}
        for security in self.securities:
            self.wDict[security.name]=sWeight
        self.secWeights=list(self.wDict.values())
        return(self.secWeights,self.wDict)

    def updateWeights(self, newWeights):
        #We are expecting a dictionary that may contain strings where we want an integer. first we convert.
        for security in newWeights:
            newWeights[security]=float(newWeights[security])
            #next we update each securities weight
            self.wDict[security]=newWeights[security]
        self.secWeights=list(self.wDict.values())
        self.getPrices()
        self.getReturns()
        self.getTerminalWealth()
        self.getStats()
        self.mergeStats()
        self.getDashStats()
        return(self.secWeights,self.wDict)

    def getPrices(self):
        secNames=[n.name for n in self.securities]+["Portfolio"]
        prices=[]
        #Initializing a dataframe by copyting the closing price and date of the first security in the portfolio
        self.securityDF =self.securities[0].securityDF.loc[:,["Date","Close_Price"]]
        #Add the rest of the closing prices into the existing data frame.
        colNames=["Date",self.securities[0].name]
        for security in self.securities[1:]:
            colNames.append(security.name)
            self.securityDF  = self.securityDF .merge(security.securityDF.loc[:,["Date","Close_Price"]], on='Date')
            self.securityDF.columns=colNames
        self.securityDF.set_index("Date",inplace=True)

        #taking the sum of the prices multiplied by their weights to get the average price of the portoflio for that month.
        for r in self.securityDF .iterrows():
            prices.append(sum(r[1]*self.secWeights))
        #Create a new column and append all the portfolio prices previously calculated
        self.securityDF["Portfolio"]=prices
        #copy this dataframe and rename it so that we have all the prices of all securities and portoflio in 1 frame
        self.priceFrame=self.securityDF.copy()
        newnames=dict(zip([n for n in self.priceFrame],secNames))
        self.priceFrame.rename(newnames,axis=1,inplace=True)
        #select the subset of only the closing price of the portfolio.
        self.securityDF=self.securityDF[["Portfolio"]].copy()
        return(self.securityDF, self.priceFrame)

    def getReturns(self):
        #For each column in the priceDF, compute the .pct change
        self.returnFrame=self.priceFrame.pct_change()
        self.returnFrame.iloc[:1,:]=0
        self.securityDF["Returns"]=self.returnFrame["Portfolio"]
        return(self.securityDF, self.returnFrame)


    def getTerminalWealth(self):
        #counter to help with indexing
        c=0
        self.wealthFrame=pd.DataFrame(columns=self.returnFrame.columns,index=self.returnFrame.index)
        self.wealthFrame.iloc[0,:]=1
        for index, sRow in self.returnFrame.iterrows():
            if sRow["Portfolio"]!=0:
                x=sRow.add(1)
                y=x.mul(self.wealthFrame.iloc[c])
                self.wealthFrame.loc[index]=y
                c+=1
        self.securityDF["T_Wealth"]=self.wealthFrame["Portfolio"]
        return(self.wealthFrame,self.securityDF)


    def mergeStats(self):
        secNames=["Portfolio"]+[s.name for s in self.securities]
        for security in self.securities:
            self.statDF=self.statDF.join(security.statDF,rsuffix=security.name)
        self.statDF=self.statDF.set_axis(secNames,axis=1)
        return(self.statDF)


    #needed to display the statistics in the dash table
    def getDashStats(self):
        self.dashStatDF=self.statDF
        self.dashStatDF.insert(0,"Statistic",self.statDF.index)
        self.dashStatDF=self.dashStatDF.to_dict("records")

        return(self.dashStatDF)

    def updateRiskComp(self, rf=riskFree, ra=1):
        for security in self.securities:
            sY=security.getRiskComp(riskFree=rf,riskAversion=ra)
            self.statDF.loc["Y*",security.name]=sY
            self.dashStatDF[4][security.name]=sY
        pY=portfolio.getRiskComp(riskFree=rf,riskAversion=ra)
        self.statDF.loc["Y*","Portfolio"]=pY
        self.dashStatDF[4]["Portfolio"]=pY
        return(self.statDF,self.dashStatDF)


#This class is used to retreive regression data for security and prtfolio performance.
class Comparisons():
    def __init__(self, portfolio, ffloc=root_dir/"src"/"assets"/"data"/"ff.csv"):
        self.portfolio=portfolio
        self.ffloc=ffloc
        self.getFFData()
        self.getRiskPremiums()

        #Real results we are looking for. Below calls return the different dictionaries of results.
        factorLst= ["Mkt-RF","SMB","HML","RMW","CMA"]
        #CAPM has to be put in brackets because that funtion is expecting a list.
        self.CAPM = self.regress([factorLst[0]])
        self.ff3 = self.regress(factorLst[:3])
        self.ff5 = self.regress(factorLst)

    def getFFData(self):
        self.ffDF=pd.read_csv(self.ffloc)
        #setting dates to index so that we can filter the ff data by our return period dates.
        self.ffDF["date"]=pd.to_datetime(self.ffDF["date"])
        self.ffDF.set_index('date',inplace=True)
        return(self.ffDF)

    #should rename to rpFrame
    def getRiskPremiums(self):
        self.rfFrame=self.portfolio.returnFrame.copy()
        # self.rfFrame.set_index('Date',inplace=True)
        #first step is getting the risk free rate
        self.ffDF=self.ffDF.filter(items=self.rfFrame.index.values,axis=0)
        #subtracts the risk free rate from every item in our return df.
        for index, row in self.ffDF.iterrows():
            rf=self.ffDF.loc[index,"RF"]
            self.rfFrame.loc[index]=self.rfFrame.loc[index]-rf
        return(self.rfFrame)

    ###Get alphas and betas from these results)###
    def regress(self,factors):
        self.regFrame=self.rfFrame.join(self.ffDF.loc[:,factors],how='inner')
        #since beta and alphas are just returns from a regression. We'll just run a regression.
        #initialize an empty dict to hold parameters
        regResultDict={}
        #Create regression models for each security so that we can get beta and alpha.
        for security in self.rfFrame:
            model = sm.OLS(self.regFrame.loc[:,security], sm.add_constant(self.regFrame.loc[:,factors]))
            regResults=model.fit()
            #Look at the results, get the stats and append them to a dictionary.
            regResultDict[security]={
                "Alpha":regResults.params["const"],
                "Alpha T-Score": regResults.tvalues["const"]}
            for factor in factors:
                regResultDict[security][f"{factor}_Beta"]=regResults.params[factor]
                regResultDict[security][f"{factor}_T_Value"]=regResults.tvalues[factor]

        # for security in regResultDict:
            # dashRegress.append()
        regResultDF=pd.DataFrame(regResultDict)
        regResultDF.insert(0,"Statistic",regResultDF.index)
        return(regResultDF)

tickers =["AAPL","IBM"]

secDict={ticker: Security(ticker,debug=True) for ticker in tickers}
portfolio=Portfolio("portfolio",list(secDict.values()))
# print(portfolio.dashStatDF)
portfolio.updateRiskComp(ra=.5)
# print(portfolio.dashStatDF)
# data = dict([ticker for ticker in portfolio.wDict.items()])
comp=Comparisons(portfolio)

