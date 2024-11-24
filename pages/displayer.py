from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Tuple
import re

def get_metric_icon_and_color(name: str, value: str) -> tuple[str, str]:
    """Helper function to determine icon and color based on metric name and value."""
    # Default values
    icon = "fa-chart-line"  # Default icon
    color = "#6c757d"       # Bootstrap secondary color
    
    # Check for storage-related metrics
    if any(term in name.lower() for term in ['storage', 'disk', 'memory', 'ram']):
        icon = "fa-hard-drive"
        color = "#0dcaf0"  # Bootstrap info color
    
    # Check for percentage values
    if '%' in value:
        icon = "fa-percent"
        if float(value.replace('%', '')) > 80:
            color = "#dc3545"  # Bootstrap danger color
        elif float(value.replace('%', '')) > 60:
            color = "#ffc107"  # Bootstrap warning color
    
    # Check for time-related metrics
    if any(term in name.lower() for term in ['time', 'duration', 'latency']):
        icon = "fa-clock"
        color = "#198754"  # Bootstrap success color
    
    return icon, color

def description_component(data: List[Tuple[str, str]]) -> html.Div:
    """Creates a responsive grid of description items with a clean, modern look."""
    
    description_items = []
    for key, value in data:
        item = dbc.Card(
            dbc.CardBody([
                html.H6(key, className="text-muted mb-1", 
                        style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                html.P(value, className="mb-0", 
                      style={'fontSize': '1rem', 'wordBreak': 'break-word'})
            ]),
            className="h-100 border-0 bg-dark",
            style={'minHeight': '100px'}
        )
        description_items.append(dbc.Col(item, lg=4, md=6, sm=12, className="mb-3"))

    return html.Div([
        html.H4("System Description", className="mb-4"),
        dbc.Row(description_items, className="g-3")
    ])

def metrics_component(data: List[Tuple[str, str]]) -> html.Div:
    """Creates a responsive grid of metric cards with icons and dynamic styling."""
    
    metric_items = []
    for key, value in data:
        icon, color = get_metric_icon_and_color(key, value)
        
        item = dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.I(className=f"fas {icon} fa-2x", 
                          style={'color': color, 'marginRight': '15px'}),
                    html.Div([
                        html.H6(key, className="text-muted mb-1", 
                               style={'fontSize': '0.8rem', 'fontWeight': 'bold'}),
                        html.H4(value, className="mb-0", 
                               style={'fontSize': '1.2rem', 'color': color})
                    ])
                ], style={'display': 'flex', 'alignItems': 'center'})
            ]),
            className="h-100 border-0 bg-dark",
            style={
                'minHeight': '90px',
                'transition': 'transform 0.2s',
                ':hover': {'transform': 'translateY(-5px)'}
            }
        )
        metric_items.append(dbc.Col(item, xl=2, lg=3, md=4, sm=6, className="mb-3"))

    return html.Div([
        html.H4("System Metrics", className="mb-4"),
        dbc.Row(metric_items, className="g-3")
    ])

# Optional CSS styles - add these to your assets/custom.css file
"""
.card {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

@media (min-width: 2000px) {
    .container {
        max-width: 2400px;
    }
}

/* Custom scrollbar for dark theme */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #343a40;
}

::-webkit-scrollbar-thumb {
    background: #495057;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #6c757d;
}
"""
