import pandas as pd
import matplotlib.pyplot as plt

def plot_performance_distribution(df_results: pd.DataFrame):
    """Plots the distribution of speedups across evaluated candidates."""
    if df_results.empty or 'speedup' not in df_results.columns:
        print("No speedup data available to plot.")
        return
        
    plt.figure(figsize=(10, 5))
    plt.hist(df_results['speedup'].dropna(), bins=20, alpha=0.7, color='blue', edgecolor='black')
    plt.title('Distribution of Kernel Speedups')
    plt.xlabel('Speedup vs Baseline (x)')
    plt.ylabel('Number of Variants')
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_parameter_impact(df_results: pd.DataFrame, param: str):
    """Visualizes the impact of a specific parameter on the speedup."""
    if df_results.empty or 'config' not in df_results.columns:
        print("No configuration data available to plot.")
        return
        
    df = df_results.copy()
    # Extract parameter from config params dict
    df[param] = df['config'].apply(lambda c: c.get('params', {}).get(param) if isinstance(c, dict) else None)
    df = df.dropna(subset=[param, 'speedup'])
    
    if df.empty:
        print(f"Parameter '{param}' not found in candidate configs.")
        return
        
    plt.figure(figsize=(10, 5))
    df.boxplot(column='speedup', by=param, grid=True)
    plt.title(f'Performance impact of {param}')
    plt.suptitle('')  # Removes the default pandas suptitle
    plt.ylabel('Speedup vs Baseline (x)')
    plt.xlabel(param)
    plt.show()
