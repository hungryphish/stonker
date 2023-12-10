from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, ctx
import plotly.express as px
import pandas as pd
from pathlib import Path
# from utils.analysis import portfolio,comp,Portfolio,Comparisons,Security
from utils.test import portfolio,comp,Portfolio,Comparisons,Security



#setting root directory for relative file paths
root_dir = Path(__file__).resolve().parent.parent


# Initialize the app
app = Dash(__name__)


app.layout = html.Div([
    html.Div([
        html.H1("Stonker")
    ],id='siteName'),

    #input Div, tickers, risk aversion, weights.
    html.Div([
        #STOCKS
        html.Div([
            #stock Input label
            html.Label('Enter stock tickers seperated by a comma.'),
            #stock name input
            dcc.Input(value='AAPL,IBM', type='text',id='tickers'),
            #submit button
            html.Button('Submit', type='submit', id='stock_submit')
        ],id="stockDiv"),
        #RISK AVERSION
        html.Div([
            #Risk Aversion label
            html.Label('Enter risk aversion level.'),
            #Risk Aversion input
            dcc.Input(value='1', type='text', id='userRA'),
            #RA Submit button
            html.Button('Submit', type='submit', id='raSubmit')
        ],id="riskDiv")
    ],id='inputDiv'),

    #WEIGHTS
    html.Div([
        #Table Label
        html.H2('Portfolio Composition'),
        #Table
        dash_table.DataTable(
            id='weightTable',
            #Has to be in a list because of Dash.
            columns = (
                [{'id': c.name,'name': c.name} for c in portfolio.securities]
            ),
            data = [portfolio.wDict],
            page_size=2,
            style_header={
                'backgroundColor': 'rgb(30, 30, 30)',
                'color': 'white'
                },
            style_data={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white'
                },
            editable = True,
            ),
    ],id='weightDiv'),

    #STATISTICS
    html.Div([
        #Table Label
        html.H2('Stat Table'),
        #Table
        dash_table.DataTable(
                            data=portfolio.dashStatDF,
                            page_size=5,
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'color': 'white'
                            },
                            style_data={
                                'backgroundColor': 'rgb(50, 50, 50)',
                              'color': 'white'
                            },
                            style_cell_conditional=[
                                {'if':{'column_id':'Statistic'},
                                'textAlign':'left'}
                            ],
                            id='statTable',
                            ),

        #save to csv Button
        html.Button('Download Spreadhseet', id="xlsx-button"),
        dcc.Download(id="download-data-xlsx"),
        ],id='statDiv'),

    #Graphs Div, terminal wealth and $ value
    html.Div([
        #terminal wealth
        html.Div([
            html.H2('Terminal Wealth'),
            dcc.Graph(
                figure=px.line(
                    portfolio.wealthFrame,
                    x=portfolio.wealthFrame.index,
                    y=portfolio.wealthFrame.columns
                    ),
                id='twGraph'
                )
        ],id='twDiv'),

        #$ Value
        html.Div([
            html.H2('Price over time'),
            dcc.Graph(
                figure=px.line(
                    portfolio.priceFrame,
                    x=portfolio.priceFrame.index,
                    y=portfolio.priceFrame.columns
                    ),
                id='priceGraph'
                )
        ],id='valDiv')
    ],id='graphDiv'),

    #CAPM
    html.Div([
        html.H2('CAPM Results'),
        dash_table.DataTable(
            data=comp.CAPM.to_dict("records"),
            page_size=5,
            style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
            },
            style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
             'color': 'white'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(75, 75, 75)',
                }
            ],
            style_cell_conditional=[
                {'if':{'column_id':'Statistic'},
                 'textAlign':'left'}
            ],
            id='CAPMTable',
        ),
        ],id='CAPMDiv'),

    #FF 3 factor
    html.Div([
        html.H2('Fama French 3 Factor Results'),
        dash_table.DataTable(
            data=comp.ff3.to_dict("records"),
            page_size=8,
            style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
            },
            style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(75, 75, 75)',
                }
            ],
            style_cell_conditional=[
                {'if':{'column_id':'Statistic'},
                 'textAlign':'left'}
            ],
            id='ff3Table',
        ),
        ],id='ff3Div'),
    #FF 5 factor
    html.Div([
        html.H2('Fama French 5 Factor Results'),
        dash_table.DataTable(
            data=comp.ff5.to_dict("records"),
            page_size=12,
            style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
            },
            style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
             'color': 'white'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(75, 75, 75)',
                }
            ],
            style_cell_conditional=[
                {'if':{'column_id':'Statistic'},
                 'textAlign':'left'}
            ],
            id='ff5Table',
        ),
        ],id='ff5Div')

],id='mainDiv')

# #Since its difficult to share objects between callbacks. We are just going to have the server recompute everything.
# #This is taxing and there is probably a better way, but I need to push this through.
# #By getting what tickers are in the ticker box, we can recompute stats for the portfolio. This will be shared across callbacks.
def get_portfolio(tickers, ra="1"):
        #splitting user input which is given as one string into a list of string which can be used by the Security class.
        tickers = tickers.split(",")

        #Using the list of strings, generate a list of dictionaries containing the returns for all tickers.
        #####--------~~~~~~~~~ CHANGE DEBUG TO FALSE FOR DEPLOYMENT ~~~~~~~~~~---------##################
        secDict={ticker: Security(ticker,debug=False) for ticker in tickers}

        #using the return dictionaries, create a portfolio , get statistics, and all of the graphs.
        portfolio=Portfolio("portfolio",list(secDict.values()))
        portfolio.updateRiskComp(ra=float(ra))
        comp=Comparisons(portfolio)
        return(portfolio,comp)


