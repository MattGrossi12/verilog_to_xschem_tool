# verilog_to_xschem_tool
Uma ferramenta para transdução de netlist baseada em sky130 para uso em diagramas xschem, permitindo assim o uso de arquivos de pós-síntese abertos, originários do librelane/openlane, para realizar uma simulação AMS.


Pontos importantes:

No período presente o pdk sk130 é feito com o uso de células:

sky130_ef_sc_hd__decap_20_12
sky130_ef_sc_hd__decap_40_12
sky130_ef_sc_hd__decap_60_12
sky130_ef_sc_hd__decap_80_12

Em substituição as clássicas sky130_ef_sc_hd__decap_12, por motivos que podem ser listados no link abaixo.

https://github.com/RTimothyEdwards/open_pdks/issues/490

Entretanto a lib presente no xschem não possui as células decap_20, 40, 60 e 80, sendo assim, no processo de sparser são automaticamente convertidas nas clássicas decap_12, para que possa ser possível a simulação no xschem.

A ferramenta é possui essa estrutura:

```bash
o 1º é um sparser que lê uma netlist.nl.v pós síntese e remove


o 2º Possui a capacidade de converter células que não possuem comportament lógico, como as decap e fill, convertendo-as e moldando-as no esquemático em forma de matriz, abaixo do diagrama principal.

o 3º Possui a capacidade de converter as células que implementam comportamento funcional, como portas lógicas, buffers, flip-flops, mux e afins.

o 4º É um banco contendo as medidas internas dos .sym de todos os itens da biblioteca digital do pdk, permitindo assim que as conexões sejam feitas de forma automatizada, vale ressaltar que, o modelo presente se baseia em células nl, portanto, sem pinos de alimentação.
