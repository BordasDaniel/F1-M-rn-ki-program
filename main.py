import pandas as pd

def load_race_data(filename):
    return pd.read_csv(filename)

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

def find_planned_pitstop(data, wear_threshold=70):
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

def find_current_pit_advice(data, wear_threshold=70, recent_laps=3):
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

def summarize_stints(data):
    data['Average Tire Usage'] = data[['Front left tire usage (percentage)',
                                       'Front right tire usage (percentage)',
                                       'Rear left tire usage (percentage)',
                                       'Rear right tire usage (percentage)']].mean(axis=1)
    resets = (data['Average Tire Usage'] < 5).cumsum()
    compound_column = [col for col in data.columns if 'Compound' in col][0]
    print("\nStint summaries:")
    for stint, group in data.groupby(resets):
        first_lap = group['Lap'].iloc[0]
        last_lap = group['Lap'].iloc[-1]
        compound = group[compound_column].iloc[0]
        num_laps = last_lap - first_lap + 1
        print(f"  Stint {stint}: {first_lap}-{last_lap} ({num_laps} laps) on {compound}")

def main():
    filename = 'datas.csv'
    data = load_race_data(filename)
    data.columns = [col.strip() for col in data.columns]
    enhanced_stats(data)
    find_planned_pitstop(data, wear_threshold=70)
    find_current_pit_advice(data, wear_threshold=70, recent_laps=3)
    summarize_stints(data)

if __name__ == "__main__":
    main()
