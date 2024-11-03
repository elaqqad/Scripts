# comparison.py
import dash
from dash import html, dcc, dash_table, register_page, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from summary import generate_summary, identify_categories, get_numeric_columns

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Compare full dataframes grouped by all categories"""
    categories = identify_categories(df1)
    numeric_cols = get_numeric_columns(df1)
    
    # Group by all categories and currency
    group_cols = categories + ['Currency']
    
    # Aggregate both dataframes
    agg_dict = {col: 'sum' for col in numeric_cols}
    df1_grouped = df1.groupby(group_cols).agg(agg_dict).reset_index()
    df2_grouped = df2.groupby(group_cols).agg(agg_dict).reset_index()
    
    # Merge the grouped dataframes
    merged = pd.merge(
        df1_grouped, df2_grouped,
        on=group_cols,
        suffixes=('_df1', '_df2'),
        how='outer'
    )
    
    # Calculate differences and filter based on threshold
    result_rows = []
    for col in numeric_cols:
        col_df1 = f'{col}_df1'
        col_df2 = f'{col}_df2'
        
        # Fill NaN with 0 for comparison
        merged[col_df1] = merged[col_df1].fillna(0)
        merged[col_df2] = merged[col_df2].fillna(0)
        
        # Calculate absolute and relative differences
        merged[f'{col}_diff'] = merged[col_df2] - merged[col_df1]
        merged[f'{col}_rel_diff'] = (merged[f'{col}_diff'].abs() / 
                                   merged[col_df1].abs().clip(lower=1e-10))
        
    # Filter rows where at least one column has difference above threshold
    diff_cols = [f'{col}_rel_diff' for col in numeric_cols]
    significant_diffs = merged[merged[diff_cols].max(axis=1) > threshold].copy()
    
    # Format numeric columns
    for col in numeric_cols:
        significant_diffs[f'{col}_df1'] = significant_diffs[f'{col}_df1'].round(4)
        significant_diffs[f'{col}_df2'] = significant_diffs[f'{col}_df2'].round(4)
        significant_diffs[f'{col}_diff'] = significant_diffs[f'{col}_diff'].round(4)
    
    return significant_diffs

def create_comparison_table(df: pd.DataFrame) -> dash_table.DataTable:
    """Create a formatted comparison table"""
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
            } for col in df.columns if '_diff' in col
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} > 0'.format(col=col),
                    'column_id': col
                },
                'color': 'green'
            } for col in df.columns if '_diff' in col
        ]
    )

def create_comparison_layout(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float) -> html.Div:
    """Create improved layout for comparison display"""
    comparison_components = []
    
    # Get full comparison
    full_comparison = compare_dataframes(df1, df2, threshold)
    
    if not full_comparison.empty:
        comparison_card = dbc.Card([
            dbc.CardHeader("Significant Differences", style={'font-weight': 'bold'}),
            dbc.CardBody([
                create_comparison_table(full_comparison)
            ])
        ], className="mb-4")
        comparison_components.append(comparison_card)
    else:
        comparison_components.append(
            html.Div("No significant differences found", 
                    className="text-center p-4")
        )
    
    return html.Div([
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
                        marks={i/100: f'{i/100:.3f}' for i in range(1, 11)}
                    )
                ])
            ], className="mb-4"),
            html.Div(comparison_components)
        ])
    ])


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

@callback(
    Output("comparison-content", "children"),
    [Input("precision-slider", "value"),
     Input("stored-data1", "data"),
     Input("stored-data2", "data")]
)
def update_comparison(threshold, data1, data2):
    if data1 is None or data2 is None:
        return html.Div("Please load both datasets")
    
    # Convert stored data back to DataFrames
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)
    
    # Generate summaries
    df1_summaries = generate_summary(df1)
    df2_summaries = generate_summary(df2)
    
    # Compare summaries    
    return create_comparison_layout(df1_summaries, df2_summaries, threshold)