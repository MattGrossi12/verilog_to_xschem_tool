def render(builder, cells_processed, inputs, outputs, x_start):
    """Gera a representação visual baseada em labels e stubs."""
    for cell in cells_processed:
        x_gate, y_gate = cell['pos']
        for pin in cell['pins']:
            xp_pin, yp = pin['coord']
            net_name = pin['net']
            side = pin['side']
            
            if side == "LEFT":
                if net_name in inputs:
                    # Conexão Global de Entrada
                    builder.add_wire(x_gate - 150, yp, xp_pin, yp, net_name)
                    builder.add_io_pin("ipin.sym", x_gate - 150, yp, 0, f"in_{net_name}_{cell['id']}", net_name)
                else:
                    # Conexão Interna (Stub curto)
                    builder.add_wire(xp_pin - 30, yp, xp_pin, yp, net_name)
            else:
                if net_name in outputs:
                    # Conexão Global de Saída
                    builder.add_wire(xp_pin, yp, x_gate + 150, yp, net_name)
                    builder.add_io_pin("opin.sym", x_gate + 150, yp, 0, f"out_{net_name}_{cell['id']}", net_name)
                else:
                    # Conexão Interna (Stub curto)
                    builder.add_wire(xp_pin, yp, xp_pin + 30, yp, net_name)