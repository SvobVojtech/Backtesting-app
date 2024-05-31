import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from itertools import combinations
import seaborn as sns


# Funkce pro načtení existujícího CSV nebo vytvoření nového
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        columns = ['Pair', 'Side', 'Trade Time', '1D Trend', '1H Trend', '15m Trend',
                   'HTF zone Mitigation', 'Liquidation', 'IFC', 'ChoCh/Flip', 'PRO TREND/Orderflow',
                   '50% mitigation', 'V-shape reaction', 'Liquidity to target', 'Not from opposite zone',
                   'Corrective pullback', 'Combined liquidation', 'Result', 'Balance', 'Notes']
        return pd.DataFrame(columns=columns)


# Funkce pro uložení dat do CSV
def save_data(df, file_path):
    df.to_csv(file_path, index=False)


# Cesta k souboru s daty
data_file = 'trades.csv'

# Načtení dat
data = load_data(data_file)

st.title("Backtesting Application")

# Formulář pro zadání obchodu
pair = st.selectbox('Pair', ['EUR/USD', 'GBP/USD'])
side = st.selectbox('Trade Side', ['buy', 'sell'])
trade_time = st.time_input('Trade Time')
trend_1d = st.selectbox('1D Trend', ['Bullish', 'Bearish'])
trend_1h = st.selectbox('1H Trend', ['Bullish', 'Bearish'])
trend_15m = st.selectbox('15m Trend', ['Bullish', 'Bearish'])

criteria = {
    'HTF zone Mitigation': st.checkbox('HTF zone Mitigation'),
    'Liquidation': st.checkbox('Liquidation'),
    'IFC': st.checkbox('IFC'),
    'ChoCh/Flip': st.checkbox('ChoCh/Flip'),
    'PRO TREND/Orderflow': st.checkbox('PRO TREND/Orderflow'),
    '50% mitigation': st.checkbox('50% mitigation'),
    'V-shape reaction': st.checkbox('V-shape reaction'),
    'Liquidity to target': st.checkbox('Liquidity to target'),
    'Not from opposite zone': st.checkbox('Not from opposite zone'),
    'Corrective pullback': st.checkbox('Corrective pullback'),
    'Combined liquidation': st.checkbox('Combined liquidation'),
}

result = st.number_input('Result ($)', value=0)
notes = st.text_area('Notes and Improvement Opportunities')

if st.button('Add Trade'):
    new_trade = {
        'Pair': pair,
        'Side': side,
        'Trade Time': trade_time,
        '1D Trend': trend_1d,
        '1H Trend': trend_1h,
        '15m Trend': trend_15m,
        'Result': result,
        'Balance': data['Balance'].iloc[-1] + result if not data.empty else 10000 + result,
        'Notes': notes
    }
    for key in criteria:
        new_trade[key] = criteria[key]

    data = pd.concat([data, pd.DataFrame([new_trade])], ignore_index=True)
    save_data(data, data_file)
    st.success('Trade has been added!')

st.header('Trade History')


# Zvýraznění výher a proher
def highlight_results(val):
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'


st.dataframe(data.style.applymap(highlight_results, subset=['Result']))

# Zobrazení aktuálního zůstatku
current_balance = data['Balance'].iloc[-1] if not data.empty else 10000
balance_color = 'green' if current_balance >= 10000 else 'red'
st.markdown(f"### Current Balance: <span style='color:{balance_color}'>{current_balance:.2f}$</span>",
            unsafe_allow_html=True)

