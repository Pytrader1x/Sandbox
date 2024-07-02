import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import uuid

# Initialize session state
if 'trade_groups' not in st.session_state:
    st.session_state.trade_groups = []
if 'current_market_price' not in st.session_state:
    st.session_state.current_market_price = 0.6650
if 'strategy_notes' not in st.session_state:
    st.session_state.strategy_notes = ''
if 'default_tp_pips' not in st.session_state:
    st.session_state.default_tp_pips = 20
if 'default_sl_pips' not in st.session_state:
    st.session_state.default_sl_pips = 20

# Constants
CURRENCY_PAIRS = ['AUDUSD', 'EURUSD', 'GBPUSD', 'USDCAD', 'USDJPY', 'USDCHF', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY']
POSITION_TYPES = ['Long', 'Short']

# Helper functions
def calculate_pnl(entry_price, exit_price, trade_type, size):
    direction = 1 if trade_type == 'Long' else -1
    price_diff = (exit_price - entry_price) * direction
    pips = price_diff * 10000
    return pips * 100 * size  # $100 per million per pip

def calculate_weighted_average(trades):
    total_size = sum(float(trade['size']) * (1 if trade['type'] == 'Long' else -1) for trade in trades if trade['result'] == 'Open')
    weighted_sum = sum(float(trade['entryPrice']) * float(trade['size']) * (1 if trade['type'] == 'Long' else -1) for trade in trades if trade['result'] == 'Open')
    return weighted_sum / total_size if total_size != 0 else 0

def calculate_tp_sl(entry_price, trade_type, tp_pips, sl_pips):
    if trade_type == 'Long':
        tp = entry_price + (tp_pips * 0.0001)
        sl = entry_price - (sl_pips * 0.0001)
    else:
        tp = entry_price - (tp_pips * 0.0001)
        sl = entry_price + (sl_pips * 0.0001)
    return round(tp, 5), round(sl, 5)

def update_group_stats(group, current_price):
    open_trades = [trade for trade in group['trades'] if trade['result'] == 'Open']
    closed_trades = [trade for trade in group['trades'] if trade['result'] == 'Closed']
    
    group['totalSize'] = sum(float(trade['size']) * (1 if trade['type'] == 'Long' else -1) for trade in open_trades)
    group['weightedAvgPrice'] = calculate_weighted_average(open_trades)
    group['netDirection'] = 'Long' if group['totalSize'] > 0 else 'Short' if group['totalSize'] < 0 else 'Flat'
    
    # Calculate realized PNL
    group['realizedPnL'] = sum(calculate_pnl(trade['entryPrice'], trade['closePrice'], trade['type'], trade['size']) for trade in closed_trades)
    
    # Calculate unrealized PNL
    group['unrealizedPnL'] = sum(calculate_pnl(trade['entryPrice'], current_price, trade['type'], trade['size']) for trade in open_trades)
    
    # Calculate total PNL
    group['totalPnL'] = group['realizedPnL'] + group['unrealizedPnL']
    
    # Calculate average entry and exit prices
    long_entries = [trade for trade in group['trades'] if trade['type'] == 'Long']
    short_entries = [trade for trade in group['trades'] if trade['type'] == 'Short']
    
    group['avgEntryPrice'] = calculate_weighted_average(long_entries) if long_entries else 0
    group['avgClosePrice'] = calculate_weighted_average(short_entries) if short_entries else 0
    group['totalSizeEntered'] = sum(float(trade['size']) for trade in group['trades'])
    
    if group['totalSize'] == 0:
        group['status'] = 'Closed'
    else:
        group['status'] = 'Open'

    # Set initial direction based on first trade
    group['initialDirection'] = group['trades'][0]['type'] if group['trades'] else 'Flat'

# Styling
st.set_page_config(layout="wide")
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .trade-group-container {
        background-color: #2D2D2D;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .trade-container {
        background-color: #3D3D3D;
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }
    .styled-button {
        padding: 5px 10px;
        border-radius: 5px;
        border: none;
        color: white;
        cursor: pointer;
    }
    .edit-button { background-color: #4CAF50; }
    .delete-button { background-color: #f44336; }
    .add-button { background-color: #008CBA; }
    .dataframe {
        font-size: 12px;
    }
    .dataframe th {
        background-color: #4CAF50;
        color: white;
    }
    .dataframe td {
        text-align: right;
    }
    .profit { color: #4CAF50; }
    .loss { color: #f44336; }
</style>
""", unsafe_allow_html=True)

# Main dashboard
st.title('Perfected Trading Performance Dashboard')

# Strategy notes (collapsible)
with st.expander("Strategy Notes", expanded=False):
    st.session_state.strategy_notes = st.text_area("", st.session_state.strategy_notes, height=150)

# Current market price input
st.session_state.current_market_price = st.number_input("Current Market Price", value=st.session_state.current_market_price, format="%.5f", step=0.00001)

# Default TP/SL settings
col1, col2 = st.columns(2)
with col1:
    st.session_state.default_tp_pips = st.number_input("Default TP (pips)", value=st.session_state.default_tp_pips, min_value=1)
with col2:
    st.session_state.default_sl_pips = st.number_input("Default SL (pips)", value=st.session_state.default_sl_pips, min_value=1)

# Calculate statistics
current_price = st.session_state.current_market_price
for group in st.session_state.trade_groups:
    update_group_stats(group, current_price)

total_pnl = sum(group['totalPnL'] for group in st.session_state.trade_groups)
realized_pnl = sum(group['realizedPnL'] for group in st.session_state.trade_groups)
unrealized_pnl = sum(group['unrealizedPnL'] for group in st.session_state.trade_groups)

# Display statistics
col1, col2, col3 = st.columns(3)
col1.metric("Total PNL", f"${total_pnl:.2f}")
col2.metric("Realized PNL", f"${realized_pnl:.2f}")
col3.metric("Unrealized PNL", f"${unrealized_pnl:.2f}")

# New trade group form
with st.expander("Add New Trade Group", expanded=False):
    st.subheader("Add New Trade Group")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_type = st.selectbox("Type", POSITION_TYPES)
        new_pair = st.selectbox("Pair", CURRENCY_PAIRS)
    with col2:
        new_entry_price = st.number_input("Entry Price", value=current_price, format="%.5f", step=0.00001)
        new_size = st.number_input("Size (M)", value=1.0, step=0.1)
    with col3:
        new_tp, new_sl = calculate_tp_sl(new_entry_price, new_type, st.session_state.default_tp_pips, st.session_state.default_sl_pips)
        new_tp = st.number_input("TP Level", value=new_tp, format="%.5f", step=0.00001)
        new_sl = st.number_input("SL Level", value=new_sl, format="%.5f", step=0.00001)
    with col4:
        new_date = st.date_input("Date")
        new_time = st.time_input("Time")

    if st.button("Add New Trade Group"):
        if new_entry_price and new_size:
            new_trade = {
                'id': str(uuid.uuid4()),
                'date': f"{new_date} {new_time}",
                'type': new_type,
                'pair': new_pair,
                'entryPrice': new_entry_price,
                'size': new_size,
                'tpLevel': new_tp,
                'slLevel': new_sl,
                'result': 'Open',
                'comment': ''
            }
            new_group = {
                'id': str(uuid.uuid4()),
                'trades': [new_trade],
                'weightedAvgPrice': new_entry_price,
                'totalSize': new_size,
                'tpLevel': new_tp,
                'slLevel': new_sl,
                'netDirection': new_type,
                'initialDirection': new_type,
                'status': 'Open',
                'realizedPnL': 0,
                'unrealizedPnL': 0,
                'totalPnL': 0,
                'avgEntryPrice': new_entry_price,
                'avgClosePrice': 0,
                'totalSizeEntered': new_size
            }
            st.session_state.trade_groups.insert(0, new_group)  # Insert at the beginning of the list
            update_group_stats(new_group, current_price)
            st.success("New trade group added successfully!")
            st.experimental_rerun()
        else:
            st.warning("Please enter both Entry Price and Size.")

# Display trade groups
st.subheader("Trade Groups")
for group_index, group in enumerate(st.session_state.trade_groups):
    update_group_stats(group, current_price)
    
    # Construct the label string
    direction_symbol = "🟢" if group['initialDirection'] == 'Long' else "🔴" if group['initialDirection'] == 'Short' else "⚪"
    pnl_color = "profit" if group['totalPnL'] >= 0 else "loss"
    if group['status'] == 'Closed':
        label = f"{direction_symbol} Group {group_index + 1}: {group['trades'][0]['pair']} - Closed | Total PnL: ${group['totalPnL']:.2f} | Avg Entry: {group['avgEntryPrice']:.5f} | Avg Close: {group['avgClosePrice']:.5f} | Total Size: {group['totalSizeEntered']:.2f}M"
    else:
        label = f"{direction_symbol} Group {group_index + 1}: {group['trades'][0]['pair']} - {abs(group['totalSize']):.2f}M {group['netDirection']} @ {group['weightedAvgPrice']:.5f} | PnL: ${group['totalPnL']:.2f}"

    # Color code the group based on its direction
    group_color = '#4CAF50' if group['netDirection'] == 'Long' else '#f44336' if group['netDirection'] == 'Short' else '#808080'
    
    with st.expander(label, expanded=True):
        st.markdown(f"<div class='trade-group-container' style='border-left: 5px solid {group_color};'>", unsafe_allow_html=True)
        
        # Display group summary
        st.markdown(f"""
            <div style='background-color: #2D2D2D; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                <h3 style='margin: 0;'>Group Summary</h3>
                <p><strong>Status:</strong> {group['status']}</p>
                <p><strong>Total Size:</strong> {abs(group['totalSize']):.2f}M {group['netDirection']}</p>
                <p><strong>Weighted Avg Price:</strong> {group['weightedAvgPrice']:.5f}</p>
                <p><strong>Realized PnL:</strong> <span style='color: {"#4CAF50" if group["realizedPnL"] >= 0 else "#f44336"};'>${group['realizedPnL']:.2f}</span></p>
                {"<p><strong>Unrealized PnL:</strong> <span style='color: " + ("#4CAF50" if group["unrealizedPnL"] >= 0 else "#f44336") + f";'>${group['unrealizedPnL']:.2f}</span></p>" if group['status'] == 'Open' else ''}
                <p><strong>Total PnL:</strong> <span style='color: {"#4CAF50" if group["totalPnL"] >= 0 else "#f44336"};'>${group['totalPnL']:.2f}</span></p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display individual trades
        for trade_index, trade in enumerate(group['trades']):
            with st.container():
                st.markdown(f"<div class='trade-container'>", unsafe_allow_html=True)
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2, 2, 2])
                col1.write(f"**Date:** {trade['date']}")
                col2.write(f"**Type:** {trade['type']}")
                col3.write(f"**Entry Price:** {trade['entryPrice']:.5f}")
                col4.write(f"**Size:** {trade['size']:.2f}M")
                col5.write(f"**Result:** {trade['result']}")
                col6.write(f"**Close Price:** {trade.get('closePrice', '-')}")
                
                if trade['type'] != group['initialDirection']:
                    # Realized PNL for opposite direction trades
                    trade_pnl = calculate_pnl(group['weightedAvgPrice'], trade['entryPrice'], group['initialDirection'], trade['size'])
                    pnl_type = "Realized PNL"
                else:
                    # Unrealized PNL for same direction trades
                    trade_pnl = calculate_pnl(trade
                    else:
                    # Unrealized PNL for same direction trades
                    trade_pnl = calculate_pnl(trade['entryPrice'], current_price, trade['type'], trade['size'])
                    pnl_type = "Unrealized PNL"
                
                pnl_color = "#4CAF50" if trade_pnl >= 0 else "#f44336"
                col7.markdown(f"**{pnl_type}:** <span style='color: {pnl_color};'>${trade_pnl:.2f}</span>", unsafe_allow_html=True)
                
                # Add modify and delete buttons for both open and closed groups
                if st.button(f"Modify", key=f"modify_{trade['id']}"):
                    st.session_state[f"modify_trade_{trade['id']}"] = True
                if st.button(f"Delete", key=f"delete_{trade['id']}"):
                    group['trades'].remove(trade)
                    update_group_stats(group, current_price)
                    st.experimental_rerun()
                
                # Modify trade form
                if st.session_state.get(f"modify_trade_{trade['id']}", False):
                    with st.form(f"modify_trade_form_{trade['id']}"):
                        st.subheader(f"Modify Trade")
                        mod_entry_price = st.number_input("New Entry Price", value=float(trade['entryPrice']), format="%.5f", step=0.00001)
                        mod_size = st.number_input("New Size (M)", value=float(trade['size']), step=0.1)
                        if trade['result'] == 'Closed':
                            mod_close_price = st.number_input("New Close Price", value=float(trade.get('closePrice', trade['entryPrice'])), format="%.5f", step=0.00001)
                        if st.form_submit_button("Save Changes"):
                            trade['entryPrice'] = mod_entry_price
                            trade['size'] = mod_size
                            if trade['result'] == 'Closed':
                                trade['closePrice'] = mod_close_price
                            update_group_stats(group, current_price)
                            st.session_state[f"modify_trade_{trade['id']}"] = False
                            st.experimental_rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Add sub-trade form within group
        if group['status'] == 'Open':
            with st.form(f"add_sub_trade_form_{group_index}"):
                st.subheader("Add Sub-Trade to Group")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    sub_type = st.selectbox(f"Type", POSITION_TYPES, key=f"type_{group_index}")
                    sub_pair = st.selectbox(f"Pair", CURRENCY_PAIRS, key=f"pair_{group_index}")
                with col2:
                    sub_entry_price = st.number_input(f"Entry Price", value=current_price, format="%.5f", step=0.00001, key=f"entry_{group_index}")
                    sub_size = st.number_input(f"Size (M)", value=1.0, step=0.1, key=f"size_{group_index}")
                with col3:
                    sub_tp, sub_sl = calculate_tp_sl(sub_entry_price, sub_type, st.session_state.default_tp_pips, st.session_state.default_sl_pips)
                    sub_tp = st.number_input(f"TP Level", value=sub_tp, format="%.5f", step=0.00001, key=f"tp_{group_index}")
                    sub_sl = st.number_input(f"SL Level", value=sub_sl, format="%.5f", step=0.00001, key=f"sl_{group_index}")
                with col4:
                    sub_date = st.date_input(f"Date", key=f"date_{group_index}")
                    sub_time = st.time_input(f"Time", key=f"time_{group_index}")

                if st.form_submit_button(f"Add Sub-Trade to Group {group_index + 1}"):
                    if sub_entry_price and sub_size:
                        sub_trade = {
                            'id': str(uuid.uuid4()),
                            'date': f"{sub_date} {sub_time}",
                            'type': sub_type,
                            'pair': sub_pair,
                            'entryPrice': sub_entry_price,
                            'size': sub_size,
                            'tpLevel': sub_tp,
                            'slLevel': sub_sl,
                            'result': 'Open',
                            'comment': ''
                        }
                        group['trades'].append(sub_trade)
                        update_group_stats(group, current_price)
                        st.success("Sub-trade added successfully!")
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter both Entry Price and Size.")

        # Close entire trade group button
        if group['status'] == 'Open':
            if st.button(f"Close Entire Group {group_index + 1}", key=f"close_{group_index}"):
                close_price = st.number_input(f"Close Price for Group {group_index + 1}", value=current_price, format="%.5f", step=0.00001, key=f"group_close_price_{group_index}")
                if st.button(f"Confirm Close Group {group_index + 1}", key=f"confirm_close_{group_index}"):
                    for trade in group['trades']:
                        if trade['result'] == 'Open':
                            trade['result'] = 'Closed'
                            trade['closePrice'] = close_price
                    update_group_stats(group, current_price)
                    st.success(f"Group {group_index + 1} closed successfully! Total Realized PnL: ${group['realizedPnL']:.2f}")
                    st.experimental_rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# Export and import functionality
with st.expander("Export/Import Trade Data", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        trade_data = {
            'trade_groups': st.session_state.trade_groups,
            'strategy_notes': st.session_state.strategy_notes,
            'default_tp_pips': st.session_state.default_tp_pips,
            'default_sl_pips': st.session_state.default_sl_pips
        }
        trade_data_json = json.dumps(trade_data, indent=2)
        st.download_button(label="Export Trades", data=trade_data_json, file_name='trade_data.json', mime='application/json')
    with col2:
        uploaded_file = st.file_uploader("Import Trade Data", type=['json'])
        if uploaded_file is not None:
            trade_data = json.loads(uploaded_file.read())
            st.session_state.trade_groups = trade_data['trade_groups']
            st.session_state.strategy_notes = trade_data['strategy_notes']
            st.session_state.default_tp_pips = trade_data['default_tp_pips']
            st.session_state.default_sl_pips = trade_data['default_sl_pips']
            st.success("Trade data imported successfully!")
            st.experimental_rerun()

# Display summary table
st.subheader("Trade Summary")
summary_data = []
for group_index, group in enumerate(st.session_state.trade_groups):
    group_id = f"Group {group_index + 1}"
    for trade in group['trades']:
        if trade['type'] != group['initialDirection']:
            trade_pnl = calculate_pnl(group['weightedAvgPrice'], trade['entryPrice'], group['initialDirection'], trade['size'])
            pnl_type = "Realized PNL"
        else:
            trade_pnl = calculate_pnl(trade['entryPrice'], current_price, trade['type'], trade['size'])
            pnl_type = "Unrealized PNL"
        
        summary_data.append({
            'Group': group_id,
            'Date': trade['date'],
            'Pair': trade['pair'],
            'Type': trade['type'],
            'Entry Price': float(trade['entryPrice']),
            'Size (M)': float(trade['size']),
            'Result': trade['result'],
            'Close Price': trade.get('closePrice', '-'),
            'PNL Type': pnl_type,
            'PNL': trade_pnl,
            'Comment': trade['comment']
        })

summary_df = pd.DataFrame(summary_data)

# Apply color coding to PNL column
def color_pnl(val):
    if isinstance(val, str) or pd.isna(val):
        return ''
    color = '#4CAF50' if float(val) >= 0 else '#f44336'
    return f'color: {color}'

if not summary_df.empty:
    st.dataframe(summary_df.style
                 .format({
                     'Entry Price': '{:.5f}',
                     'Size (M)': '{:.2f}',
                     'Close Price': lambda x: '{:.5f}'.format(x) if isinstance(x, (int, float)) else x,
                     'PNL': '${:.2f}'
                 })
                 .applymap(color_pnl, subset=['PNL'])
                 .set_properties(**{'text-align': 'right'})
                 .set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}])
    )
else:
    st.write("No trades to display.")