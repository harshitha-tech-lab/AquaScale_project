import pandas as pd
import numpy as np
import os

DATASET_FILE = 'fish_growth_data.csv'

def generate_synthetic_data(num_samples=1000):
    """Generates a synthetic dataset for Fish Length vs Maturity."""
    if os.path.exists(DATASET_FILE):
        return

    np.random.seed(42)
    
    # Tilapia: ~10-40cm, Weight relationship W = a * L^b (approx)
    # Using hypothetical linear-ish mapping for MVP: Weight = 1.5 * Length^2.2 (just an example curve)
    l_tilapia = np.random.uniform(5, 35, num_samples)
    w_tilapia = 0.02 * (l_tilapia ** 3.0) + np.random.normal(0, 20, num_samples) # Cubic relationship
    
    # Snakehead: ~20-80cm
    l_snakehead = np.random.uniform(15, 80, num_samples)
    w_snakehead = 0.01 * (l_snakehead ** 3.0) + np.random.normal(0, 50, num_samples)

    data = []
    
    for l, w in zip(l_tilapia, w_tilapia):
        phase = "Growing Phase"
        if w > 200: phase = "About to Mature" 
        if w > 500: phase = "Matured"
        data.append(['Tilapia', l, w, phase])

    for l, w in zip(l_snakehead, w_snakehead):
        phase = "Growing Phase"
        if w > 500: phase = "About to Mature"
        if w > 1000: phase = "Matured"
        data.append(['Snakehead', l, w, phase])
        
    df = pd.DataFrame(data, columns=['Species', 'Length_cm', 'Weight_g', 'Growth_Phase'])
    df.to_csv(DATASET_FILE, index=False)
    print(f"Synthetic dataset created: {DATASET_FILE}")

def estimate_weight(length, species):
    """Estimate weight based on Length using synthetic data rules."""
    if species == 'Tilapia':
        return 0.02 * (length ** 3.0)
    elif species == 'Snakehead':
        return 0.01 * (length ** 3.0)
    return 0.0

def get_growth_phase(species, length):
    """Calculate the growth phase based on species and estimated length."""
    if species == 'Tilapia':
        if length <= 10:
            return "Juvenile"
        elif length <= 20:
            return "Growing"
        else:
            return "Mature"
    elif species == 'Snakehead':
        if length <= 20:
            return "Juvenile"
        elif length <= 35:
            return "Growing"
        else:
            return "Mature"
    return "Unknown"


# Initialize dataset on import
generate_synthetic_data()
