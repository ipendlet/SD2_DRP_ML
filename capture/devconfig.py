# devconfig.py

#version control
RoboVersion = 2.4

# Hard coded limits
max_robot_reagents = 7
maxreagentchemicals = 3
volspacing = 10 #reagent microliter (uL) spacing between points in the stateset 


# perovskite solvent list (simple specification of what is a liquid)
# assumes only 1 liquid / reagent
solventlist = ['GBL', 'DMSO', 'DMF', 'FAH', 'DCM'] #ya, I know FAH isn't a solvent, but it makes programming easier

# lab file requirements list

# Gdrive target folder for rendering
template_folder = '1PVeVpNjnXiAuzm3Oq2q-RiiLBhKPGW53'
targetfolder = '1tUb4GcF_tDanMjvQuPa6vj0n9RNa5IDI' #target folder for run generation
chemsheetid = "1htERouQUD7WR2oD-8a3KhcBpadl0kWmbipG0EFDnpcI"
chem_workbook_index = 0
reagentsheetid = "1htERouQUD7WR2oD-8a3KhcBpadl0kWmbipG0EFDnpcI"
reagent_workbook_index = 1
reagent_interface_amount_startrow = 15

def labfiles(lab):
    if lab == "LBL" or lab == "HC":
        filereq = ['CrystalScoring','ExpDataEntry','metadata.json']
    if lab == 'ECL':
        filereq = ['CrystalScoring','metadata.json']
    return(filereq)


