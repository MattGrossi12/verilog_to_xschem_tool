from sky130_db import CELL_DB
from collections import defaultdict

def get_pin_side(pin_name):
    """
    Determina se um pino deve ficar à esquerda (entrada) ou à direita (saída).
    Segue as convenções da biblioteca sky130_fd_sc_hd.
    """
    # Entradas típicas
    input_prefixes = ['A', 'B', 'C', 'D', 'S', 'CLK', 'RESET', 'SET', 'SLEEP', 'GATE', 'DE', 'CI', 'TE', 'HI', 'SI', 'SE']
    # Saídas típicas
    output_prefixes = ['X', 'Y', 'Q', 'CO', 'GCLK', 'LO', 'CON']
    
    name_upper = pin_name.upper()
    
    if any(name_upper.startswith(p) for p in input_prefixes):
        return "LEFT"
    if any(name_upper.startswith(p) for p in output_prefixes):
        return "RIGHT"
    
    return "LEFT"

def build_circuit_graph(cells, global_inputs):
    """
    Constrói um grafo de dependências para determinar a profundidade (Rank) de cada célula.
    Retorna: Um dicionário {cell_index: rank_integer}
    """
    # 1. Mapear quem "dirige" cada net (Net -> Index da Célula Produtora)
    net_drivers = {}
    
    # Adiciona as entradas globais como drivers virtuais
    for inp in global_inputs:
        net_drivers[inp] = -1  # -1 indica Input Global

    # Mapeia as saídas das células
    for idx, cell in enumerate(cells):
        for pin_name, net_name in cell['conns']:
            if get_pin_side(pin_name) == "RIGHT":
                net_drivers[net_name] = idx

    # 2. Determinar o Rank de cada célula (ASAP - As Soon As Possible)
    # Inicialmente, desconhecido = -1
    cell_ranks = {i: -1 for i in range(len(cells))}
    
    # Detecção de ciclos simples: limitamos a iteração pelo número de células
    changed = True
    max_iterations = len(cells) + 2
    iter_count = 0

    while changed and iter_count < max_iterations:
        changed = False
        iter_count += 1
        
        for idx, cell in enumerate(cells):
            max_input_rank = -1
            has_unresolved_input = False
            
            # Verifica as conexões de entrada dessa célula
            for pin_name, net_name in cell['conns']:
                if get_pin_side(pin_name) == "LEFT":
                    driver_idx = net_drivers.get(net_name)
                    
                    if driver_idx is None:
                        # Net flutuante ou não encontrada, assume rank 0
                        current_rank = 0
                    elif driver_idx == -1:
                        # Conectado a Input Global
                        current_rank = 0
                    else:
                        # Conectado a outra célula
                        driver_rank = cell_ranks[driver_idx]
                        if driver_rank == -1:
                            has_unresolved_input = True
                            continue # CORREÇÃO: Pula para o próximo pino se a dependência não foi resolvida
                        else:
                            current_rank = driver_rank + 1
                    
                    if current_rank > max_input_rank:
                        max_input_rank = current_rank

            # Se a célula tem inputs não resolvidos (feedback loop), 
            # mantemos o rank atual ou definimos um mínimo se for a primeira passada
            final_rank = max(0, max_input_rank)
            
            # Só atualizamos se tivermos certeza (sem inputs pendentes) OU se já estamos
            # num estado onde precisamos forçar uma atualização (para evitar lock em loops)
            # Mas a lógica simples de ASAP é: atualiza se o rank calculado for maior
            
            if final_rank > cell_ranks[idx]:
                 cell_ranks[idx] = final_rank
                 changed = True
    
    # 3. Fallback: Se sobrar alguém com rank -1 (loops complexos), joga no rank 0
    for idx in cell_ranks:
        if cell_ranks[idx] == -1:
            cell_ranks[idx] = 0
            
    return cell_ranks

