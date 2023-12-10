def getConfigs():
    debug = False #This controls what data the analysis file references. Either saved testing data if True, or the alpha vantage API if false. #NOT IMPLEMENTED CURRENTLY
    riskFree = .02 #Controls the risk free rate.
    API_Key = "H6BUNV2BLIBH4589" #PLACE YOUR API KEY IN QUOTES HERE EX.  API_Key = "DEMOAPI69420"
    paid = True #This controls which AlphaVantage API call is used. ADJ monthly close price id True. Monthly close price if false.
    #Note, monthly close price will not include stock splits or dividends.
    return({"debug":debug, "riskFree":riskFree,"API_Key":API_Key,"paid":paid})
    