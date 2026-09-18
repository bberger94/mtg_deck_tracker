import os
import dash
from dash import Input, Output, State, ctx, html
import dash_bootstrap_components as dbc

from config import DECK_REPO_PATH
from services import deck_manager, git_manager
from components import layout

# Initialize Dash with a clean Bootstrap theme (LUX)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# --- Initialization ---
available_decks = deck_manager.get_available_decks()
initial_deck_path = os.path.join(DECK_REPO_PATH, available_decks[0]) if available_decks else ""
initial_branches = git_manager.get_branches(initial_deck_path) if initial_deck_path else []

# --- Layout ---
app.layout = layout.build_app_layout(available_decks, initial_branches)

# --- Callbacks ---
@app.callback(
    [Output('branch-selector', 'options'),
     Output('branch-selector', 'value'),
     Output('new-branch-input', 'value')],
    [Input('deck-selector', 'value'),
     Input('create-branch-btn', 'n_clicks')],
    [State('new-branch-input', 'value')]
)
def manage_branches(selected_deck, create_clicks, new_branch_name):
    if not selected_deck:
        return [], None, ""
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    if ctx.triggered_id == 'create-branch-btn' and new_branch_name:
        git_manager.create_branch(deck_path, new_branch_name)
    
    branches = git_manager.get_branches(deck_path)
    active_branch = git_manager.get_active_branch(deck_path)
    
    options = [{'label': b, 'value': b} for b in branches]
    val = active_branch if active_branch in branches else (branches[0] if branches else None)
    
    return options, val, ""

@app.callback(
    [Output('git-status-message', 'children'),
     Output('git-status-message', 'className'),
     Output('deck-display', 'children'),
     Output('fixed-preview-img', 'src'),  # <--- Target preview image tag
     Output('commit-msg-input', 'value')],
    [Input('branch-selector', 'value'),
     Input('commit-btn', 'n_clicks')],
    [State('deck-selector', 'value'),
     State('commit-msg-input', 'value')]
)
def update_deck_and_commit(selected_branch, commit_clicks, selected_deck, commit_msg):
    if not selected_branch or not selected_deck:
        return "Please select both a deck and a branch.", "status-banner status-warning", [], "", ""
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    triggered_id = ctx.triggered_id
    msg = ""
    
    if triggered_id == 'commit-btn':
        msg = git_manager.commit_changes(deck_path, commit_msg or "Update deck via Dashboard")
    else:
        msg = git_manager.checkout_branch(deck_path, selected_branch)
    
    banner_class = "status-banner status-warning" if ("Warning" in msg or "Error" in msg or "Not" in msg) else "status-banner status-success"
    
    deck_file_path = os.path.join(deck_path, "deck.txt")
    if not os.path.exists(deck_file_path):
        return msg, banner_class, [html.Div(f"Error: {deck_file_path} not found.")], "", ""
    
    grouped_cards = deck_manager.get_grouped_deck_data(deck_file_path)
    columns = layout.build_deck_columns(grouped_cards)
    
    # Extract Commander image URI for initial preview
    commander_src = ""
    if "Commander" in grouped_cards and grouped_cards["Commander"]:
        commander_src = grouped_cards["Commander"][0].get("image_uri", "")
            
    return msg, banner_class, columns, commander_src, "" 

if __name__ == '__main__':
    app.run(debug=True)