# #Since my interactivity will end with updating tables and graphs, this function can be used as the return for call backs.
def update_figures(portfolio,comp):

        #convert stats DF to something useable by Dash.
        sFrame=portfolio.dashStatDF

        price=px.line(
            portfolio.priceFrame,
            x=portfolio.priceFrame.index,
            y=portfolio.priceFrame.columns
            )

        #convert terminal wealth to something useable by dash
        twealth=px.line(
            portfolio.wealthFrame,
            x=portfolio.wealthFrame.index,
            y=portfolio.wealthFrame.columns
            )
        wCols = [{'id': c.name,'name': c.name} for c in portfolio.securities]
        wDat = [portfolio.wDict]
        capm=comp.CAPM.to_dict("records")
        ff3=comp.ff3.to_dict("records")
        ff5=comp.ff5.to_dict("records")
        return(wCols,wDat, sFrame, twealth, price, capm,ff3,ff5)

#### Following is the callback occuring after a user changes the user input values  #####
#### USER INPUT CALLBACK ####
@app.callback(
    Output('weightTable','columns'),# allow_duplicate=True),
    Output('weightTable','data'),# allow_duplicate=True),
    Output('statTable', 'data'),#,allow_duplicate=True),
    Output('twGraph', 'figure'),# allow_duplicate=True),
    Output('priceGraph','figure'),# allow_duplicate=True),
    Output('CAPMTable', 'data'),# allow_duplicate=True),
    Output('ff3Table', 'data'),# allow_duplicate=True),
    Output('ff5Table','data'),# allow_duplicate=True),
    Input('stock_submit', 'n_clicks'),
    Input('raSubmit', 'n_clicks'),
    Input('weightTable','data'),
    Input('weightTable','columns'),
    State('tickers', 'value'),
    State('userRA', 'value'),
    prevent_initial_call=True
    )

def update_page(b1,b2,wd,wc,tickers,ra):
    triggered_id = ctx.triggered_id
    #TICKERS
    if triggered_id == 'stock_submit':
        return ticker_update(tickers,ra)
    #RISK AVERSION
    elif triggered_id == "raSubmit":
        return Y_update(tickers,ra)
    #WEIGHTS
    elif triggered_id=='weightTable':
        return(weight_update(wd,wc,tickers,ra))
#TICKERS
def ticker_update(tickers = "AAPL,IBM", ra="1"):
    portfolio=get_portfolio(tickers, ra)
    #since the portfolio function is returning the portfolio class and fama french data, we have to seperate them.
    comp=portfolio[1]
    portfolio=portfolio[0]
    return(update_figures(portfolio,comp))
#RISK AVERSION
def Y_update(tickers="AAPL,IBM",ra= "1"):
    #Including weights so that they dont get wiped when you change risk aversion
    portfolio=get_portfolio(tickers,ra)
    comp=portfolio[1]
    portfolio=portfolio[0]
    return(update_figures(portfolio,comp))
#WEIGHTS
#columns goes unused but must be included as each change to the cell returns both rows and columns.
def weight_update(rows,columns,tickers,ra):
    #Lets get the value of the new weights.
    portfolio=get_portfolio(tickers, ra)
    comp=portfolio[1]
    portfolio=portfolio[0]
    newWeights=rows[0]
    #Use the new values to get new data frames and graphs.
    #pass the value into the update weight function of the portfolio class.
    portfolio.updateWeights(newWeights)
    return(update_figures(portfolio,comp))

#Callback to download a spreadsheet of all the data.
@callback(
    Output("download-data-xlsx","data"),
    Input("xlsx-button","n_clicks"),
    Input('weightTable','data'),
    Input('weightTable','columns'),
    State('tickers', 'value'),
    State('userRA', 'value'),
    prevent_initial_call=True,
)

#All this is necessary so that we get all the user data.
#dfoing yet another call. Can probably streamline this somehow.
def xlsxExport(n_clicks,rows,columns,tickers,ra):
    #this silly bit of logic is necessary so that a spreadsheet isnt created everytime the page loads.
    #This should be taken care of by prevent_initial_call = True, but here we are.
    # if n_clicks == None:
    #     n_clicks = 0
    # old=0
    # new=1
    # old += n_clicks
    # if old == new:
    if n_clicks is not None:
        print(n_clicks)
        portfolio=get_portfolio(tickers, ra)
        comp=portfolio[1]
        portfolio=portfolio[0]
        newWeights=rows[0]
        portfolio.updateWeights(newWeights)

        #Putting all the data frames in a dictionary so that we can iterate through easily
        data={"returns":portfolio.returnFrame,
            "prices":portfolio.priceFrame,
            "wealth":portfolio.wealthFrame,
            #Dropping redundant indexes since they are only needed for the dash table output.
            "stats":portfolio.statDF.iloc[:,1:],
            "capm":comp.CAPM.iloc[:,1:],
            "ff3":comp.ff3.iloc[:,1:],
            "ff5":comp.ff5.iloc[:,1:]
        }

        #Putting all the data frames into a spreadsheet. Each data frame gets its own sheet.
        writer = pd.ExcelWriter('portfolio_data.xlsx', engine='xlsxwriter')
        for df in data:
            data[df].to_excel(writer,sheet_name=df)
        writer.close()
        return(dcc.send_file('portfolio_data.xlsx'))
    else:
        pass

if __name__ == '__main__':
    app.run(debug=True)