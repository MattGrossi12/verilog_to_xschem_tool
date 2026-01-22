def calculate_matrix_positions(cells, x_start, y_start, max_per_col=4, dx=1000, dy=400):
    """
    Define as coordenadas (x, y) de cada célula em uma grade.
    max_per_col: Quantas células por coluna antes de saltar para a próxima.
    dx/dy: Espaçamento horizontal e vertical.
    """
    positions = []
    for i in range(len(cells)):
        col = i // max_per_col
        row = i % max_per_col
        x = x_start + (col * dx)
        y = y_start - (row * dy)
        positions.append((x, y))
    return positions