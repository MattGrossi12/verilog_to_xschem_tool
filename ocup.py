import math

def generate_occupation_matrix(cells, x_base, y_step, x_step, max_rows):
    lines = []
    for i, cell in enumerate(cells):
        col = i // max_rows
        row = i % max_rows
        x = x_base + (col * x_step)
        y = row * y_step
        
        attr = f"name={cell['name']} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__"
        lines.append(f"C {{sky130_stdcells/{cell['type']}.sym}} {x} {y} 0 0 {{{attr}}}")
    
    num_cols = math.ceil(len(cells) / max_rows) if cells else 0
    return lines, num_cols