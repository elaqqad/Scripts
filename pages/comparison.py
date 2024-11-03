# comparison.py
import dash
from dash import html, dcc, dash_table, register_page, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from summary import generate_summary

register_page(__name__, path='/comparison')

def compare_summaries(df1_summaries: dict, df2_summaries: dict, threshold: float = 0.01) -> dict:
    """
    Compare two sets of summaries and return differences above threshold
    """
    differences = {}
    
    # Compare each category present in either summary
    all_categories = set(df1_summaries.keys()) | set(df2_summaries.keys())
    
    for category in all_categories:
        if category == 'errors':
            continue
            
        category_diffs = []
        
        # Handle cases where category exists in both summaries
        if category in df1_summaries and category in df2_summaries:
            df1_summary = df1_summaries[category]
            df2_summary = df2_summaries[category]
            
            # Merge the summaries on category and currency
            merged = pd.merge(
                df1_summary, 
                df2_summary,
                on=[category, 'Currency'],
                suffixes=('_df1', '_df2'),
                how='outer'
            )
            
            # Compare numeric columns
            numeric_cols = [col for col in df1_summary.columns 
                          if col not in [category, 'Currency', 'count']]
            
            for col in numeric_cols:
                col_df1 = f'{col}_df1'
                col_df2 = f'{col}_df2'
                
                # Calculate relative difference where both values exist
                mask = merged[col_df1].notna() & merged[col_df2].notna()
                merged.loc[mask, f'{col}_diff'] = (
                    (merged[col_df2] - merged[col_df1]).abs() / 
                    merged[col_df1].abs().clip(lower=1e-10)
                )
                
                # Filter significant differences
                significant_diffs = merged[
                    merged[f'{col}_diff'] > threshold
                ][[category, 'Currency', col_df1, col_df2, f'{col}_diff']]
                
                if not significant_diffs.empty:
                    category_diffs.append({
                        'column': col,
                        'differences': significant_diffs
                    })
        
        # Handle categories present in only one summary
        elif category in df1_summaries:
            category_diffs.append({
                'message': f'Category {category} only present in first dataset',
                'data': df1_summaries[category]
            })
        else:
            category_diffs.append({
                'message': f'Category {category} only present in second dataset',
                'data': df2_summaries[category]
            })
        
        if category_diffs:
            differences[category] = category_diffs
    
    return differences

def create_comparison_layout(differences: dict) -> html.Div:
    """Create the HTML layout for the comparison results"""
    comparison_components = []
    
    for category, diffs in differences.items():
        category_cards = []
        
        for diff in diffs:
            if 'message' in diff:
                # Handle category present in only one dataset
                card = dbc.Card([
                    dbc.CardHeader(diff['message']),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=diff['data'].to_dict('records'),
                            columns=[{"name": i, "id": i} for i in diff['data'].columns],
                            style_table={'overflowX': 'auto'}
                        )
                    ])
                ], className="mb-3")
            else:
                # Handle numeric differences
                card = dbc.Card([
                    dbc.CardHeader(f"Differences in {diff['column']}"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=diff['differences'].to_dict('records'),
                            columns=[{"name": i, "id": i} for i in diff['differences'].columns],
                            style_table={'overflowX': 'auto'}
                        )
                    ])
                ], className="mb-3")
            
            category_cards.append(card)
        
        category_section = html.Div([
            html.H3(f"Differences in {category}", className="mb-3"),
            html.Div(category_cards)
        ], className="mb-4")
        
        comparison_components.append(category_section)
    
    return html.Div([
        dbc.Container([
            html.H1("DataFrame Comparison", className="text-center mb-4"),
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
    differences = compare_summaries(df1_summaries, df2_summaries, threshold)
    
    return create_comparison_layout(differences)