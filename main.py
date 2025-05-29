import pandas as pd
import matplotlib.pyplot as plt


# Betölti a CSV adatokat pandas DataFrame-be.
def load_race_data(filename):
    return pd.read_csv(filename)


# Kiszámolja az átlagos gumidegradációt compoundonként.
def calculate_compound_degradation(data):
    compound_degradation = {}
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    data.columns = [col.strip() for col in data.columns]
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    for compound in data[compound_column].unique():
        compound_data = data[data[compound_column] == compound].copy()
        compound_data['Average Tire Usage'] = compound_data[tire_columns].mean(axis=1)
        compound_data['Reset'] = (compound_data['Average Tire Usage'] < 5).cumsum()
        degradation_rates = []
        for _, group in compound_data.groupby('Reset'):
            if len(group) > 1:
                degradation = group['Average Tire Usage'].diff().fillna(0).mean()
                degradation_rates.append(degradation)
        avg_degradation_rate = sum(degradation_rates) / len(degradation_rates) if degradation_rates else 0
        compound_degradation[compound] = avg_degradation_rate
    return compound_degradation

#Főbb statisztikák kiírása: leggyorsabb kör, átlag, degradációk.
def enhanced_stats(data):
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    print("\n==== Race Statistics ====")
    fastest_lap = data.loc[data['Laptime'].idxmin()]
    print(f"Fastest lap (all time): Lap {fastest_lap['Lap']} - {fastest_lap['Laptime']:.3f}s on {fastest_lap[compound_column]}")
    data['Average Tire Usage'] = data[tire_columns].mean(axis=1)
    resets = (data['Average Tire Usage'] < 5).cumsum()
    current_stint = data[resets == resets.iloc[-1]]
    fastest_stint = current_stint.loc[current_stint['Laptime'].idxmin()]
    print(f"Fastest lap (current stint): Lap {fastest_stint['Lap']} - {fastest_stint['Laptime']:.3f}s")
    avg_stint_laptime = current_stint['Laptime'].mean()
    print(f"Average lap time (current stint): {avg_stint_laptime:.3f}s")
    last_lap = data.iloc[-1]
    delta_avg = last_lap['Laptime'] - avg_stint_laptime
    delta_fastest = last_lap['Laptime'] - fastest_stint['Laptime']
    delta_fastest_all = last_lap['Laptime'] - fastest_lap['Laptime']
    print(f"Last lap: Lap {last_lap['Lap']} - {last_lap['Laptime']:.3f}s")
    print(f"Delta to avg (current stint): {delta_avg:+.3f}s")
    print(f"Delta to fastest (current stint): {delta_fastest:+.3f}s")
    print(f"Delta to fastest (all time): {delta_fastest_all:+.3f}s")
    compound_degradation = calculate_compound_degradation(data)
    print("\nAverage degradation per compound:")
    for compound, rate in compound_degradation.items():
        print(f"  {compound}: {rate:.2f}% per lap")
    print("==========================\n")


# Becsli, mikor lesz szükséges a következő kerékcsere a kopás alapján.
def find_planned_pitstop(data, wear_threshold):
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    data['Average Tire Usage'] = data[tire_columns].mean(axis=1)
    resets = (data['Average Tire Usage'] < 5).cumsum()
    last_reset = resets.iloc[-1]
    current_stint = data[resets == last_reset]
    if len(current_stint) < 2:
        print("Not enough data for planned pitstop calculation.")
        return None
    avg_degradation_per_lap = current_stint['Average Tire Usage'].diff().mean()
    current_avg_wear = current_stint['Average Tire Usage'].iloc[-1]
    laps_needed = (wear_threshold - current_avg_wear) / avg_degradation_per_lap if avg_degradation_per_lap > 0 else float('inf')
    planned_pit_lap = data['Lap'].iloc[-1] + laps_needed if laps_needed != float('inf') else None
    if planned_pit_lap and planned_pit_lap > data['Lap'].iloc[-1]:
        print(f"Planned pitstop around lap {planned_pit_lap:.0f}")
    else:
        print("No planned pitstop within data range.")
    return planned_pit_lap


# Javaslat azonnali kerékcserére az utolsó néhány kör kopása alapján.
def find_current_pit_advice(data, wear_threshold, recent_laps):
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    if len(data) < recent_laps:
        print("Not enough data for current pit advice.")
        return
    recent_data = data.tail(recent_laps)
    avg_recent_wear = recent_data[tire_columns].mean().mean()
    if avg_recent_wear >= wear_threshold:
        print(f"Immediate pitstop recommended! Recent average wear: {avg_recent_wear:.2f}%")
    else:
        print(f"No immediate pitstop needed. Recent average wear: {avg_recent_wear:.2f}%")


