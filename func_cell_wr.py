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
    return "LEFT" 

def generate_functional_block(builder, cells, inputs, outputs, x_start, y_start):
    """
    Gera o bloco funcional no esquemático usando o SchBuilder.
    Agora recebe o builder como primeiro argumento.
    """
    for i, cell in enumerate(cells):
        y_gate = y_start - (i * 300)
        x_gate = x_start
        cell_type = cell['type']
        
        # 1. Colocação da Instância da Célula via Builder
        builder.add_instance(
            sym_path=f"sky130_stdcells/{cell_type}.sym",
            x=x_gate,
            y=y_gate,
            rotation=0,
            name=cell['name']
        )
        
        # 2. Busca de métricas no Banco de Dados
        cell_metrics = CELL_DB.get(cell_type, {})
        
        for pin_name, net_name in cell['conns']:
            # Ignora pinos de alimentação global
            if pin_name in ['VGND', 'VNB', 'VPB', 'VPWR']:
                continue
            
            # Obtém métricas: dy (vertical), dx_off (distância horizontal)
            dy, dx_off = cell_metrics.get(pin_name, (0, 60))
            
            yp = y_gate + dy
            side = get_pin_side(pin_name)
            
            if side == "LEFT":
                xp_pin = x_gate - dx_off
                
                if net_name in inputs:
                    # CONEXÃO GLOBAL: Fio do ipin até o pino
                    builder.add_wire(x_gate - 150, yp, xp_pin, yp, net_name)
                    builder.add_io_pin("ipin.sym", x_gate - 150, yp, 0, f"in_{net_name}_{i}", net_name)
                else:
                    # CONEXÃO INTERNA: Stub de 30 unidades
                    builder.add_wire(xp_pin - 30, yp, xp_pin, yp, net_name)
            
            else: # side == "RIGHT"
                xp_pin = x_gate + dx_off
                
                if net_name in outputs:
                    # CONEXÃO GLOBAL: Fio do pino até o opin
                    builder.add_wire(xp_pin, yp, x_gate + 150, yp, net_name)
                    builder.add_io_pin("opin.sym", x_gate + 150, yp, 0, f"out_{net_name}_{i}", net_name)
                else:
                    # CONEXÃO INTERNA: Stub de 30 unidades
                    builder.add_wire(xp_pin, yp, xp_pin + 30, yp, net_name)