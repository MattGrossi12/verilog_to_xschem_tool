import re
import sys
import os
import shutil
import math
import ocup
import func_cell_wr
from sch_builder import SchBuilder

def clean_verilog(content):
    """Remove comentários e normaliza o código para facilitar o parsing."""
    # Remove /* ... */
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove // ...
    content = re.sub(r'//.*', '', content)
    # Normaliza múltiplos espaços/quebras em um único espaço
    content = re.sub(r'\s+', ' ', content)
    return content

def move_file_to_parent(filename):
    try:
        destination = os.path.join("test_directory", filename)
        shutil.move(filename, destination)
        print(f"Arquivo movido para: {destination}")
    except Exception as e:
        print(f"Erro ao mover arquivo: {e}")

def run_converter(input_file):
    output_file = "rn_wrapper.sch"
    
    if not os.path.exists(input_file):
        print(f"Erro: {input_file} não encontrado.")
        return

    try:
        with open(input_file, 'r') as f:
            # Etapa de limpeza para ignorar ruído no parsing
            content = clean_verilog(f.read())

        inputs, outputs = {}, {}
        occ_cells, func_cells = [], []

        # Extração de Portas (considerando barramentos)
        re_port = re.compile(r"(input|output)\s+(?:\[[^\]]+\]\s+)?(\w+)")
        for direction, name in re_port.findall(content):
            if direction == "input": inputs[name] = True
            else: outputs[name] = True

        # Extração de Instâncias robusta (ignora parâmetros #(...) se existirem)
        re_inst = re.compile(r"(\w+)\s*(?:#\s*\([^)]+\)\s*)?(\w+)\s*\((.*?)\);")
        
        for cell_type, inst_name, pins_raw in re_inst.findall(content):
            reserved = ['module', 'endmodule', 'input', 'output', 'wire', 'assign', 'always']
            if cell_type in reserved: continue
            
            pin_conns = re.findall(r"\.(\w+)\(([^)]+)\)", pins_raw)
            data = {'type': cell_type, 'name': inst_name, 'conns': pin_conns}
            
            if any(x in cell_type.lower() for x in ['decap', 'fill', 'tap']):
                occ_cells.append(data)
            else:
                func_cells.append(data)

        # Inicia o Builder do Esquemático
        builder = SchBuilder()
        X_MATRIZ_BASE = -1200
        Y_MATRIZ_BASE = 100  # y_start no ocup.py
        Y_STEP = 200  # y_step no ocup.py
        MAX_ROWS = 10  # max_rows no ocup.py
        
        # Módulo de Ocupação: insere células de infraestrutura
        num_cols = ocup.generate_occupation_matrix(builder, occ_cells, X_MATRIZ_BASE, Y_MATRIZ_BASE, 200, MAX_ROWS)
        
        # Calcula a posição Y da última linha da matriz de ocupação
        # A última linha está em: Y_MATRIZ_BASE + (MAX_ROWS - 1) * Y_STEP
        # Mas se tiver menos células que MAX_ROWS, calculamos a linha real
        num_cells = len(occ_cells)
        if num_cells > 0:
            # Encontra a linha máxima ocupada
            actual_max_row = min((num_cells - 1) % MAX_ROWS, MAX_ROWS - 1)
            y_last_occupation_line = Y_MATRIZ_BASE + (actual_max_row * Y_STEP)
        else:
            # Se não há células de ocupação, usa a base
            y_last_occupation_line = Y_MATRIZ_BASE
        
        # Módulo Funcional: posiciona 1000px abaixo da última linha de ocupação
        x_func_start = X_MATRIZ_BASE
        y_func_start = y_last_occupation_line - 1000  # 1000px para baixo (negativo em Y)
        
        print(f"[INFO] Posicionamento do bloco funcional:")
        print(f"  Última linha de ocupação: Y = {y_last_occupation_line}")
        print(f"  Bloco funcional: X = {x_func_start}, Y = {y_func_start}")
        
        # Gera o bloco funcional
        func_cell_wr.generate_functional_block(builder, func_cells, inputs, outputs, x_func_start, y_func_start)

        # Salva o resultado final
        with open(output_file, 'w') as f_out:
            f_out.write(builder.get_content())
        
        print(f"Esquemático '{output_file}' gerado com sucesso.")
        move_file_to_parent(output_file)

    except Exception as e:
        print(f"Erro no processamento: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        run_converter(sys.argv[1])
    else:
        print("Uso: python main.py <arquivo.v>")