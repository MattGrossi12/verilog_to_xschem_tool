import math

def generate_occupation_matrix(builder, cells, x_base, y_step, x_step, max_rows):
    """
    ⚠ MODO TEMPORÁRIO DESATIVADO ⚠
    Células de ocupação (decap, tap, fill) foram DESATIVADAS para facilitar
    o desenvolvimento e visualização do bloco funcional principal.

    Para reativar, remova o 'return 0' e o bloco comentado abaixo.
    """

    # ====== MODO DESATIVADO ======
    print("[INFO] MODO DE OCUPAÇÃO DESATIVADO — nenhuma célula de infraestrutura será desenhada.")
    return 0  # <- importante: retorna 0 para que main.py saiba que não há deslocamento no X

    # ====== IMPLEMENTAÇÃO ORIGINAL (DESATIVADA) ======
    # (código original aqui, mantido como comentário)
    """
    if not cells:
        return 0
    
    num_cells = len(cells)
    n = math.ceil(math.sqrt(num_cells))
    print(f"[INFO] Matriz de ocupação: {num_cells} células, matriz {n}x{n}")

    for i, cell in enumerate(cells):
        col = i % n
        row = i // n
        x = x_base + (col * x_step)
        y = (row * y_step)

        builder.add_instance(
            sym_path=f"sky130_stdcells/{cell['type']}.sym",
            x=x,
            y=y,
            rotation=0,
            name=cell['name']
        )

    return n
    """

# Versão alternativa: se você queria usar max_rows para limitar linhas
def generate_occupation_matrix_with_max_rows(builder, cells, x_base, y_step, x_step, max_rows):
    print("[INFO] MODO DE OCUPAÇÃO DESATIVADO — nenhuma célula de infraestrutura será desenhada.")
    return 0
    """
    Organiza células de infraestrutura em uma matriz com número máximo de linhas.
    """
    """
    if not cells:
        return 0
    
    num_cells = len(cells)
    
    # Calcula número de colunas baseado no max_rows
    num_cols = math.ceil(num_cells / max_rows)
    
    print(f"[INFO] Matriz de ocupação: {num_cells} células, {num_cols}x{max_rows}")
    
    for i, cell in enumerate(cells):
        col = i // max_rows  # Divisão inteira para coluna
        row = i % max_rows   # Resto para linha
        
        x = x_base + (col * x_step)
        y = (row * y_step)
        
        builder.add_instance(
            sym_path=f"sky130_stdcells/{cell['type']}.sym",
            x=x,
            y=y,
            rotation=0,
            name=cell['name']
        )
    
    return num_cols
    """