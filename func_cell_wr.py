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
    
    return "LEFT"

def generate_functional_block(builder, cells, inputs, outputs, x_start, y_start):
    """
    Gera o bloco funcional no esquemático usando o SchBuilder.
    """
    for i, cell in enumerate(cells):
        y_gate = y_start - (i * 300)
        x_gate = x_start
        cell_type = cell['type']
        
        # 1. Validação da célula
        final_sym, final_type, substituted, reason = builder.resolve_cell_sym(
            cell_type=cell_type,
            sym_path=f"sky130_stdcells/{cell_type}.sym"
        )
        
        if substituted:
            print(f"[INFO] Célula personalizada '{cell_type}' substituída por '{final_type}' para simulação")
        
        # 2. Se foi substituída por buf_1, mapeamos os pinos automaticamente
        # Extrai apenas pinos não-power (deve ser exatamente 2)
        non_power_pins = []
        for pin_name, net_name in cell['conns']:
            if pin_name not in ['VGND', 'VNB', 'VPB', 'VPWR']:
                non_power_pins.append((pin_name, net_name))
        
        """
        # Verifica se temos exatamente 2 pinos não-power
        if len(non_power_pins) != 2:
            print(f"[WARN] Célula '{cell_type}' tem {len(non_power_pins)} pinos não-power (esperado: 2)")
        """
        
        # 3. Cria mapeamento automático para buf_1
        pin_mapping = {}
        if substituted and final_type == "buf_1" and len(non_power_pins) == 2:
            # Primeiro pino não-power -> A (entrada do buf_1)
            # Segundo pino não-power -> X (saída do buf_1)
            pin_mapping[non_power_pins[0][0]] = 'A'  # Primeiro pino -> entrada
            pin_mapping[non_power_pins[1][0]] = 'X'  # Segundo pino -> saída
            print(f"[INFO] Mapeamento automático: {non_power_pins[0][0]} -> A, {non_power_pins[1][0]} -> X")
        
        # 4. Adiciona a instância
        builder.add_instance(
            sym_path=final_sym,
            x=x_gate,
            y=y_gate,
            rotation=0,
            name=cell['name'],
            cell_type=final_type
        )
        
        # 5. Busca de métricas no Banco de Dados
        cell_metrics = CELL_DB.get(final_type, {})
        
        # 6. Conexão dos pinos
        for pin_name, net_name in cell['conns']:
            # Ignora pinos de alimentação global
            if pin_name in ['VGND', 'VNB', 'VPB', 'VPWR']:
                continue
            
            # Determina o nome real do pino a ser usado (mapeado ou original)
            actual_pin_name = pin_mapping.get(pin_name, pin_name)
            
            # Obtém métricas para o pino
            dy, dx_off = cell_metrics.get(actual_pin_name, (0, 60))
            
            yp = y_gate + dy
            side = get_pin_side(actual_pin_name)
            
            if side == "LEFT":
                xp_pin = x_gate - dx_off
                
                if net_name in inputs:
                    builder.add_wire(x_gate - 150, yp, xp_pin, yp, net_name)
                    builder.add_io_pin("ipin.sym", x_gate - 150, yp, 0, f"in_{net_name}_{i}", net_name)
                else:
                    builder.add_wire(xp_pin - 30, yp, xp_pin, yp, net_name)
            
            else:  # side == "RIGHT"
                xp_pin = x_gate + dx_off
                
                if net_name in outputs:
                    builder.add_wire(xp_pin, yp, x_gate + 150, yp, net_name)
                    builder.add_io_pin("opin.sym", x_gate + 150, yp, 0, f"out_{net_name}_{i}", net_name)
                else:
                    builder.add_wire(xp_pin, yp, xp_pin + 30, yp, net_name)