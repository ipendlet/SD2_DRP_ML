import pandas as pd
import numpy as np
import logging
import sys

modlog = logging.getLogger('capture.prepare.experiment_model_out')

#Defines what type of liquid class sample handler (pipette) will be needed for the run, these are hardcoded to the robot
def volarray(rdf, maxr):
    hv='HighVolume_Water_DispenseJet_Empty'
    sv='StandardVolume_Water_DispenseJet_Empty'
    lv='Tip_50ul_Water_DispenseJet_Empty'
    x=1
    vol_ar=[]
    while x <= maxr:
        name_maxvol=(rdf.loc[:,"Reagent%i (ul)" %(x)]).max()
        if name_maxvol >= 300:
            vol_ar.append(hv)
        elif name_maxvol >= 50 and name_maxvol <300:
            vol_ar.append(sv)
        elif name_maxvol < 50:
            vol_ar.append(lv)
        x+=1
    return(vol_ar)

def ecl_liquid(rdict):
    reagent_lc_list=[]
    reagentcount = 1
    eclpipette_model = 'Model[Method, Pipetting, "StandardVolume_GBL_DispenseJet_Empty"]'
    #make a reagent list for export to the ECL dataframe
    for reagentname,v in rdict.items():
        reagentnameint = int(reagentname) 
        while reagentnameint > reagentcount:
            reagent_lc_list.append('null')
            reagentcount+=1
        reagent_lc_list.append(eclpipette_model)
        modlog.info('user specified %s pipette model of %s' %(reagentname, eclpipette_model))
        reagentcount+=1
    return(reagent_lc_list)

def ecl_temp(rdict):
    reagent_temp_list=[]
    reagentcount = 1
    #make a reagent list for export to the ECL dataframe
    for reagentname,reagentobject in rdict.items():
        reagentnameint = int(reagentname) 
        while reagentnameint > reagentcount:
            reagent_temp_list.append('null')
            reagentcount+=1
        reagent_temp_list.append(reagentobject.prerxntemp)
        modlog.info('user specified %s for transport warmed of %s' %(reagentname, reagentobject.prerxntemp))
        reagentcount+=1
    return(reagent_temp_list)

#Constructs well array information based on the total number of wells for the run
#Future versions could do better at controlling the specific location on the tray that reagents are dispensed.  This would be place to start
# that code overhaul
# will not work for workflow 3
def MakeWellList(platecontainer, wellcount):
    wellorder=['A', 'C', 'E', 'G', 'B', 'D', 'F', 'H'] #order is set by how the robot draws from the solvent wells
    VialList=[]
    welllimit=wellcount/8+1
    count=1
    while count<welllimit:
        for item in wellorder:
            countstr=str(count)
            Viallabel=item+countstr
            VialList.append(Viallabel)
        count+=1
    df_VialInfo=pd.DataFrame(VialList)
    df_VialInfo.columns=['Vial Site']
    df_VialInfo['Labware ID:']=platecontainer 
    df_VialInfo = df_VialInfo.truncate(after=(wellcount-1))
    return(df_VialInfo)

def MakeWellList_WF3(platecontainer, wellcount):
    wellorder=['A', 'C', 'E', 'G'] 
    wellorder2=['B', 'D', 'F', 'H'] 
    VialList=[]
    welllimit=wellcount/4+1
    count=1
    while count<welllimit:
        for item in wellorder:
            countstr=str(count)
            Viallabel=item+countstr
            VialList.append(Viallabel)
        count+=1
        for item in wellorder2:
            countstr=str(count)
            Viallabel=item+countstr
            VialList.append(Viallabel)
        count+=1
    df_VialInfo=pd.DataFrame(VialList)
    df_VialInfo.columns=['Vial Site']
    df_VialInfo['Labware ID:']=platecontainer 
    df_VialInfo = df_VialInfo.truncate(after=(wellcount-1))
    return(df_VialInfo)

def WF3_split(erdf, splitreagents):
    new_rows = len(erdf)*2
    new_cols = len(erdf.columns)
    erdf_new = pd.DataFrame(np.zeros((new_rows, new_cols)), columns=erdf.columns)
    splitcols = []
    normalcols = []
    for column in erdf.columns:
        if any(item in column for item in splitreagents):
            splitcols.append(column)
        else:
            normalcols.append(column)
    count = 0
    count2 = 0
    erdf_normals = erdf[normalcols]
    erdf_splits = erdf[splitcols]
    for index, row in erdf.iterrows():
        erdf_new.loc[count2] = erdf_normals.loc[index]
        erdf_new.loc[count2+4] = erdf_splits.loc[index]
        count2 +=1
        count+=1
        if count == 4:
            count2+=4
            count=0
    erdf_new2 = (erdf_new.fillna(value=0))
    return erdf_new2


def cleanvolarray(erdf, maxr):
    ''' converts reagent volume dataframe to returns dataframe compatible with max reagents supported by nimbus4

    takes the reagent volume dataframe along with the max supported reagents (set in the developer variables) and 
    converts the reagent volume dataframe to nimbus4 formatted volume entry specifically including blank rows where 
    no reagent was specified.
    '''
    columnlist = []
    templatelst = [0]*(len(erdf.iloc[0:]))
    for column in erdf.columns:
        columnlist.append(column)
    count = 1
    newcolumnslist = []
    while count <= maxr:
        reagentname =('Reagent%s (ul)' %count)
        if reagentname not in columnlist:
            newcolumnslist.append(reagentname)
        else:
            pass
        count+=1
    for item in newcolumnslist:
        newdf = pd.DataFrame(templatelst)
        newdf.columns = [item]
        erdf = pd.concat([erdf, newdf], axis=1, sort=True)
    erdf = erdf.reindex(sorted(erdf.columns), axis=1)
    return erdf

