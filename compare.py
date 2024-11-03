import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np

def identify_categories(df, threshold=20):
    """Identify categorical columns based on unique value count"""
    categories = []
    for col in df.columns:
        if col not in ['Currency', 'Error']:
            unique_count = df[col].nunique()
            if unique_count < threshold:
                categories.append(col)
    return categories

def get_column_types(df):
    """Classify columns as numeric or string"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    string_cols = df.select_dtypes(include=['object']).columns
    return list(numeric_cols), list(string_cols)

def summarize_by_category(df, categories):
    """Create summary statistics for the dataframe grouped by categories"""
    summaries = []
    numeric_cols, string_cols = get_column_types(df)
    
    for category in categories:
        # Basic category statistics
        category_stats = {
            'Category': category,
            'Unique Values': df[category].nunique(),
            'Value Distribution': df[category].value_counts().to_dict()
        }
        
        # Numeric column statistics by category
        for num_col in numeric_cols:
            if num_col != category:
                stats = df.groupby(category)[num_col].agg(['mean', 'std', 'min', 'max']).round(2)
                category_stats[f'{num_col}_stats'] = stats.to_dict()
        
        summaries.append(category_stats)
    
    return summaries

def compare_dataframes(df1, df2, categories, precision=0.01):
    """Compare two dataframes and return differences"""
    comparison_results = []
    
    for category in categories:
        # Compare category-wise
        df1_values = set(df1[category].unique())
        df2_values = set(df2[category].unique())
        
        new_values = df2_values - df1_values
        removed_values = df1_values - df2_values
        
        numeric_cols, _ = get_column_types(df1)
        
        # For each category value present in both dataframes
        common_values = df1_values.intersection(df2_values)
        value_differences = {}
        
        for value in common_values:
            df1_subset = df1[df1[category] == value]
            df2_subset = df2[df2[category] == value]
            
            for col in numeric_cols:
                if col != category:
                    diff = abs(df1_subset[col].mean() - df2_subset[col].mean())
                    if diff > precision:
                        value_differences[value] = {
                            'column': col,
                            'diff': diff,
                            'df1_value': df1_subset[col].mean(),
                            'df2_value': df2_subset[col].mean()
                        }
        
        comparison_results.append({
            'category': category,
            'new_values': list(new_values),
            'removed_values': list(removed_values),
            'value_differences': value_differences
        })
    
    return comparison_results

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Example dataframes (replace with your actual data)
df1 = pd.DataFrame()  # Your first dataframe
df2 = pd.DataFrame()  # Your second dataframe

# Identify categories
categories = identify_categories(df1)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("DataFrame Analysis Dashboard", className="text-center mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("DataFrame Summary"),
                dbc.CardBody([
                    html.Div(id="summary-content")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("DataFrame Comparison"),
                dbc.CardBody([
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
        ], width=12)
    ])
])

@app.callback(
    Output("summary-content", "children"),
    [Input("dummy-trigger", "children")]  # Dummy input for initial load
)
def update_summary():
    """Update the summary content"""
    summaries = summarize_by_category(df1, categories)
    
    summary_components = []
    for summary in summaries:
        category_card = dbc.Card([
            dbc.CardHeader(f"Category: {summary['Category']}"),
            dbc.CardBody([
                html.H6("Value Distribution:"),
                dash_table.DataTable(
                    data=[
                        {"Value": k, "Count": v}
                        for k, v in summary['Value Distribution'].items()
                    ],
                    columns=[
                        {"name": "Value", "id": "Value"},
                        {"name": "Count", "id": "Count"}
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    style_header={'fontWeight': 'bold'}
                )
            ])
        ], className="mb-3")
        summary_components.append(category_card)
    
    return html.Div(summary_components)

@app.callback(
    Output("comparison-content", "children"),
    [Input("precision-slider", "value")]
)
def update_comparison(precision):
    """Update the comparison content"""
    comparison_results = compare_dataframes(df1, df2, categories, precision)
    
    comparison_components = []
    for result in comparison_results:
        category = result['category']
        
        # Create a card for each category comparison
        comparison_card = dbc.Card([
            dbc.CardHeader(f"Category: {category}"),
            dbc.CardBody([
                html.Div([
                    html.H6("New Values:"),
                    html.P(", ".join(map(str, result['new_values'])) or "None"),
                    
                    html.H6("Removed Values:"),
                    html.P(", ".join(map(str, result['removed_values'])) or "None"),
                    
                    html.H6("Significant Differences:"),
                    dash_table.DataTable(
                        data=[
                            {
                                "Value": value,
                                "Column": diff_info['column'],
                                "Difference": f"{diff_info['diff']:.3f}",
                                "DF1 Value": f"{diff_info['df1_value']:.3f}",
                                "DF2 Value": f"{diff_info['df2_value']:.3f}"
                            }
                            for value, diff_info in result['value_differences'].items()
                        ],
                        columns=[
                            {"name": col, "id": col}
                            for col in ["Value", "Column", "Difference", "DF1 Value", "DF2 Value"]
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={'fontWeight': 'bold'}
                    )
                ])
            ])
        ], className="mb-3")
        
        comparison_components.append(comparison_card)
    
    return html.Div(comparison_components)

if __name__ == '__main__':
    app.run_server(debug=True)