# Stintváltások összegzése: compound vagy kopás reset alapján.
def summarize_stints(data):
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    data['Average Tire Usage'] = data[tire_columns].mean(axis=1).reset_index(drop=True)
    stint_indices = [0]
    for i in range(1, len(data)):
        prev_wear = data['Average Tire Usage'].iloc[i-1]
        curr_wear = data['Average Tire Usage'].iloc[i]
        prev_comp = data[compound_column].iloc[i-1]
        curr_comp = data[compound_column].iloc[i]
        if curr_wear < prev_wear or curr_comp != prev_comp:
            stint_indices.append(i)
    stint_indices.append(len(data))
    print("\nStint summaries:")
    for s in range(len(stint_indices)-1):
        start_idx = stint_indices[s]
        end_idx = stint_indices[s+1]-1
        first_lap = int(data['Lap'].iloc[start_idx])
        last_lap = int(data['Lap'].iloc[end_idx])
        compound = data[compound_column].iloc[start_idx]
        num_laps = last_lap - first_lap + 1
        print(f"  Stint {s+1}: {first_lap}-{last_lap} ({num_laps} laps) on {compound}")


# Versenystratégia ajánlása a degradáció és paraméterek alapján.
def suggest_race_strategy(data, race_length_laps, required_pitstops, wear_threshold, min_compound_changes):
    degradation = calculate_compound_degradation(data)
    if not degradation:
        print("Not enough data for race strategy.")
        return
    stint_lengths = {}
    for compound, avg_deg in degradation.items():
        if avg_deg > 0:
            stint_length = int(wear_threshold / avg_deg)
            stint_lengths[compound] = stint_length
        else:
            stint_lengths[compound] = race_length_laps
    preferred_order = ['Hard', 'Medium', 'Soft']
    compounds = [c for c in preferred_order if c in stint_lengths]
    if not compounds:
        compounds = list(stint_lengths.keys())
    selected_compounds = compounds[:min(len(compounds), min_compound_changes)]
    if len(selected_compounds) < min_compound_changes:
        print(f"Warning: Only {len(selected_compounds)} compound(s) available, but {min_compound_changes} required.")
    stints_needed = required_pitstops + 1
    base_stint = race_length_laps // stints_needed
    extra = race_length_laps % stints_needed
    planned_stints = [base_stint + (1 if i < extra else 0) for i in range(stints_needed)]
    stints = []
    for i in range(min(len(selected_compounds), stints_needed)):
        comp = selected_compounds[i]
        stint_len = planned_stints[i]
        max_len = stint_lengths[comp]
        if stint_len > max_len:
            stint_len = max_len
        stints.append((comp, stint_len))
    laps_used = sum([s[1] for s in stints])
    stints_left = stints_needed - len(stints)
    last_comp = stints[-1][0] if stints else None
    for i in range(stints_left):
        available = [c for c in selected_compounds if c != last_comp]
        if not available:
            available = selected_compounds
        comp = available[0]
        stint_len = planned_stints[len(stints)]
        max_len = stint_lengths[comp]
        if stint_len > max_len:
            stint_len = max_len
        stints.append((comp, stint_len))
        last_comp = comp
    total_stint_laps = sum([s[1] for s in stints])
    if total_stint_laps < race_length_laps:
        last_comp, last_len = stints[-1]
        stints[-1] = (last_comp, last_len + (race_length_laps - total_stint_laps))
    print("Suggested race strategy:")
    lap_counter = 0
    for idx, (compound, stint) in enumerate(stints):
        pitlap = lap_counter + stint if idx < len(stints)-1 else "-"
        print(f"  Stint {idx+1}: {stint} laps on {compound}, pit at lap {pitlap}")
        lap_counter += stint
    print(f"Recommended for {race_length_laps}-lap race: {required_pitstops} pitstop(s), at least {min_compound_changes} compounds.")
    print("\nPlanned pitstops:")
    lap_counter = 0
    for compound, stint in stints[:-1]:
        lap_counter += stint
        print(f"  Lap {lap_counter} - {compound} - stint length {stint} laps")


