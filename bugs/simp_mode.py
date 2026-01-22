def render(builder, net_map, inputs, outputs, x_start, y_start):
    for net_name, coords in net_map.items():
        driver, receivers = coords['driver'], coords['receivers']

        if net_name in inputs:
            # Entrada global próxima à primeira célula que a usa
            y_base = receivers[0][1] if receivers else y_start
            builder.add_io_pin("ipin.sym", x_start - 300, y_base, 0, f"in_{net_name}", net_name)
            for rx_x, rx_y in receivers:
                builder.add_wire(x_start - 300, y_base, rx_x, rx_y, net_name)

        elif driver and receivers:
            # Cria o "cotovelo" da conexão (Manhattan routing)
            # O canal de desvio é relativo à saída do driver
            x_mid = driver[0] + 100 
            builder.add_wire(driver[0], driver[1], x_mid, driver[1], net_name)
            for rx_x, rx_y in receivers:
                builder.add_wire(x_mid, driver[1], x_mid, rx_y, net_name) # Vertical
                builder.add_wire(x_mid, rx_y, rx_x, rx_y, net_name) # Horizontal final

        if net_name in outputs and driver:
            builder.add_wire(driver[0], driver[1], driver[0] + 200, driver[1], net_name)
            builder.add_io_pin("opin.sym", driver[0] + 200, driver[1], 0, f"out_{net_name}", net_name)