# summary.py
import dash
from dash import html, dash_table, register_page, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from typing import Dict, List, Set

def identify_categories(df: pd.DataFrame, threshold: int = 20) -> list:
    """Identify categorical columns based on unique value count"""
    return [col for col in df.columns 
            if col not in ['Currency', 'Error'] 
            and df[col].nunique() < threshold]

def get_numeric_columns(df: pd.DataFrame) -> list:
    """Get numerical columns excluding Currency and Error"""
    return [col for col in df.select_dtypes(include=[np.number]).columns 
            if col not in ['Currency', 'Error']]

def identify_single_value_categories(df: pd.DataFrame, categories: List[str]) -> Set[str]:
    """Identify categories that have only one unique value"""
    return {cat for cat in categories if df[cat].nunique() == 1}

def format_numeric_column(column: pd.Series) -> pd.Series:
    """Format numeric values with 4 decimal places and remove zeros"""
    formatted = column.round(4)
    return formatted.where(formatted != 0, '')

def generate_summary(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Generate improved summary with combined single-value categories and better formatting.
    """
    summaries = {}
    categories = identify_categories(df)
    numeric_cols = get_numeric_columns(df)
    single_value_cats = identify_single_value_categories(df, categories)
    
    # Handle errors first
    if 'Error' in df.columns:
        error_df = df[df['Error'].notna()].copy()
        if not error_df.empty:
            summaries['errors'] = error_df
    
    # First, create a summary grouped by Currency and single-value categories
    if single_value_cats:
        group_cols = ['Currency'] + list(single_value_cats)
        agg_dict = {col: 'sum' for col in numeric_cols}
        agg_dict.update({cat: 'first' for cat in single_value_cats})
        
        base_summary = (df.groupby(group_cols)
                       .agg(agg_dict)
                       .reset_index())
        
        # Add count column
        base_summary['count'] = df.groupby(group_cols).size().values
        
        # Format numeric columns
        for col in numeric_cols:
            base_summary[col] = format_numeric_column(base_summary[col])
        
        summaries['base'] = base_summary
    
    # Then handle remaining categories
    remaining_cats = [cat for cat in categories if cat not in single_value_cats]
    for category in remaining_cats:
        if df[category].empty:
            continue
            
        # Create aggregation dictionary
        agg_dict = {col: 'sum' for col in numeric_cols}
        
        # Group by category and currency
        try:
            summary = (df.groupby([category, 'Currency'])
                      .agg(agg_dict)
                      .reset_index())
            
            # Add count column
            summary['count'] = df.groupby([category, 'Currency']).size().values
            
            # Format numeric columns
            for col in numeric_cols:
                summary[col] = format_numeric_column(summary[col])
            
            # Reorder columns
            cols = [category, 'Currency', 'count'] + numeric_cols
            summary = summary[cols]
            
            summaries[category] = summary
            
        except Exception as e:
            print(f"Error processing category {category}: {str(e)}")
            continue
    
    return summaries

def create_summary_table(df: pd.DataFrame) -> dash_table.DataTable:
    """Create a formatted DataTable with conditional styling"""
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'right',
            'padding': '10px',
            'minWidth': '100px'
        },
        style_header={
            'fontWeight': 'bold',
            'backgroundColor': '#f8f9fa',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{{{col}}} < 0'.format(col=col),
                    'column_id': col
                },
                'color': 'red'
            } for col in df.select_dtypes(include=[np.number]).columns
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} > 0'.format(col=col),
                    'column_id': col
                },
                'color': 'green'
            } for col in df.select_dtypes(include=[np.number]).columns
        ]
    )

def create_summary_layout(summaries: Dict[str, pd.DataFrame]) -> html.Div:
    """Create improved layout for summary display"""
    summary_components = []
    
    # Display base summary (Currency + single-value categories) first
    if 'base' in summaries:
        base_card = dbc.Card([
            dbc.CardHeader("Base Summary", style={'font-weight': 'bold'}),
            dbc.CardBody([
                create_summary_table(summaries['base'])
            ])
        ], className="mb-4")
        summary_components.append(base_card)
    
    # Display error summary if exists
    if 'errors' in summaries:
        error_card = dbc.Card([
            dbc.CardHeader("Errors Found", style={'font-weight': 'bold', 'color': 'red'}),
            dbc.CardBody([
                create_summary_table(summaries['errors'])
            ])
        ], className="mb-4")
        summary_components.append(error_card)
    
    # Display remaining category summaries
    for category, summary_df in summaries.items():
        if category not in ['errors', 'base']:
            category_card = dbc.Card([
                dbc.CardHeader(f"Summary by {category}", style={'font-weight': 'bold'}),
                dbc.CardBody([
                    create_summary_table(summary_df)
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