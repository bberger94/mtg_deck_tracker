from dash import dcc, html
import dash_bootstrap_components as dbc
import os
import json
from config import DECK_REPO_PATH

def build_app_layout(available_decks, available_branches):
    deck_options = []
    for d in available_decks:
        label = d
        meta_path = os.path.join(DECK_REPO_PATH, d, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    label = json.load(f).get("name", d)
            except Exception:
                pass
        deck_options.append({'label': label, 'value': d})

    return html.Div([
        # Header Toolbar
        html.Header([
            html.H1("MTG GIT DECK", className="header-title"),
            
            html.Div([
                html.Button('+ New Deck', id='open-new-deck-modal-btn', n_clicks=0, className='action-btn btn-secondary header-btn'),

                html.Div([
                    html.Span("Deck", className="control-label"),
                    dcc.Dropdown(
                        id='deck-selector',
                        options=deck_options,
                        value=available_decks[0] if available_decks else None,
                        clearable=False,
                        className="custom-dropdown deck-select"
                    )
                ], className="control-unit"),

                html.Div([
                    html.Span("Sort By", className="control-label"),
                    dcc.Dropdown(
                        id='sort-selector',
                        options=[{'label': 'Name', 'value': 'name'}, {'label': 'Mana', 'value': 'cmc'}],
                        value='name',
                        clearable=False,
                        className="custom-dropdown branch-select"
                    )
                ], className="control-unit"),

                # --- CARD SEARCH BAR (No Inline Styles) ---
                html.Div([
                    dcc.Input(
                        id='add-card-input',
                        type='text',
                        placeholder='Search and add card...',
                        autoComplete='off',
                        list='add-card-autocomplete-list',
                        className='form-control header-btn add-card-search'
                    ),
                    html.Datalist(id='add-card-autocomplete-list'),
                    dbc.Button('Add', id='add-card-btn', n_clicks=0, color="primary", className="header-btn ms-2")
                ], className="d-flex align-items-center mx-3"),
                # --------------------------------

                # Manage Deck Dropdown
                dbc.DropdownMenu(
                    label="Manage Deck",
                    children=[
                        dbc.DropdownMenuItem("Bulk Add Cards", id="open-bulk-add-modal-btn", n_clicks=0),
                        dbc.DropdownMenuItem("Set Commander", id="open-set-cmdr-modal-btn", n_clicks=0),
                        dbc.DropdownMenuItem("Git Actions", id="open-git-modal-btn", n_clicks=0),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem("Remove all cards", id="menu-remove-all", n_clicks=0, className="text-danger fw-bold"),
                    ],
                    color="secondary",
                    toggleClassName="header-btn manage-deck-toggle"
                )
            ], className="toolbar-controls"),
        ], className='top-bar'),

        # --- Set Commander Modal (Small) ---
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Set Commander")),
            dbc.ModalBody([
                html.Label("Search for a Commander", className="fw-bold mb-1"),
                dcc.Input(
                    id='set-cmdr-input',
                    type='text',
                    placeholder='Enter card name...',
                    autoComplete='off',
                    list='set-cmdr-autocomplete-list',
                    className='form-control mb-4'
                ),
                html.Datalist(id='set-cmdr-autocomplete-list')
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="close-set-cmdr-modal-btn", className="me-auto", n_clicks=0, color="light"),
                dbc.Button("Set", id="submit-cmdr-btn", color="primary", n_clicks=0)
            ])
        ], id="set-cmdr-modal", is_open=False, centered=True, size="sm"),

        # --- Bulk Add Modal ---
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Bulk Add Cards")),
            dbc.ModalBody([
                html.P("Paste card names below (e.g., '1 Sol Ring' or just 'Sol Ring' on each line).", className="text-muted small mb-2"),
                dbc.Textarea(id="bulk-add-textarea", placeholder="1 Sol Ring\n1 Arcane Signet\n...", className="mb-3 bulk-textarea"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="close-bulk-add-modal-btn", className="me-auto", n_clicks=0, color="light"),
                dbc.Button("Add Cards", id="bulk-add-submit-btn", color="primary", n_clicks=0)
            ])
        ], id="bulk-add-modal", is_open=False, centered=True, size="lg"),

        # --- New Deck Modal ---
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Create Deck")),
            dbc.ModalBody([
                html.Label("Deck Name (Required)", className="fw-bold mb-1"),
                dbc.Input(id='new-deck-name-input', type='text', placeholder='e.g., My Slivers Deck', autoComplete='off', className="mb-4"),
                
                html.Label("Specify a Commander", className="fw-bold mb-1"),
                dcc.Input(
                    id='new-deck-commander-input',
                    type='text',
                    placeholder='Search commander...',
                    autoComplete='off',
                    list='new-deck-autocomplete-list',
                    className='form-control mb-4'
                ),
                html.Datalist(id='new-deck-autocomplete-list')
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="close-new-deck-modal-btn", className="me-auto", n_clicks=0, color="light"),
                dbc.Button("Create Deck", id="create-deck-submit-btn", color="primary", n_clicks=0)
            ])
        ], id="new-deck-modal", is_open=False, centered=True),

        # --- Git Management Modal ---
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Git Management")),
            dbc.ModalBody([
                html.Label("Current Branch", className="fw-bold mb-1"),
                dcc.Dropdown(
                    id='branch-selector',
                    options=[{'label': b, 'value': b} for b in available_branches] + [{'label': '+ Create New Branch', 'value': '_create_new_'}],
                    value=available_branches[0] if available_branches else None,
                    clearable=False,
                    className="mb-2"
                ),
                
                # Hidden by default using Bootstrap 'd-none' instead of style dictionary
                html.Div([
                    dbc.Input(id='new-branch-input', type='text', placeholder='New branch name...', autoComplete='off'),
                    dbc.Button('Create', id='create-branch-btn', n_clicks=0, color="secondary", className="ms-2")
                ], id='create-branch-container', className='mb-4 d-none'),
                
                html.Label("Commit Changes", className="fw-bold mb-1 mt-3"),
                html.Div([
                    dbc.Input(id='commit-msg-input', type='text', placeholder='Commit message...', autoComplete='off'),
                    dbc.Button('Commit', id='commit-btn', n_clicks=0, color="primary", className="ms-2")
                ], className='d-flex'),

                html.Label("Merge Branch", className="fw-bold mb-1 mt-3"),
                html.Div([
                    dcc.Dropdown(
                        id='merge-branch-selector',
                        placeholder="Select branch to merge into current...",
                        clearable=False,
                        className="flex-grow-1"
                    ),
                    dbc.Button('Merge', id='merge-btn', n_clicks=0, color="warning", className="ms-2")
                ], className='d-flex mb-4'),
                
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-git-modal-btn", className="ms-auto", n_clicks=0)
            )
        ], id="git-modal", is_open=False, centered=True),

        html.Div(id='git-status-message', className='status-banner status-success', children="Ready"),

        html.Div([
            html.Div([
                html.Div([
                    html.Img(id='fixed-preview-img', alt="Hover a card to preview")
                ], className='preview-card-container shadow-sm')
            ], className='sidebar-preview'),
            html.Div(id='deck-display', className='deck-columns-container')
        ], className='main-layout')
    ])

