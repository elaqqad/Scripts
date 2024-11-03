import dash
import dash_bootstrap_components as dbc
from dash import html

app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                use_pages=True)

app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Summary", href="/summary")),
            dbc.NavItem(dbc.NavLink("Comparison", href="/comparison")),
        ],
        brand="DataFrame Analysis",
        brand_href="/",
        color="primary",
        dark=True,
    ),
    dash.page_container
])

if __name__ == '__main__':
    app.run_server(debug=True)