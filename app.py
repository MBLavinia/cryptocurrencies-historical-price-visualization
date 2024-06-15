import pandas as pd
from sqlalchemy import create_engine
from flask import Flask
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context, ALL
import dash_bootstrap_components as dbc
import plotly.express as px

# Database connection string
db_string = "postgresql://postgres:brkbeko.97@localhost:8050/postgres"
engine = create_engine(db_string)

# Flask server
server = Flask(__name__)

# Dash app
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout of the Dash app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date='2018-01-01',
                end_date='2020-12-31',
                display_format='YYYY-MM-DD',
            ),
        ], width=6),
    ], justify='center', style={'margin-top': '20px'}),
    
    dbc.Row([
        dbc.Col([
            html.Div(id='stats-output')
        ], width=12),
    ], justify='center', style={'margin-top': '20px'}),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='price-line-chart')
        ], width=12),
    ], justify='center', style={'margin-top': '20px'}),
    
    # Modal for displaying detailed data
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Detailed Data")),
            dbc.ModalBody(dash_table.DataTable(
                id='data-table',
                columns=[
                    {'name': 'Date', 'id': 'date'},
                    {'name': 'Pair', 'id': 'pair'},
                    {'name': 'Price', 'id': 'price'},
                    {'name': 'Open', 'id': 'open'},
                    {'name': 'High', 'id': 'high'},
                    {'name': 'Low', 'id': 'low'},
                    {'name': 'Volume', 'id': 'volume'},
                    {'name': 'Change %', 'id': 'change_percent'},
                ],
                sort_action="native",
                page_size=10,
            )),
            dbc.ModalFooter(
                dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
            ),
        ],
        id="modal",
        is_open=False,
        size="xl",
    ),
])

@app.callback(
    Output('stats-output', 'children'),
    Output('price-line-chart', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_output(start_date, end_date):
    # Query the data
    query = f"""
    SELECT date, pair, price, open, high, low, volume, change_percent 
    FROM crypto_data
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])  # Ensure date column is datetime

    if df.empty:
        return "No data available for the selected date range.", {}

    # Calculate the highest average difference between the daily opening and closing prices
    df['Difference'] = (df['open'] - df['price']).abs()
    avg_difference = df.groupby('pair')['Difference'].mean()
    max_avg_difference_pair = avg_difference.idxmax()
    max_avg_difference_value = avg_difference.max()

    # Find the lowest and highest prices for each pair
    lowest_prices = df.groupby('pair')['low'].min()
    highest_prices = df.groupby('pair')['high'].max()

    # Create the statistics output with clickable cards
    stats_output = []
    for pair in avg_difference.index:
        stats_output.append(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(pair, className="card-title"),
                            html.P(f"Avg. Difference: {avg_difference[pair]:.2f}%"),
                            html.P(f"Lowest Price: {lowest_prices[pair]:.2f}"),
                            html.P(f"Highest Price: {highest_prices[pair]:.2f}")
                        ]
                    ),
                    dbc.Button("View Details", id={"type": "clickable-card", "index": pair}, color="primary")
                ],
                className="clickable-card"
            )
        )

    # Create the price line charts
    fig = px.line(df, x='date', y='price', color='pair', title='Price Line Chart for each Pair')
    
    return stats_output, fig

@app.callback(
    Output("modal", "is_open"),
    Output("data-table", "data"),
    Input({"type": "clickable-card", "index": ALL}, "n_clicks"),
    Input("close", "n_clicks"),
    State("modal", "is_open"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
)
def display_data_in_modal(card_clicks, close_click, is_open, start_date, end_date):
    ctx = callback_context
    if not ctx.triggered:
        return False, []
    
    if ctx.triggered[0]['prop_id'] == 'close.n_clicks':
        return not is_open, []

    # Determine which card was clicked
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    card_id = eval(triggered_id)  # Convert string to dictionary
    pair = card_id['index']

    # Query the data for the selected pair
    query = f"""
    SELECT date, pair, price, open, high, low, volume, change_percent 
    FROM crypto_data
    WHERE date BETWEEN '{start_date}' AND '{end_date}' AND pair = '{pair}'
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])  # Ensure date column is datetime

    data = df.to_dict('records')

    return True, data

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)
