# summary.py
import dash
from dash import html, dash_table, register_page, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from typing import Dict

register_page(__name__, path='/summary')

def identify_categories(df: pd.DataFrame, threshold: int = 20) -> list:
    """Identify categorical columns based on unique value count"""
    categories = []
    for col in df.columns:
        if col not in ['Currency', 'Error'] and df[col].nunique() < threshold:
            categories.append(col)
    return categories

def get_numeric_columns(df: pd.DataFrame) -> list:
    """Get numerical columns excluding Currency and Error"""
    return [col for col in df.select_dtypes(include=[np.number]).columns 
            if col not in ['Currency', 'Error']]

def generate_summary(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
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
    if 'Error' in df.columns:
        error_df = df[df['Error'].notna()].copy()
        if not error_df.empty:
            summaries['errors'] = error_df
    
    # Generate summaries for each category
    for category in categories:
        # Ensure we have at least one row of data
        if df[category].empty:
            continue
            
        # Create aggregation dictionary
        agg_dict = {
            'Currency': pd.NamedAgg(column='Currency', aggfunc='first'),
            f'{category}_count': pd.NamedAgg(column=category, aggfunc='count')
        }
        
        # Add numeric columns to aggregation
        for col in numeric_cols:
            agg_dict[f'{col}_sum'] = pd.NamedAgg(column=col, aggfunc='sum')
        
        # Group by both category and currency
        try:
            summary = (df.groupby([category, 'Currency'])
                      .agg(**agg_dict)
                      .reset_index(drop=False))
            
            # Rename the count column
            summary.rename(columns={f'{category}_count': 'count'}, inplace=True)
            
            # Reorder columns to put category and count first
            cols = [category, 'Currency', 'count'] + [f'{col}_sum' for col in numeric_cols]
            summary = summary[cols]
            
            summaries[category] = summary
            
        except Exception as e:
            print(f"Error processing category {category}: {str(e)}")
            continue
    
    return summaries

def create_summary_layout(summaries: Dict[str, pd.DataFrame]) -> html.Div:
    """Create the HTML layout for the summary page"""
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
    
    return html.Div([
        dbc.Container([
            html.H1("DataFrame Summary", className="text-center mb-4"),
            html.Div(summary_components)
        ])
    ])

# Page layout
layout = html.Div([
    dbc.Container([
        html.H1("DataFrame Summary", className="text-center mb-4"),
        html.Div(id="summary-content")
    ])
])

@callback(
    Output("summary-content", "children"),
    Input("stored-data", "data")  # You'll need to set up data storage
)
def update_summary(data):
    if data is None:
        return html.Div("No data loaded")
    
    # Convert stored data back to DataFrame
    df = pd.DataFrame(data)
    summaries = generate_summary(df)
    return create_summary_layout(summaries)