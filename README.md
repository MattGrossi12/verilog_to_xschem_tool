# verilog_to_xschem_tool
Uma ferramenta de código aberto para transdução de netlist baseada em sky130 para uso em diagramas xschem, permitindo assim o uso de arquivos de pós-síntese abertos, originários do librelane/openlane, para realizar uma simulação AMS.


Pontos importantes:

No período presente o pdk sk130 é feito com o uso de células:

sky130_ef_sc_hd__decap_20_12
sky130_ef_sc_hd__decap_40_12
sky130_ef_sc_hd__decap_60_12
sky130_ef_sc_hd__decap_80_12

Em substituição as clássicas sky130_ef_sc_hd__decap_12, por motivos que podem ser listados no link abaixo.

https://github.com/RTimothyEdwards/open_pdks/issues/490

Entretanto a lib presente no xschem não possui as células decap_20, 40, 60 e 80, sendo assim, no processo de sparser são automaticamente convertidas nas clássicas decap_12, para que possa ser possível a simulação no xschem.