def generate_functional_block(builder, cells, inputs, outputs, x_start, y_start):
    """
    Gera o bloco funcional no esquemático usando posicionamento por grafos (Camadas).
    """
    if not cells:
        return


    # --- ETAPA 1: Lógica de Grafo (Calcula posições abstratas) ---
    print(f"[INFO] Calculando topologia do circuito para {len(cells)} células...")
    
    ranks = build_circuit_graph(cells, inputs)
    # Determinar rank máximo existente
    max_rank = max(ranks.values()) if ranks else 0
    # Muitas vezes ranks grandes aparecem apenas porque as dependências são lineares.
    # Aqui compactamos: células com mesmo conjunto de dependências ficam no mesmo rank.
    # Isso evita centenas de camadas e esquemas gigantes.
    condensed = {}
    next_rank = 0

    for idx in sorted(ranks, key=lambda i: ranks[i]):
        r = ranks[idx]
        if r not in condensed:
            condensed[r] = next_rank
            next_rank += 1
        ranks[idx] = condensed[r]

    # Recalcular máximo após condensação
    
    max_rank = max(ranks.values()) if ranks else 0

    # Atribuir ranks especiais para pinos de I/O
    input_ranks = {net: -1 for net in inputs}              # sempre mais à esquerda
    output_ranks = {net: max_rank + 1 for net in outputs}  # sempre mais à direita


    layers = defaultdict(list)

    # Células internas
    for idx, rank in ranks.items():
        layers[rank].append(("cell", idx))

    def node_score(cell_idx):
        cell = cells[cell_idx]
        score = 0
        count = 0
        for pin_name, net_name in cell['conns']:
            if get_pin_side(pin_name) == "LEFT":
                # pega drivers (rank e posição do driver)
                for other_idx, other_r in ranks.items():
                    for p2, n2 in cells[other_idx]['conns']:
                        if n2 == net_name and get_pin_side(p2) == "RIGHT":
                            score += other_r
                            count += 1
        return score / count if count > 0 else 0

    # Pinos de entrada antes do rank 0
    for net, r in input_ranks.items():
        layers[r].append(("input", net))

    # Pinos de saída após o último rank
    for net, r in output_ranks.items():
        layers[r].append(("output", net))
        
    sorted_ranks = sorted(layers.keys())
    max_rank = sorted_ranks[-1] if sorted_ranks else 0
    print(f"[INFO] Circuito organizado em {max_rank + 1} camadas lógicas.")

    # Configurações de Espaçamento Visual
    COL_WIDTH = 500   # Espaço horizontal entre camadas
    ROW_HEIGHT = 400  # Espaço vertical entre células

    # --- ETAPA 2: Instanciação e Posicionamento Físico ---
    
    # Dicionário para guardar onde cada célula foi colocada fisicamente
    # cell_index -> (x, y, pin_mapping)
    placed_cells_info = {}

    for rank in sorted_ranks:
        cell_indices = sorted(
            layers[rank],
            key=lambda x: node_score(x[1]) if x[0] == "cell" else -9999
        )

        # Calcula X da camada
        layer_x = x_start + (rank * COL_WIDTH)
        
        # Centraliza verticalmente em relação ao y_start, ou começa do topo
        # Aqui vamos começar do topo e descer
        for i_in_layer, item in enumerate(cell_indices):
            kind, ref = item

            if kind == "cell":
                cell_idx = ref
                cell = cells[cell_idx]
            
            # (posicionamento das células permanece exatamente igual)
            elif kind == "input":
                net = ref
                layer_y = y_start + (i_in_layer * ROW_HEIGHT)
                layer_x = x_start + (rank * COL_WIDTH)
                builder.add_io_pin("ipin.sym", layer_x, layer_y, 0, f"in_{net}", net)
                continue

            elif kind == "output":
                net = ref
                layer_y = y_start + (i_in_layer * ROW_HEIGHT)
                layer_x = x_start + (rank * COL_WIDTH)
                builder.add_io_pin("opin.sym", layer_x, layer_y, 0, f"out_{net}", net)
                continue

            # Calcula Y na camada
            layer_y = y_start + (i_in_layer * ROW_HEIGHT)
            
            cell_type = cell['type']
            
            # 1. Validação da célula
            final_sym, final_type, substituted, reason = builder.resolve_cell_sym(
                cell_type=cell_type,
                sym_path=f"sky130_stdcells/{cell_type}.sym"
            )
            
            if substituted:
                # Opcional: print para debug, mas pode poluir muito se forem muitas células
                # print(f"[INFO] Célula '{cell_type}' substituída por '{final_type}'")
                pass
            
            # 2. Mapeamento de Pinos para Substituições (ex: buf_1)
            pin_mapping = {}
            non_power_pins = []
            for pin_name, net_name in cell['conns']:
                if pin_name not in ['VGND', 'VNB', 'VPB', 'VPWR']:
                    non_power_pins.append(pin_name)
            
            if substituted and final_type == "buf_1" and len(non_power_pins) == 2:
                pin_mapping[non_power_pins[0]] = 'A'
                pin_mapping[non_power_pins[1]] = 'X'
            
            # 3. Adiciona a instância no Builder
            builder.add_instance(
                sym_path=final_sym,
                x=layer_x,
                y=layer_y,
                rotation=0,
                name=cell['name'],
                cell_type=final_type
            )
            
            # Guarda info para uso posterior se necessário
            placed_cells_info[cell_idx] = {
                'x': layer_x, 
                'y': layer_y, 
                'final_type': final_type,
                'pin_mapping': pin_mapping
            }

            # 4. Conexão dos pinos (Fiação Local)
            # Busca métricas
            cell_metrics = CELL_DB.get(final_type, {})
            
            for pin_name, net_name in cell['conns']:
                # Ignora pinos de alimentação
                if pin_name in ['VGND', 'VNB', 'VPB', 'VPWR']:
                    continue
                
                # Nome real do pino
                actual_pin_name = pin_mapping.get(pin_name, pin_name)
                
                # Métricas geométricas do pino
                dy, dx_off = cell_metrics.get(actual_pin_name, (0, 60))
                
                yp = layer_y + dy
                side = get_pin_side(actual_pin_name)
                
                if side == "LEFT":
                    xp_pin = layer_x - dx_off
                    
                    # Se for conectado diretamente a uma Entrada Global, desenha o pino de IO
                    if net_name in inputs:
                        builder.add_wire(xp_pin - 100, yp, xp_pin, yp, net_name)
                        builder.add_io_pin("ipin.sym", xp_pin - 100, yp, 0, f"in_{net_name}_{cell_idx}", net_name)
                    else:
                        # Toco de fio para indicar conexão
                        builder.add_wire(xp_pin - 30, yp, xp_pin, yp, net_name)
                
                else:  # RIGHT
                    xp_pin = layer_x + dx_off
                    
                    # Se for conectado diretamente a uma Saída Global, desenha o pino de IO
                    if net_name in outputs:
                        builder.add_wire(xp_pin, yp, xp_pin + 100, yp, net_name)
                        builder.add_io_pin("opin.sym", xp_pin + 100, yp, 0, f"out_{net_name}_{cell_idx}", net_name)
                    else:
                        # Toco de fio para indicar conexão
                        builder.add_wire(xp_pin, yp, xp_pin + 30, yp, net_name)

    # =========================================================================
    # ETAPA FINAL: CRIAÇÃO DOS PINOS GLOBAIS DE I/O QUE NÃO FORAM GERADOS NOS STUBS
    # =========================================================================

    # Determinar os limites X reais das células posicionadas
    all_x = [info['x'] for info in placed_cells_info.values()]
    if all_x:
        min_x = min(all_x)
        max_x = max(all_x)
    else:
        min_x = x_start
        max_x = x_start + 500

    # ---------------------------
    # Criar pinos de entrada (inputs)
    # ---------------------------
    input_y_offset = 0

    for net in inputs:
        # Checar se já foi criado automaticamente no stub LEFT
        already = False
        for idx, cell in enumerate(cells):
            for pin_name, net_name in cell['conns']:
                if net_name == net and get_pin_side(pin_name) == "LEFT":
                    already = True
                    break
            if already:
                break

        if not already:
            y_pin = y_start + input_y_offset
            input_y_offset += 200

            x_pin = min_x - 300
            builder.add_io_pin("ipin.sym", x_pin, y_pin, 0, f"in_{net}", net)
            builder.add_wire(x_pin + 100, y_pin, x_pin, y_pin, net)

    # ---------------------------
    # Criar pinos de saída (outputs)
    # ---------------------------
    output_y_offset = 0

    for net in outputs:
        # Checar se já foi criado automaticamente no stub RIGHT
        already = False
        for idx, cell in enumerate(cells):
            for pin_name, net_name in cell['conns']:
                if net_name == net and get_pin_side(pin_name) == "RIGHT":
                    already = True
                    break
            if already:
                break

        if not already:
            y_pin = y_start + output_y_offset
            output_y_offset += 200

            x_pin = max_x + 300
            builder.add_io_pin("opin.sym", x_pin, y_pin, 0, f"out_{net}", net)
            builder.add_wire(x_pin - 100, y_pin, x_pin, y_pin, net)