def build_deck_columns(grouped_cards, sort_by="name"):
    TYPE_ORDER = ["Commander", "Creatures", "Sorceries", "Instants", "Planeswalkers", "Enchantments", "Artifacts", "Lands", "Other"]
    columns = []
    for card_type in TYPE_ORDER:
        if card_type in grouped_cards:
            cards = grouped_cards[card_type]
            total_count = sum(c['qty'] for c in cards)
            
            if sort_by == 'cmc':
                cards = sorted(cards, key=lambda c: (c['cmc'], c['name']))
            else:
                cards = sorted(cards, key=lambda c: c['name'])
            
            card_rows = []
            for c in cards:
                card_rows.append(html.Div([
                    html.A([
                        html.Span(f"{c['qty']}", className='card-qty'),
                        html.Span(c['name'], className='card-name')
                    ], href=c.get('scryfall_uri', '#'), target="_blank", className='card-link'),
                    html.Button("✖", id={'type': 'delete-card-btn', 'index': c['name']}, className='delete-btn')
                ], className='card-row', **{'data-image': c['image_uri'] or ''}))
            
            columns.append(html.Div([
                html.Div(f"{card_type} ({total_count})", className='type-header'),
                html.Div(card_rows)
            ], className='type-column shadow-sm'))
            
    return columns