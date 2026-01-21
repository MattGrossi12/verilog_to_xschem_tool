import re
import sys
import os

def clean_and_organize_netlist(input_file):
    output_file = "rn_wrapper.v"
    
    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return

    # Regras de Renomeação de Células
    decap_pattern = r"sky130_ef_sc_hd__decap_\d+_12"
    standard_prefix = "sky130_fd_sc_hd__"

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()

        # 1. Pré-processamento: Limpeza de nomes e extração de dados
        module_name = "unknown"
        inputs = {}
        outputs = {}
        body = []
        
        # Regex para capturar o nome do módulo
        re_module = re.compile(r"module\s+(\w+)")
        # Regex para capturar input/output [largura] nome;
        re_port = re.compile(r"^\s*(input|output)\s+(\[[^\]]+\]\s+)?(\w+)\s*;")
        
        # Flags de controle
        found_first_body_line = False

        for line in lines:
            # Aplica renomeação de células na linha
            line = re.sub(decap_pattern, "decap_12", line)
            line = re.sub(standard_prefix, "", line)
            
            stripped = line.strip()
            if not stripped: continue

            # Identifica nome do módulo
            m_mod = re_module.search(stripped)
            if m_mod and module_name == "unknown":
                module_name = m_mod.group(1)
                continue

            # Captura definições de portas
            m_port = re_port.search(stripped)
            if m_port:
                direction = m_port.group(1)
                width = m_port.group(2).strip() + " " if m_port.group(2) else ""
                name = m_port.group(3)
                
                if direction == "input":
                    inputs[name] = f"input {width}{name}"
                else:
                    outputs[name] = f"output {width}{name}"
                continue

            # Identifica o início do corpo real (wires ou instâncias)
            # Ignora linhas que são apenas nomes de portas ou parênteses do cabeçalho antigo
            if stripped.startswith("wire") or ("(" in stripped and not stripped.startswith("module")):
                found_first_body_line = True
            
            if found_first_body_line and not stripped.startswith("endmodule"):
                body.append(line)

        # 2. Reconstrução seguindo IEEE 1364-2005 (Estilo ANSI)
        with open(output_file, 'w') as f_out:
            f_out.write(f"module {module_name} (\n")
            
            # Ordena entradas e saídas alfabeticamente
            sorted_ports = [inputs[k] for k in sorted(inputs)] + [outputs[k] for k in sorted(outputs)]
            
            for i, port in enumerate(sorted_ports):
                comma = "," if i < len(sorted_ports) - 1 else ""
                f_out.write(f"    {port}{comma}\n")
            
            f_out.write(");\n\n")

            # Escreve o corpo (wires e instâncias)
            for b_line in body:
                f_out.write(b_line)
            
            f_out.write("\nendmodule\n")
        
        print(f"Sucesso! O arquivo '{output_file}' foi limpo e normalizado.")

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python rename_netlist.py <arquivo_origem.v>")
    else:
        clean_and_organize_netlist(sys.argv[1])