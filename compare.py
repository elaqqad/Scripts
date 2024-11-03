import dash
from dash import html, dcc, dash_table, page_container
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

def identify_categories(df, threshold=20):
    """Identify categorical columns based on unique value count"""
    categories = []
    for col in df.columns:
        if col not in ['Currency', 'Error'] and df[col].nunique() < threshold:
            categories.append(col)
    return categories

def get_numeric_columns(df):
    """Get numerical columns excluding Currency and Error"""
    return [col for col in df.select_dtypes(include=[np.number]).columns 
            if col not in ['Currency', 'Error']]

def generate_summary(df):
    """
    Generate summary for each category in the dataframe.
    Returns a dictionary mapping category names to summary dataframes,
    plus an 'errors' key for error records.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with Currency and Error columns
    
    Returns:
    dict: Dictionary mapping category names to summary dataframes and 'errors' to error dataframe
    """
    summaries = {}
    categories = identify_categories(df)
    numeric_cols = get_numeric_columns(df)
    
    # Handle errors first
    error_df = df[df['Error'].notna()].copy()
    if not error_df.empty:
        summaries['errors'] = error_df
    
    # Generate summaries for each category
    for category in categories:
        # Group by both category and currency
        grouped = df.groupby([category, 'Currency'])
        
        # Create summary with count and sums of numeric columns
        agg_dict = {col: 'sum' for col in numeric_cols}
        agg_dict['Currency'] = 'first'  # Keep currency in the result
        
        summary = grouped.agg({
            **agg_dict,
            category: 'count'  # This will give us the count
        }).reset_index()
        
        # Rename the count column
        summary.rename(columns={category: 'count'}, inplace=True)
        
        # Reorder columns to put category and count first
        cols = [category, 'Currency', 'count'] + numeric_cols
        summary = summary[cols]
        
        summaries[category] = summary
    
    return summaries

# Initialize the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                use_pages=True)

# Create the app layout
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
    page_container
])

# Create pages/summary.py
"""
import dash
from dash import html, dash_table, register_page
import dash_bootstrap_components as dbc

register_page(__name__, path='/summary')

def create_summary_tables(df):
    summaries = generate_summary(df)
    
    summary_components = []
    
    # Display error summary if exists
    if 'errors' in summaries:
        error_card = dbc.Card([
            dbc.CardHeader("Errors Found"),
            dbc.CardBody([
                dash_table.DataTable(
                    data=summaries['errors'].to_dict('records'),
                    columns=[{"name": i, "id": i} for i in summaries['errors'].columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    style_header={'fontWeight': 'bold'}
                )
            ])
        ], className="mb-4")
        summary_components.append(error_card)
    
    # Display category summaries
    for category, summary_df in summaries.items():
        if category != 'errors':
            category_card = dbc.Card([
                dbc.CardHeader(f"Summary by {category}"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=summary_df.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in summary_df.columns],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={'fontWeight': 'bold'}
                    )
                ])
            ], className="mb-4")
            summary_components.append(category_card)
    
    return summary_components

layout = html.Div([
    dbc.Container([
        html.H1("DataFrame Summary", className="text-center mb-4"),
        html.Div(id="summary-content")
    ])
])

# Example usage in your callback:
@callback(
    Output("summary-content", "children"),
    Input("some-trigger", "value")
)
def update_summary(trigger):
    # Replace with your actual dataframe
    df = pd.DataFrame()  # Your dataframe here
    return create_summary_tables(df)
"""

# Create pages/comparison.py
"""
import dash
from dash import html, dcc, dash_table, register_page
import dash_bootstrap_components as dbc

register_page(__name__, path='/comparison')

layout = html.Div([
    dbc.Container([
        html.H1("DataFrame Comparison", className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.Label("Precision Threshold:"),
                dcc.Slider(
                    id='precision-slider',
                    min=0.001,
                    max=0.1,
                    step=0.001,
                    value=0.01,
                    marks={i/100: str(i/100) for i in range(1, 11)}
                )
            ])
        ]),
        html.Div(id="comparison-content")
    ])
])

# Comparison logic will go here in the next iteration
"""

if __name__ == '__main__':
    app.run_server(debug=True)