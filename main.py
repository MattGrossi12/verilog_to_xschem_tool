import re
import sys
import os
import shutil
import math
import ocup
import func_cell_wr

class SchBuilder:
    """Classe responsável pela sintaxe e estrutura do arquivo .sch do Xschem."""
    def __init__(self, version="3.4.8RC"):
        self.lines = [
            f"v {{xschem version={version} file_version=1.3}}",
            "G {}", "K {}", "V {}", "S {}", "F {}", "E {}", ""
        ]

    def add_instance(self, sym_path, x, y, rotation, name, extra_attrs=""):
        attr = f"name={name} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__"
        if extra_attrs:
            attr += f" {extra_attrs}"
        self.lines.append(f"C {{{sym_path}}} {x} {y} {rotation} 0 {{{attr}}}")

    def add_wire(self, x1, y1, x2, y2, label=None):
        line = f"N {x1} {y1} {x2} {y2} "
        line += f"{{lab={label}}}" if label else "{}"
        self.lines.append(line)

    def add_io_pin(self, sym_path, x, y, rotation, name, label):
        self.lines.append(f"C {{{sym_path}}} {x} {y} {rotation} 0 {{name={name} lab={label}}}")

    def get_content(self):
        return "\n".join(self.lines)

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
        destination = os.path.join("..", filename)
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

        # Módulo de Ocupação: insere células de infraestrutura
        num_cols = ocup.generate_occupation_matrix(builder, occ_cells, X_MATRIZ_BASE, 100, 200, 10)

        # Módulo Funcional: calcula posição após a matriz para evitar sobreposição
        x_func_start = X_MATRIZ_BASE + (max(1, num_cols) * 200) + 400
        
        # IMPORTANTE: Garanta que func_cell_wr também foi atualizado para usar o 'builder'
        func_cell_wr.generate_functional_block(builder, func_cells, inputs, outputs, x_func_start, -500)

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