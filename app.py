import os
import json
import dash
from dash import Input, Output, State, ctx, html, ALL, no_update
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
     Output('new-branch-input', 'value'),
     Output('create-branch-container', 'className'),
     Output('merge-branch-selector', 'options'),
     Output('merge-branch-selector', 'value')],
    [Input('deck-selector', 'value'),
     Input('create-branch-btn', 'n_clicks'),
     Input('branch-selector', 'value')],
    [State('new-branch-input', 'value')]
)
def manage_branches(selected_deck, create_clicks, selected_branch, new_branch_name):
    if not selected_deck:
        return [], None, "", 'd-none', [], None
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    triggered = ctx.triggered_id
    
    container_class = 'mb-4 d-none'
    
    # Process Creation first so the new branch appears in our branches list
    if triggered == 'create-branch-btn' and new_branch_name:
        git_manager.create_branch(deck_path, new_branch_name)
        git_manager.checkout_branch(deck_path, new_branch_name)
        selected_branch = new_branch_name
    
    branches = git_manager.get_branches(deck_path)
    active_branch = git_manager.get_active_branch(deck_path)
    
    # --- FIX: Stop overriding the user's selection ---
    if triggered == 'branch-selector':
        if selected_branch == '_create_new_':
            container_class = 'mb-4 d-flex'
            val = '_create_new_'
        else:
            val = selected_branch  # Respect the new branch being switched to!
    elif triggered == 'create-branch-btn' and new_branch_name:
        val = new_branch_name
    else:
        # Initial load or changing to a completely different deck
        val = active_branch if active_branch in branches else (branches[0] if branches else None)
        
    # Main selector options
    options = [{'label': b, 'value': b} for b in branches]
    options.append({'label': '+ Create New Branch', 'value': '_create_new_'})
    
    # Merge selector options (exclude the branch we are currently actively switching to)
    current_for_merge = val if val != '_create_new_' else active_branch
    merge_options = [{'label': b, 'value': b} for b in branches if b != current_for_merge]
    merge_val = merge_options[0]['value'] if merge_options else None
    
    reset_new_branch = "" if triggered == 'create-branch-btn' else (new_branch_name or "")
    
    return options, val, reset_new_branch, container_class, merge_options, merge_val

