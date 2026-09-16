import os
import dash
from dash import Input, Output
from config import DECK_REPO_PATH
from services import deck_manager, git_manager
from components import layout

app = dash.Dash(__name__)

# --- Initialization ---
available_decks = deck_manager.get_available_decks()
initial_deck_path = os.path.join(DECK_REPO_PATH, available_decks[0]) if available_decks else ""
initial_branches = git_manager.get_branches(initial_deck_path) if initial_deck_path else []

# --- Layout ---
app.layout = layout.build_app_layout(available_decks, initial_branches)

# --- Callbacks ---
@app.callback(
    [Output('branch-selector', 'options'),
     Output('branch-selector', 'value')],
    [Input('deck-selector', 'value')]
)
def update_branch_options(selected_deck):
    if not selected_deck:
        return [], None
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    branches = git_manager.get_branches(deck_path)
    active_branch = git_manager.get_active_branch(deck_path)
    
    options = [{'label': b, 'value': b} for b in branches]
    val = active_branch if active_branch in branches else (branches[0] if branches else None)
    
    return options, val

@app.callback(
    [Output('git-status-message', 'children'),
     Output('deck-display', 'children')],
    [Input('branch-selector', 'value'),
     Input('deck-selector', 'value')]
)
def update_deck_view(selected_branch, selected_deck):
    if not selected_branch or not selected_deck:
        return "Please select both a deck and a branch.", []
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    
    # Git Checkout
    msg = git_manager.checkout_branch(deck_path, selected_branch)
    
    # Load and Render Deck
    deck_file_path = os.path.join(deck_path, "deck.txt")
    if not os.path.exists(deck_file_path):
        return msg, [dash.html.Div(f"Error: {deck_file_path} not found.")]
    
    grouped_cards = deck_manager.get_grouped_deck_data(deck_file_path)
    columns = layout.build_deck_columns(grouped_cards)
            
    return msg, columns

if __name__ == '__main__':
    app.run(debug=True)