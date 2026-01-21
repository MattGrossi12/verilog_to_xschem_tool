from sky130_db import CELL_DB

def get_pin_side(pin_name):
    """
    Determina se um pino deve ficar à esquerda (entrada) ou à direita (saída).
    Segue as convenções da biblioteca sky130_fd_sc_hd.
    """
    # Entradas típicas
    input_prefixes = ['A', 'B', 'C', 'D', 'S', 'CLK', 'RESET', 'SET', 'SLEEP', 'GATE', 'DE', 'CI']
    # Saídas típicas
    output_prefixes = ['X', 'Y', 'Q', 'CO', 'GCLK']
    
    name_upper = pin_name.upper()
    
    if any(name_upper.startswith(p) for p in input_prefixes):
        return "LEFT"
    if any(name_upper.startswith(p) for p in output_prefixes):
        return "RIGHT"
    
    # Caso especial: 'S' pode ser seletor (entrada) ou soma (saída)
    # No DB, somadores usam 'S' na direita e Muxes usam 'S' na esquerda.
    return "LEFT" # Padrão para segurança

def generate_functional_block(cells, inputs, outputs, x_start, y_start):
    lines = []
    for i, cell in enumerate(cells):
        y_gate = y_start - (i * 300)
        x_gate = x_start
        cell_type = cell['type']
        
        # 1. Colocação da Instância da Célula
        attr = f"name={cell['name']} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__"
        lines.append(f"C {{sky130_stdcells/{cell_type}.sym}} {x_gate} {y_gate} 0 0 {{{attr}}}")
        
        # 2. Busca de métricas no nosso Banco de Dados
        # Caso a célula não exista, define um fallback padrão
        cell_metrics = CELL_DB.get(cell_type, {})
        
        for pin_name, net_name in cell['conns']:
            # Ignora pinos de alimentação global
            if pin_name in ['VGND', 'VNB', 'VPB', 'VPWR']:
                continue
            
            # Obtém métricas: dy (vertical), dx_off (distância do centro ao pino)
            # Fallback padrão se o pino não estiver no DB: dy=0, dx=60
            dy, dx_off = cell_metrics.get(pin_name, (0, 60))
            
            yp = y_gate + dy
            side = get_pin_side(pin_name)
            
            if side == "LEFT":
                # Ponto exato onde o fio toca o pino no símbolo
                xp_pin = x_gate - dx_off
                
                if net_name in inputs:
                    # CONEXÃO GLOBAL: Fio do ipin (-150) até o pino
                    lines.append(f"N {x_gate-150} {yp} {xp_pin} {yp} {{lab={net_name}}}")
                    lines.append(f"C {{ipin.sym}} {x_gate-150} {yp} 0 0 {{name=in_{net_name}_{i} lab={net_name}}}")
                else:
                    # CONEXÃO INTERNA: Stub de 30 unidades para clareza
                    lines.append(f"N {xp_pin-30} {yp} {xp_pin} {yp} {{lab={net_name}}}")
            
            else: # side == "RIGHT"
                # Ponto exato onde o fio toca o pino no símbolo
                xp_pin = x_gate + dx_off
                
                if net_name in outputs:
                    # CONEXÃO GLOBAL: Fio do pino até o opin (+150)
                    lines.append(f"N {xp_pin} {yp} {x_gate+150} {yp} {{lab={net_name}}}")
                    lines.append(f"C {{opin.sym}} {x_gate+150} {yp} 0 0 {{name=out_{net_name}_{i} lab={net_name}}}")
                else:
                    # CONEXÃO INTERNA: Stub de 30 unidades
                    lines.append(f"N {xp_pin} {yp} {xp_pin+30} {yp} {{lab={net_name}}}")

    return lines