@app.callback(
    [Output('git-status-message', 'children'),
     Output('git-status-message', 'className'),
     Output('deck-display', 'children'),
     Output('fixed-preview-img', 'src'),
     Output('commit-msg-input', 'value'),
     Output('bulk-add-textarea', 'value'),
     Output('set-cmdr-input', 'value'),
     Output('add-card-input', 'value')], # <-- Added Output to clear search bar
    [Input('branch-selector', 'value'),
     Input('create-branch-btn', 'n_clicks'),
     Input('commit-btn', 'n_clicks'),
     Input('merge-btn', 'n_clicks'),
     Input('bulk-add-submit-btn', 'n_clicks'),
     Input('menu-remove-all', 'n_clicks'),
     Input('submit-cmdr-btn', 'n_clicks'),
     Input('add-card-btn', 'n_clicks'),  # <-- Added Add Button Input
     Input({'type': 'delete-card-btn', 'index': ALL}, 'n_clicks'), 
     Input('sort-selector', 'value')],
    [State('deck-selector', 'value'),
     State('commit-msg-input', 'value'),
     State('bulk-add-textarea', 'value'),
     State('set-cmdr-input', 'value'),
     State('new-branch-input', 'value'),
     State('merge-branch-selector', 'value'),
     State('add-card-input', 'value')]   # <-- Added Search Bar State
)
def update_deck_and_commit(selected_branch, create_clicks, commit_clicks, merge_clicks, bulk_clicks, remove_all_clicks, cmdr_clicks, add_card_clicks, delete_clicks, sort_by, selected_deck, commit_msg, bulk_add_text, change_cmdr_name, new_branch_name, merge_branch_name, add_card_name): 
    if not selected_branch or not selected_deck:
        return "Please select both a deck and a branch.", "status-banner status-warning", [], "", "", "", "", ""
    
    deck_path = os.path.join(DECK_REPO_PATH, selected_deck)
    deck_file_path = os.path.join(deck_path, "deck.txt")
    triggered_id = ctx.triggered_id
    msg = "Deck loaded."
    
    # Route interactions
    if triggered_id == 'branch-selector':
        if selected_branch == '_create_new_':
            return dash.no_update
        msg = git_manager.checkout_branch(deck_path, selected_branch)
    elif triggered_id == 'create-branch-btn' and new_branch_name:
        msg = f"Created and switched to branch '{new_branch_name}'."
    elif triggered_id == 'merge-btn' and merge_branch_name:
        success, msg = git_manager.merge_branch(deck_path, merge_branch_name)
    elif triggered_id == 'commit-btn':
        msg = git_manager.commit_changes(deck_path, commit_msg or "Update deck via Dashboard")
    elif triggered_id == 'bulk-add-submit-btn' and bulk_add_text:
        success, msg = deck_manager.bulk_add_cards(deck_file_path, bulk_add_text)
    elif triggered_id == 'add-card-btn' and add_card_name:
        # Route single card adds through the smart bulk function
        success, msg = deck_manager.bulk_add_cards(deck_file_path, f"1 {add_card_name}")
    elif triggered_id == 'menu-remove-all':
        success, msg = deck_manager.remove_all_cards(deck_file_path)
    elif triggered_id == 'submit-cmdr-btn':
        success, msg = deck_manager.change_commander(deck_file_path, change_cmdr_name)
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'delete-card-btn':
        card_to_delete = triggered_id.get('index')
        success, msg = deck_manager.remove_card_from_deck(deck_file_path, card_to_delete)
    elif triggered_id == 'sort-selector':
        msg = f"Deck sorted by {sort_by}."
        
    banner_class = "status-banner status-warning" if ("Warning" in msg or "Error" in msg or "Not" in msg or "Failed" in msg or "conflict" in msg) else "status-banner status-success"
    
    if not os.path.exists(deck_file_path):
        return msg, banner_class, [html.Div(f"Error: {deck_file_path} not found.")], "", "", "", "", ""
    
    grouped_cards = deck_manager.get_grouped_deck_data(deck_file_path)
    columns = layout.build_deck_columns(grouped_cards, sort_by=sort_by) 
    
    commander_src = ""
    if "Commander" in grouped_cards and grouped_cards["Commander"]:
        commander_src = grouped_cards["Commander"][0].get("image_uri", "")
            
    # Reset input fields only if they were just fired
    reset_commit = "" if triggered_id == 'commit-btn' else (commit_msg or "")
    reset_bulk = "" if triggered_id == 'bulk-add-submit-btn' else (bulk_add_text or "") 
    reset_cmdr = "" if triggered_id == 'submit-cmdr-btn' else (change_cmdr_name or "") 
    reset_add_card = "" if triggered_id == 'add-card-btn' else (add_card_name or "")
    
    return msg, banner_class, columns, commander_src, reset_commit, reset_bulk, reset_cmdr, reset_add_card

@app.callback(
    Output("bulk-add-modal", "is_open"),
    [Input("open-bulk-add-modal-btn", "n_clicks"),
     Input("close-bulk-add-modal-btn", "n_clicks"),
     Input("bulk-add-submit-btn", "n_clicks")],
    [State("bulk-add-modal", "is_open")],
)
def toggle_bulk_add_modal(open_clicks, close_clicks, submit_clicks, is_open):
    ctx_id = ctx.triggered_id
    if ctx_id in ["open-bulk-add-modal-btn", "close-bulk-add-modal-btn"]:
        return not is_open
    if ctx_id == "bulk-add-submit-btn" and submit_clicks:
        return False
    return is_open

@app.callback(
    Output("git-modal", "is_open"),
    [Input("open-git-modal-btn", "n_clicks"), 
     Input("close-git-modal-btn", "n_clicks")],
    [State("git-modal", "is_open")],
)
def toggle_git_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open