#Versenystratégia grafikus ábrázolása (stintek, pitstopok).
def plot_race_strategy(stints):
    colors = {'Soft': 'red', 'Medium': 'orange', 'Hard': 'gray'}
    fig, ax = plt.subplots(figsize=(10, 2))
    lap = 1
    for idx, (compound, stint_len) in enumerate(stints):
        ax.barh(0, stint_len, left=lap, color=colors.get(compound, 'blue'), edgecolor='black', height=0.5, label=compound if idx == 0 or compound not in [s[0] for s in stints[:idx]] else "")
        if idx < len(stints) - 1:
            ax.axvline(lap + stint_len, color='black', linestyle='--', alpha=0.7)
        lap += stint_len
    ax.set_yticks([])
    ax.set_xlabel("Lap")
    ax.set_xlim(1, lap-1)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
    ax.set_title("Planned Race Stints and Pitstops")
    plt.tight_layout()
    plt.show()


#Szabadedzés köridők grafikus ábrázolása compound színezéssel.
def plot_practice_laptimes(data):
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    colors = {'Soft': 'red', 'Medium': 'orange', 'Hard': 'gray'}
    fig, ax = plt.subplots(figsize=(12, 4))
    for compound in data[compound_column].unique():
        laps = data[data[compound_column] == compound]['Lap']
        laptimes = data[data[compound_column] == compound]['Laptime']
        ax.plot(laps, laptimes, marker='o', linestyle='-', color=colors.get(compound, 'blue'), label=compound)
    ax.set_xlabel("Lap")
    ax.set_ylabel("Laptime (s)")
    ax.set_title("Practice Laptimes by Compound")
    ax.legend()
    plt.tight_layout()
    return fig, ax


# Stintek generálása a versenystratégiához a degradáció alapján.
def get_race_stints(data, race_length_laps, required_pitstops, wear_threshold, min_compound_changes):
    degradation = calculate_compound_degradation(data)
    if not degradation:
        print("Not enough data for race strategy.")
        return []
    stint_lengths = {}
    for compound, avg_deg in degradation.items():
        if avg_deg > 0:
            stint_length = int(wear_threshold / avg_deg)
            stint_lengths[compound] = stint_length
        else:
            stint_lengths[compound] = race_length_laps
    preferred_order = ['Hard', 'Medium', 'Soft']
    compounds = [c for c in preferred_order if c in stint_lengths]
    if not compounds:
        compounds = list(stint_lengths.keys())
    selected_compounds = compounds[:min(len(compounds), min_compound_changes)]
    if len(selected_compounds) < min_compound_changes:
        print(f"Warning: Only {len(selected_compounds)} compound(s) available, but {min_compound_changes} required.")
    stints_needed = required_pitstops + 1
    base_stint = race_length_laps // stints_needed
    extra = race_length_laps % stints_needed
    planned_stints = [base_stint + (1 if i < extra else 0) for i in range(stints_needed)]
    stints = []
    for i in range(min(len(selected_compounds), stints_needed)):
        comp = selected_compounds[i]
        stint_len = planned_stints[i]
        max_len = stint_lengths[comp]
        if stint_len > max_len:
            stint_len = max_len
        stints.append((comp, stint_len))
    laps_used = sum([s[1] for s in stints])
    stints_left = stints_needed - len(stints)
    last_comp = stints[-1][0] if stints else None
    for i in range(stints_left):
        available = [c for c in selected_compounds if c != last_comp]
        if not available:
            available = selected_compounds
        comp = available[0]
        stint_len = planned_stints[len(stints)]
        max_len = stint_lengths[comp]
        if stint_len > max_len:
            stint_len = max_len
        stints.append((comp, stint_len))
        last_comp = comp
    total_stint_laps = sum([s[1] for s in stints])
    if total_stint_laps < race_length_laps:
        last_comp, last_len = stints[-1]
        stints[-1] = (last_comp, last_len + (race_length_laps - total_stint_laps))
    return stints


