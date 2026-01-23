class SchBuilder:
    def __init__(self, version="3.4.8RC"):
        self.lines = [
            f"v {{xschem version={version} file_version=1.3}}",
            "G {}", "K {}", "V {}", "S {}", "F {}", "E {}", ""
        ]

    def add_instance(self, sym_path, x, y, rotation, name, cell_type, extra_attrs=""):
        """Adiciona uma célula sky130 com os atributos padrão de alimentação."""
        base_attr = f"name={name} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__"
        full_attr = f"{base_attr} {extra_attrs}".strip()
        self.lines.append(f"C {{{sym_path}}} {x} {y} {rotation} 0 {{{full_attr}}}")

    def add_wire(self, x1, y1, x2, y2, label=None):
        """Desenha um fio (net) no esquemático."""
        line = f"N {x1} {y1} {x2} {y2} "
        line += f"{{lab={label}}}" if label else "{}"
        self.lines.append(line)

    def add_io_pin(self, sym_path, x, y, rotation, name, label):
        """Adiciona ipin.sym ou opin.sym para entradas e saídas."""
        self.lines.append(f"C {{{sym_path}}} {x} {y} {rotation} 0 {{name={name} lab={label}}}")

    def get_content(self):
        return "\n".join(self.lines)