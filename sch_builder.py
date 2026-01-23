import os
from sky130_db import CELL_DB  # verificação de células

class SchBuilder:

    # ------------------------------------------------------------
    # Resolve nome da célula → sym válido
    # ------------------------------------------------------------
    def resolve_cell_sym(self, cell_type=None, sym_path=None):
        """
        Retorna:
            (final_sym_path, final_cell_type, substituted_flag, reason)
        """

        # 1) escolha preferencial: cell_type
        if cell_type:
            key = cell_type
        else:
            # extrair do sym_path se possível
            if sym_path:
                key = os.path.splitext(os.path.basename(sym_path))[0]
            else:
                key = None

        # se nada foi passado → buf_1
        if not key:
            return "sky130_stdcells/buf_1.sym", "buf_1", True, "no cell_type or sym_path provided"

        # 2) verificação direta no CELL_DB
        if key in CELL_DB:
            final_sym = sym_path if sym_path else f"sky130_stdcells/{key}.sym"
            return final_sym, key, False, ""

        # 3) tentar strip de prefixo do PDK
        if key.startswith("sky130_fd_sc_hd__"):
            stripped = key.replace("sky130_fd_sc_hd__", "")
            if stripped in CELL_DB:
                final_sym = f"sky130_stdcells/{stripped}.sym"
                return final_sym, stripped, False, "stripped pdk prefix"

        # 4) tentar substring match
        for candidate in CELL_DB.keys():
            if candidate == key:
                return f"sky130_stdcells/{candidate}.sym", candidate, False, ""
            if candidate in key or key in candidate:
                return f"sky130_stdcells/{candidate}.sym", candidate, False, "substring match"

        # fallback → buf_1
        return "sky130_stdcells/buf_1.sym", "buf_1", True, f"no match for '{key}'"


    # ------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------
    def __init__(self, version="3.4.8RC"):
        self.lines = [
            f"v {{xschem version={version} file_version=1.3}}",
            "G {}", "K {}", "V {}", "S {}", "F {}", "E {}", ""
        ]
        self.missing_cells = []


    # ------------------------------------------------------------
    # Adicionar instância
    # ------------------------------------------------------------
    def add_instance(self, sym_path, x, y, rotation, name, cell_type=None, extra_attrs=""):
        """
        cell_type é opcional: se for passado, preferido; se não for, extraído do sym_path.
        """

        # chamar método interno
        final_sym, final_type, substituted, reason = self.resolve_cell_sym(cell_type, sym_path)

        # registrar substituições
        if substituted:
            msg = f"[WARN] inst '{name}': '{cell_type or sym_path}' não encontrada → buf_1 ({reason})"
            print(msg)
            self.missing_cells.append((name, cell_type or sym_path, final_type, reason))

        base_attr = (
            f"name={name} VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__"
        )
        full_attr = f"{base_attr} {extra_attrs}".strip()

        self.lines.append(
            f"C {{{final_sym}}} {x} {y} {rotation} 0 {{{full_attr}}}"
        )


    # ------------------------------------------------------------
    # Fios
    # ------------------------------------------------------------
    def add_wire(self, x1, y1, x2, y2, label=None):
        line = f"N {x1} {y1} {x2} {y2} "
        line += f"{{lab={label}}}" if label else "{}"
        self.lines.append(line)


    # ------------------------------------------------------------
    # IO pins
    # ------------------------------------------------------------
    def add_io_pin(self, sym_path, x, y, rotation, name, label):
        self.lines.append(
            f"C {{{sym_path}}} {x} {y} {rotation} 0 {{name={name} lab={label}}}"
        )


    # ------------------------------------------------------------
    # Escrita final
    # ------------------------------------------------------------
    def get_content(self):
        return "\n".join(self.lines)