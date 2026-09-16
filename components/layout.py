from dash import dcc, html

def build_app_layout(available_decks, available_branches):
    """Builds the main structural layout of the dashboard."""
    return html.Div([
        html.Div([
            html.H2("MTG Git Deck Manager", style={'margin': '0'}),
            html.Div([
                html.Div([
                    html.Label("Deck"),
                    dcc.Dropdown(
                        id='deck-selector',
                        options=[{'label': d, 'value': d} for d in available_decks],
                        value=available_decks[0] if available_decks else None,
                        clearable=False
                    )
                ], className='control-item'),
                html.Div([
                    html.Label("Branch"),
                    dcc.Dropdown(
                        id='branch-selector',
                        options=[{'label': b, 'value': b} for b in available_branches],
                        value=available_branches[0] if available_branches else None,
                        clearable=False
                    )
                ], className='control-item'),
            ], className='controls-group'),
        ], className='app-header'),
        
        html.Div(id='git-status-message', style={'padding': '10px 30px', 'fontWeight': 'bold', 'color': '#059669'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Img(id='fixed-preview-img', alt="Hover a card to preview")
                ], className='preview-card-container')
            ], className='sidebar-preview'),

            html.Div(id='deck-display', className='deck-columns-container')
        ], className='main-layout')
    ])

def build_deck_columns(grouped_cards):
    """Takes a grouped dictionary of cards and returns Dash HTML columns."""
    TYPE_ORDER = ["Planeswalkers", "Creatures", "Sorceries", "Instants", "Artifacts", "Enchantments", "Lands", "Other"]
    columns = []
    
    for card_type in TYPE_ORDER:
        if card_type in grouped_cards:
            cards = grouped_cards[card_type]
            total_count = sum(c['qty'] for c in cards)
            
            card_rows = [
                html.Div([
                    html.Span(f"{c['qty']}", className='card-qty'),
                    html.Span(c['name'], className='card-name')
                ], className='card-row', **{'data-image': c['image_uri'] or ''})
                for c in cards
            ]
            
            columns.append(html.Div([
                html.Div(f"{card_type} ({total_count})", className='type-header'),
                html.Div(card_rows)
            ], className='type-column'))
            
    return columns