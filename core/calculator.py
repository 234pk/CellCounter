def calculate_concentration(total_cells, dilution=1.0, num_squares=4, volume_per_square=1e-4):
    """
    Calculate cell concentration based on total cells counted.
    
    Args:
        total_cells: Total number of cells detected
        dilution: Dilution factor (e.g., 2.0 for 1:2 dilution)
        num_squares: Number of large squares counted
        volume_per_square: Volume of one large square in mL (standard is 0.0001 mL)
        
    Returns:
        Concentration in cells/mL
    """
    total_volume = volume_per_square * num_squares
    if total_volume <= 0:
        return 0
    # Formula: Concentration = (Counted Cells / Counted Volume) * Dilution Factor
    return (total_cells / total_volume) * dilution