def LBLrobotfile(rxndict, vardict, erdf):
    ''' Generate a robotic file of the proper format for LBL

    erdf should contain the experimental reaction data frame which consists of the volumes of each
    reagent in each experiment to be performed.  The rxndict and vardict should be identical to what was
    created in the original input files.  
    '''
    vol_ar=volarray(erdf, vardict['max_robot_reagents'])
    Parameters={
    'Reaction Parameters':['Temperature (C):','Stir Rate (rpm):','Mixing time1 (s):','Mixing time2 (s):', 'Reaction time (s):',""], 
    'Parameter Values':[rxndict['temperature2_nominal'], rxndict['stirrate'], rxndict['duratation_stir1'], rxndict['duratation_stir2'], rxndict['duration_reaction'] ,''],
    }
    Conditions={
    'Reagents':['Reagent1', "Reagent2", "Reagent3", "Reagent4",'Reagent5','Reagent6','Reagent7'],
    'Reagent identity':['1', "2", "3", "4",'5','6','7'],
    'Liquid Class':vol_ar,
    'Reagent Temperature':[rxndict['reagents_prerxn_temperature']]*len(vol_ar)}
    df_parameters=pd.DataFrame(data=Parameters)
    df_conditions=pd.DataFrame(data=Conditions)
    robotfiles = []
    if rxndict['ExpWorkflowVer'] == 3:
        # For WF3 tray implementation to work
        df_Tray2=MakeWellList_WF3(rxndict['plate_container'], rxndict['wellcount']*2)
        erdf_new = WF3_split(erdf,rxndict['exp1_split'])
        outframe1=pd.concat([df_Tray2.iloc[:,0],erdf_new,df_Tray2.iloc[:,1],df_parameters, df_conditions], sort=False, axis=1)
        robotfile = ("localfiles/%s_RUNME_RobotFile.xls" %rxndict['RunID'])
        ## For report code to work
        df_Tray=MakeWellList(rxndict['plate_container'], rxndict['wellcount']*1)
        outframe2=pd.concat([df_Tray.iloc[:,0],erdf,df_Tray.iloc[:,1],df_parameters, df_conditions], sort=False, axis=1)
        robotfile2 = ("localfiles/%s_RobotInput.xls" %rxndict['RunID'])
        outframe1.to_excel(robotfile, sheet_name='NIMBUS_reaction', index=False)
        outframe2.to_excel(robotfile2, sheet_name='NIMBUS_reaction', index=False)
        robotfiles.append(robotfile)
        robotfiles.append(robotfile2)
    else:
        df_Tray=MakeWellList(rxndict['plate_container'], rxndict['wellcount']*1)
        outframe=pd.concat([df_Tray.iloc[:,0],erdf,df_Tray.iloc[:,1],df_parameters, df_conditions], sort=False, axis=1)
        robotfile = ("localfiles/%s_RobotInput.xls" %rxndict['RunID'])
        robotfiles.append(robotfile)
        outframe.to_excel(robotfile, sheet_name='NIMBUS_reaction', index=False)
    return(robotfiles) 

def reagent_id_list(rxndict):
    reagentidlist=[]
    reagentcount = 1
    #make a reagent list for export to the ECL dataframe
    for reagentidname,v in rxndict.items():
        if 'Reagent' in reagentidname and "_ID" in reagentidname:
            reagentnum = int(reagentidname.split('_')[0].split('t')[1]) # Reagent1_ID --> 1
            while reagentnum > reagentcount:
                reagentidlist.append('null')
                reagentcount+=1
            reagentidlist.append(v)
            reagentcount+=1
    return(reagentidlist)

def ECLrobotfile(rxndict, vardict, rdict, erdf):
    ''' Generate experiment file for ECL

    Reagent identity in rxndict must be specified as and ECL model ID
    '''
    df_Tray=MakeWellList(rxndict['plate_container'], rxndict['wellcount'])
    Parameters={
    'Reaction Parameters':['Temperature (C):','Stir Rate (rpm):','Mixing time1 (s):','Mixing time2 (s):', 'Reaction time (s):',""], 
    'Parameter Values':[rxndict['temperature2_nominal'], rxndict['stirrate'], rxndict['duratation_stir1'], rxndict['duratation_stir2'], rxndict['duration_reaction'] ,''],
    }
    Conditions={
    'Reagents':['Reagent1', "Reagent2", "Reagent3", "Reagent4",'Reagent5','Reagent6','Reagent7'],
    'Reagent identity':reagent_id_list(rxndict),
    'Liquid Class':ecl_liquid(rdict),
    'Reagent Temperature':ecl_temp(rdict)}
    df_parameters=pd.DataFrame(data=Parameters)
    df_conditions=pd.DataFrame(data=Conditions)
    outframe=pd.concat([df_Tray.iloc[:,0],erdf,df_Tray.iloc[:,1],df_parameters, df_conditions], sort=False, axis=1)
    robotfile = ("localfiles/%s_RobotInput.xls" %rxndict['RunID'])
    outframe.to_excel(robotfile, sheet_name='NIMBUS_reaction', index=False)
    return(robotfile) 