@app.callback(
    Output('new-deck-autocomplete-list', 'children'),
    Input('new-deck-commander-input', 'value')
)
def update_new_deck_autocomplete(search_term):
    if not search_term or len(search_term) < 3: return no_update
    suggestions = deck_manager.get_card_autocomplete(search_term)
    return [html.Option(value=name) for name in suggestions]

@app.callback(
    Output('set-cmdr-autocomplete-list', 'children'),
    Input('set-cmdr-input', 'value')
)
def update_set_cmdr_autocomplete(search_term):
    if not search_term or len(search_term) < 3: return dash.no_update
    suggestions = deck_manager.get_card_autocomplete(search_term)
    return [html.Option(value=name) for name in suggestions]

@app.callback(
    Output('add-card-autocomplete-list', 'children'),
    Input('add-card-input', 'value')
)
def update_add_card_autocomplete(search_term):
    if not search_term or len(search_term) < 3: return dash.no_update
    suggestions = deck_manager.get_card_autocomplete(search_term)
    return [html.Option(value=name) for name in suggestions]

@app.callback(
    [Output('deck-selector', 'options'),
     Output('deck-selector', 'value'),
     Output('git-status-message', 'children', allow_duplicate=True),
     Output('git-status-message', 'className', allow_duplicate=True)],
    Input('create-deck-submit-btn', 'n_clicks'),
    [State('new-deck-name-input', 'value'),
     State('new-deck-commander-input', 'value')],
    prevent_initial_call=True
)
def create_deck_callback(n_clicks, deck_name, commander_name):
    if not n_clicks:
        return no_update, no_update, no_update, no_update
    
    if not deck_name:
        return no_update, no_update, "Deck Name is required.", "status-banner status-warning"
    
    if not commander_name:
        return no_update, no_update, "Please provide a commander.", "status-banner status-warning"
        
    success, msg = deck_manager.create_new_deck(deck_name, commander_name)
    
    available_decks = deck_manager.get_available_decks()
    options = []
    for d in available_decks:
        label = d
        meta_path = os.path.join(DECK_REPO_PATH, d, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    label = json.load(f).get("name", d)
            except Exception:
                pass
        options.append({'label': label, 'value': d})
    
    banner_class = "status-banner status-warning" if not success else "status-banner status-success"
    selected_val = deck_manager._slugify(deck_name) if success else (available_decks[0] if available_decks else None)
    
    return options, selected_val, msg, banner_class

@app.callback(
    Output("new-deck-modal", "is_open"),
    [Input("open-new-deck-modal-btn", "n_clicks"),
     Input("close-new-deck-modal-btn", "n_clicks"),
     Input("create-deck-submit-btn", "n_clicks")],
    [State("new-deck-modal", "is_open")],
)
def toggle_new_deck_modal(open_clicks, close_clicks, create_clicks, is_open):
    ctx_id = ctx.triggered_id
    if ctx_id in ["open-new-deck-modal-btn", "close-new-deck-modal-btn"]:
        return not is_open
    if ctx_id == "create-deck-submit-btn" and create_clicks:
        return False
    return is_open

@app.callback(
    Output("set-cmdr-modal", "is_open"),
    [Input("open-set-cmdr-modal-btn", "n_clicks"),
     Input("close-set-cmdr-modal-btn", "n_clicks"),
     Input("submit-cmdr-btn", "n_clicks")],
    [State("set-cmdr-modal", "is_open")],
)
def toggle_set_cmdr_modal(open_clicks, close_clicks, submit_clicks, is_open):
    ctx_id = ctx.triggered_id
    if ctx_id in ["open-set-cmdr-modal-btn", "close-set-cmdr-modal-btn"]:
        return not is_open
    if ctx_id == "submit-cmdr-btn" and submit_clicks:
        return False
    return is_open

if __name__ == '__main__':
    app.run(debug=True)

