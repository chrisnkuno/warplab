import pandas as pd
import matplotlib.pyplot as plt

def prepare_results_dataframe(results: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(results)
    if df.empty:
        return df
    return df.sort_values("score", ascending=False, na_position="last")

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

def plot_stability_vs_speedup(df_results: pd.DataFrame):
    """Visualizes the speedup/stability trade-off for valid candidates."""
    if df_results.empty or "speedup" not in df_results.columns or "cv" not in df_results.columns:
        print("No speedup/CV data available to plot.")
        return

    df = df_results.dropna(subset=["speedup", "cv"])
    if df.empty:
        print("No valid speedup/CV rows available to plot.")
        return

    plt.figure(figsize=(10, 5))
    plt.scatter(df["cv"] * 100.0, df["speedup"], alpha=0.75)
    plt.xlabel("Coefficient of Variation (%)")
    plt.ylabel("Speedup vs Baseline (x)")
    plt.title("Stability vs Speedup")
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_top_candidates(df_results: pd.DataFrame, top_n: int = 10):
    """Plots the speedup of the top candidates."""
    if df_results.empty or "speedup" not in df_results.columns:
        print("No speedup data available to plot.")
        return

    df = df_results.dropna(subset=["speedup"]).head(top_n)
    if df.empty:
        print("No ranked candidates available to plot.")
        return

    labels = df.get("id", pd.Series(range(len(df)))).astype(str)
    plt.figure(figsize=(12, 5))
    plt.bar(labels, df["speedup"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Speedup vs Baseline (x)")
    plt.title(f"Top {len(df)} Candidates")
    plt.tight_layout()
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
