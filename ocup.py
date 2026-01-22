import math

def generate_occupation_matrix(builder, cells, x_base, y_step, x_step, max_rows):
    """
    Organiza células de infraestrutura (decap, tap, fill) em uma matriz.
    As instâncias são adicionadas diretamente ao builder fornecido.
    """
    for i, cell in enumerate(cells):
        col = i // max_rows
        row = i % max_rows
        x = x_base + (col * x_step)
        y = row * y_step
        
        # Atributos padrão para células sky130
        # name={cell_name} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__
        builder.add_instance(
            sym_path=f"sky130_stdcells/{cell['type']}.sym",
            x=x,
            y=y,
            rotation=0,
            name=cell['name']
        )
    
    # Retorna o número de colunas para que o main.py saiba onde começar o próximo bloco
    num_cols = math.ceil(len(cells) / max_rows) if cells else 0
    return num_cols