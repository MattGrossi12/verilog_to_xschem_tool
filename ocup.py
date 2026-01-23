import math

def generate_occupation_matrix(builder, cells, x_base, y_step, x_step, max_rows):
    """
    Organiza células de infraestrutura (decap, tap, fill) em uma matriz quadrada.
    As instâncias são adicionadas diretamente ao builder fornecido.
    """
    if not cells:
        return 0  # Retorna 0 se não há células
    
    # Número de células
    num_cells = len(cells)
    
    # Calcula o tamanho da matriz quadrada (baseado na raiz quadrada)
    # Exemplo: 16 células → n=4, 12 células → n=4 (ceil(sqrt(12)) = 4)
    n = math.ceil(math.sqrt(num_cells))
    
    print(f"[INFO] Matriz de ocupação: {num_cells} células, matriz {n}x{n}")
    
    # Organiza as células em uma matriz quadrada
    for i, cell in enumerate(cells):
        # Calcula posição na matriz (coluna, linha)
        col = i % n
        row = i // n
        
        # Calcula coordenadas X e Y
        # x_base é o ponto inicial, x_step é o espaçamento entre colunas
        x = x_base + (col * x_step)
        # y_base é 0, y_step é o espaçamento entre linhas (positivo para cima)
        y = (row * y_step)
        
        # Atributos padrão para células sky130
        builder.add_instance(
            sym_path=f"sky130_stdcells/{cell['type']}.sym",
            x=x,
            y=y,
            rotation=0,
            name=cell['name']
        )
    
    # Retorna o número de colunas (n) para que o main.py saiba onde começar o próximo bloco
    return n

# Versão alternativa: se você queria usar max_rows para limitar linhas
def generate_occupation_matrix_with_max_rows(builder, cells, x_base, y_step, x_step, max_rows):
    """
    Organiza células de infraestrutura em uma matriz com número máximo de linhas.
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