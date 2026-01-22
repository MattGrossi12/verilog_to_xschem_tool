import re
import sys
import os
import shutil
import ocup
import func_cell_wr

def move_file_to_parent(filename):
    """Move o arquivo gerado para o diretório pai (test_directory)"""
    try:
        destination = os.path.join("test_directory", filename)
        shutil.move(filename, destination)
        print(f"Arquivo movido com sucesso para: {destination}")
    except Exception as e:
        print(f"Erro ao mover o arquivo: {e}")

def run_converter(input_file):
    output_file = "rn_wrapper.sch"
    
    if not os.path.exists(input_file):
        print(f"Erro: {input_file} não encontrado.")
        return

    inputs, outputs = {}, {}
    occ_cells, func_cells = [], []

    try:
        with open(input_file, 'r') as f:
            content = f.read()

        # Extração de Portas
        re_port = re.compile(r"^\s*(input|output)\s+(\[[^\]]+\]\s+)?(\w+)", re.MULTILINE)
        for direction, _, name in re_port.findall(content):
            if direction == "input": inputs[name] = True
            else: outputs[name] = True

        # Extração de Instâncias
        reserved = ['module', 'endmodule', 'input', 'output', 'wire', 'assign', 'always']
        re_inst = re.compile(r"(\w+)\s+(\w+)\s*\((.*?)\);", re.DOTALL)
        
        for cell_type, inst_name, pins_raw in re_inst.findall(content):
            if cell_type in reserved: continue
            
            pin_conns = re.findall(r"\.(\w+)\(([^)]+)\)", pins_raw)
            data = {'type': cell_type, 'name': inst_name, 'conns': pin_conns}
            
            if any(x in cell_type.lower() for x in ['decap', 'fill', 'tap']):
                occ_cells.append(data)
            else:
                func_cells.append(data)

        # Montagem do Arquivo
        sch_lines = ["v {xschem version=3.4.8RC file_version=1.3}", "G {}", "K {}", "V {}", "S {}", "F {}", "E {}", ""]
        X_MATRIZ_BASE = -1200

        # Módulo de Ocupação
        occ_lines, num_cols = ocup.generate_occupation_matrix(occ_cells, X_MATRIZ_BASE, 100, 200, 10)
        sch_lines.extend(occ_lines)

        # Módulo Funcional
        x_func_start = X_MATRIZ_BASE + (max(1, num_cols) * 200) + 400
        func_lines = func_cell_wr.generate_functional_block(func_cells, inputs, outputs, x_func_start, -500)
        sch_lines.extend(func_lines)

        # Salva localmente primeiro
        with open(output_file, 'w') as f_out:
            f_out.write("\n".join(sch_lines))
        
        print(f"Esquemático '{output_file}' gerado.")

        # Move para o diretório pai
        move_file_to_parent(output_file)

    except Exception as e:
        print(f"Erro no processamento: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        run_converter(sys.argv[1])
    else:
        print("Uso: python main.py <arquivo.v>")