# Výpočet a zobrazení statistik
if not data.empty:
    total_trades = len(data)
    win_trades = len(data[data['Result'] > 0])
    loss_trades = total_trades - win_trades
    win_rate = (win_trades / total_trades) * 100
    average_rr = data['Result'].mean()

    st.header('Statistics')
    st.write(f'Total Trades: {total_trades}')
    st.write(f'Win Trades: {win_trades}')
    st.write(f'Loss Trades: {loss_trades}')
    st.write(f'Win Rate: {win_rate:.2f}%')
    st.write(f'Average R:R: {average_rr:.2f}')

    # Základní kritéria
    basic_criteria = ['HTF zone Mitigation', 'ChoCh/Flip', 'IFC', 'PRO TREND/Orderflow', 'Liquidation']
    other_criteria = ['50% mitigation', 'V-shape reaction', 'Liquidity to target', 'Not from opposite zone',
                      'Corrective pullback', 'Combined liquidation']

    # Vygenerování všech kombinací ostatních kritérií se 4 dalšími kritérii
    valid_combinations = list(combinations(other_criteria, 4))

    # Funkce pro vytvoření jedinečného názvu pro každou platnou kombinaci
    def create_combination_name(index):
        return f"Group {index+1}"

    # Výpočet winrate pro každou kombinaci
    combination_results = []
    for idx, comb in enumerate(valid_combinations):
        criteria_subset = basic_criteria + list(comb)
        subset_data = data
        for crit in criteria_subset:
            subset_data = subset_data[subset_data[crit] == True]
        if not subset_data.empty:
            winrate = (subset_data['Result'] > 0).mean() * 100
            combination_name = create_combination_name(idx)
            combination_results.append((combination_name, criteria_subset, winrate))

    def find_group_with_highest_winrate(groups):
        max_winrate = 0
        max_group = None
        for group in groups:
            if group[2] > max_winrate:
                max_winrate = group[2]
                max_group = group
        return max_group

    max_winrate_group = find_group_with_highest_winrate(combination_results)

    if max_winrate_group:
        st.write(f"The group with the highest winrate is {max_winrate_group[0]} "
                 f"with a winrate of {max_winrate_group[2]}%.")
    else:
        st.warning("No trades have been made yet.")

    # Zobrazení vysokých winrate kombinací
    high_winrate_combinations = [comb for comb in combination_results if comb[2] >= 60]
    low_winrate_combinations = [comb for comb in combination_results if comb[2] <= 20]

    # Funkce pro vykreslení grafů winrate kombinací
    def plot_winrate_combinations(combinations, title):
        fig, ax = plt.subplots()
        comb_labels = [comb[0] for comb in combinations]
        comb_winrates = [comb[2] for comb in combinations]
        ax.barh(comb_labels, comb_winrates,
                color=['green' if winrate >= 60 else 'red' for winrate in comb_winrates])
        plt.title(title)
        plt.xlabel('Winrate (%)')
        st.pyplot(fig)

    # Zobrazení kritérií pro skupiny s vysokým winrate
    st.header('Combinations with Winrate 60%+')
    plot_winrate_combinations(high_winrate_combinations, 'Combinations with Winrate 60%+')

    st.write("### Criteria for High Winrate Combinations")
    for comb in high_winrate_combinations:
        st.write(f"**{comb[0]}**: {', '.join(comb[1])}")

    # Zobrazení kritérií pro skupiny s nízkým winrate
    st.header('Combinations with Winrate 20%-')
    plot_winrate_combinations(low_winrate_combinations, 'Combinations with Winrate 20%-')

    st.write("### Criteria for Low Winrate Combinations")
    for comb in low_winrate_combinations:
        st.write(f"**{comb[0]}**: {', '.join(comb[1])}")

    # Graf winrate podle dne v týdnu
    data['Trade Time'] = pd.to_datetime(data['Trade Time'], format='%H:%M:%S').dt.time
    data['Day of Week'] = pd.to_datetime(data['Trade Time'], format='%H:%M:%S').dt.day_name()

    winrate_by_day = data.groupby('Day of Week')['Result'].apply(lambda x: (x > 0).mean() * 100)
    trade_count_by_day = data['Day of Week'].value_counts().sort_index()

    fig, ax1 = plt.subplots(figsize=(10, 6))  # Upravíme velikost grafu
    color = 'tab:blue'
    ax1.set_xlabel('Day of Week')
    ax1.set_ylabel('Trade Count', color=color)
    trade_count_by_day.plot(kind='bar', ax=ax1, color=color, width=0.4)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(0, trade_count_by_day.max() + 5)  # Nastavíme rozsah osy y

    # Přidáme winrate pro každý den
    for i, v in enumerate(trade_count_by_day):
        ax1.text(i, v + 1, f'{v:.0f}', ha='center', va='bottom', color='black')

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Winrate (%)', color=color)
    winrate_by_day.plot(kind='line', ax=ax2, color=color, marker='o', linestyle='-', linewidth=2)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 100)  # Nastavíme rozsah osy y

    fig.tight_layout()
    plt.title('Trade Count and Winrate by Day of Week')
    plt.xticks(rotation=45)  # Natočíme popisky osy x pro lepší čitelnost
    st.pyplot(fig)


else:
    st.warning('No trades have been made yet.')


