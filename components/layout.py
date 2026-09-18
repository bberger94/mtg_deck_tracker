from dash import dcc, html

def build_app_layout(available_decks, available_branches):
    """Builds the main structural layout of the dashboard with pixel-aligned header controls."""
    return html.Div([
        # Header Toolbar
        html.Header([
            html.H1("MTG GIT DECK MANAGER", className="header-title"),
            
            html.Div([
                # Deck Selector
                html.Div([
                    html.Span("Deck", className="control-label"),
                    dcc.Dropdown(
                        id='deck-selector',
                        options=[{'label': d, 'value': d} for d in available_decks],
                        value=available_decks[0] if available_decks else None,
                        clearable=False,
                        className="custom-dropdown deck-select"
                    )
                ], className="control-unit"),

                # Branch Selector
                html.Div([
                    html.Span("Branch", className="control-label"),
                    dcc.Dropdown(
                        id='branch-selector',
                        options=[{'label': b, 'value': b} for b in available_branches],
                        value=available_branches[0] if available_branches else None,
                        clearable=False,
                        className="custom-dropdown branch-select"
                    )
                ], className="control-unit"),

                # Create Branch Inline Group
                html.Div([
                    dcc.Input(
                        id='new-branch-input', 
                        type='text', 
                        placeholder='New branch...', 
                        className='action-input'
                    ),
                    html.Button('Create', id='create-branch-btn', n_clicks=0, className='action-btn btn-secondary')
                ], className='action-group'),
                
                # Commit Inline Group
                html.Div([
                    dcc.Input(
                        id='commit-msg-input', 
                        type='text', 
                        placeholder='Commit message...', 
                        className='action-input commit-input'
                    ),
                    html.Button('Commit', id='commit-btn', n_clicks=0, className='action-btn btn-primary')
                ], className='action-group'),

            ], className="toolbar-controls"),
        ], className='top-bar'),
        
        # Status Banner
        html.Div(id='git-status-message', className='status-banner status-success', children="Ready"),

        # Main Workspace
        html.Div([
            # Fixed Preview Box
            html.Div([
                html.Div([
                    html.Img(id='fixed-preview-img', alt="Hover a card to preview")
                ], className='preview-card-container shadow-sm')
            ], className='sidebar-preview'),

            # Deck Layout Grid
            html.Div(id='deck-display', className='deck-columns-container')
        ], className='main-layout')
    ])


def build_deck_columns(grouped_cards):
    """Takes a grouped dictionary of cards and returns Dash HTML columns."""
    TYPE_ORDER = [
        "Commander", 
        "Creatures", 
        "Sorceries", 
        "Instants", 
        "Planeswalkers", 
        "Enchantments", 
        "Artifacts", 
        "Lands", 
        "Other"
    ]
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
            ], className='type-column shadow-sm'))
            
    return columns