# Lapozható grafikus felület: szabadedzés, kerékcserék, stratégia.
def plot_strategy_with_paging(data, stints):
    current_page = [0]
    total_pages = 3
    fig, ax = plt.subplots(figsize=(14, 5))
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    colors = {'Soft': 'red', 'Medium': 'orange', 'Hard': 'gray'}
    laps = data['Lap'].values
    laptimes = data['Laptime'].values
    compounds = data[compound_column].values
    tire_columns = ['Front left tire usage (percentage)',
                    'Front right tire usage (percentage)',
                    'Rear left tire usage (percentage)',
                    'Rear right tire usage (percentage)']
    data['Average Tire Usage'] = data[tire_columns].mean(axis=1).reset_index(drop=True)
    stint_indices = [0]
    for i in range(1, len(data)):
        prev_wear = data['Average Tire Usage'].iloc[i-1]
        curr_wear = data['Average Tire Usage'].iloc[i]
        prev_comp = compounds[i-1]
        curr_comp = compounds[i]
        if curr_wear < prev_wear or curr_comp != prev_comp:
            stint_indices.append(i)
    def show_page(page):
        ax.clear()
        if page == 0:
            for compound in np.unique(compounds):
                mask = compounds == compound
                ax.plot(laps[mask], laptimes[mask], marker='o', linestyle='-', color=colors.get(compound, 'blue'), label=compound)
            ax.set_xlabel("Lap")
            ax.set_ylabel("Laptime (s)")
            ax.set_title("Practice Laptimes by Compound")
            ax.set_xticks(laps)
            ax.set_yticks(np.round(np.linspace(np.min(laptimes), np.max(laptimes), 10), 2))
            for i, (lap, laptime) in enumerate(zip(laps, laptimes)):
                ax.text(lap, laptime+0.07, f"{laptime:.2f}", fontsize=8, ha='center', va='bottom', color='black', alpha=0.7)
            ax.legend()
        elif page == 1:
            ax.plot(laps, laptimes, marker='o', linestyle='-', color='black', alpha=0.4, label="Laptime")
            for idx in range(len(stint_indices)-1):
                start = stint_indices[idx]
                comp = compounds[start]
                color = colors.get(comp, 'blue')
                ax.axvspan(laps[start], laps[stint_indices[idx+1]-1], color=color, alpha=0.18)
                ax.axvline(laps[start], color=color, linestyle='--', lw=2, label=f"Stint start: {comp}" if idx==0 or comp != compounds[stint_indices[idx-1]] else "")
            start = stint_indices[-1]
            if start < len(laps):
                comp = compounds[start]
                color = colors.get(comp, 'blue')
                ax.axvline(laps[start], color=color, linestyle='--', lw=2)
            ax.set_xlabel("Lap")
            ax.set_ylabel("Laptime (s)")
            ax.set_title("Practice Tyre Changes / Stint Changes")
            ax.set_xticks(laps)
            ax.set_yticks(np.round(np.linspace(np.min(laptimes), np.max(laptimes), 10), 2))
            ax.legend()
        else:
            lap = 1
            for idx, (compound, stint_len) in enumerate(stints):
                ax.barh(0, stint_len, left=lap, color=colors.get(compound, 'blue'),
                        edgecolor='black', height=0.5,
                        label=compound if idx == 0 or compound not in [s[0] for s in stints[:idx]] else "")
                if idx < len(stints) - 1:
                    ax.axvline(lap + stint_len, color='black', linestyle='--', alpha=0.7)
                lap += stint_len
            ax.set_yticks([])
            ax.set_xlabel("Lap")
            ax.set_xlim(1, lap-1)
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right')
            ax.set_title("Planned Race Stints and Pitstops")
        plt.tight_layout()
        fig.canvas.draw_idle()
    def on_key(event):
        if event.key in ['right', 'pagedown']:
            if current_page[0] < total_pages - 1:
                current_page[0] += 1
                show_page(current_page[0])
        elif event.key in ['left', 'pageup']:
            if current_page[0] > 0:
                current_page[0] -= 1
                show_page(current_page[0])
    import numpy as np
    show_page(current_page[0])
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()


# Főprogram: adatbetöltés, elemzés, stratégia, vizualizáció.
def main():
    filename = 'data.csv'
    # Felhasználói paraméterek bekérése
    wear_threshold = input("Enter wear threshold (default 70): ")
    wear_threshold = int(wear_threshold) if wear_threshold.isdigit() else 70
    race_length_laps = input("How long is the race (in laps, default 54): ")
    race_length_laps = int(race_length_laps) if race_length_laps.isdigit() else 54
    required_pitstops = input("How many pitstops are required (default 2): ")
    required_pitstops = int(required_pitstops) if required_pitstops.isdigit() else 2
    min_compound_changes = input("How many different compounds are required (default 2): ")
    min_compound_changes = int(min_compound_changes) if min_compound_changes.isdigit() else 2
    data = load_race_data(filename)
    data.columns = [col.strip() for col in data.columns]
    enhanced_stats(data)
    find_planned_pitstop(data, wear_threshold)
    find_current_pit_advice(data, wear_threshold, recent_laps=3)
    summarize_stints(data)
    stints = get_race_stints(data, race_length_laps, required_pitstops, wear_threshold, min_compound_changes)
    if stints:
        plot_strategy_with_paging(data, stints)

if __name__ == "__main__":
    main()