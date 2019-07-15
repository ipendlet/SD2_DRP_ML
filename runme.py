"""ESCALATE Capture

Main point of entry for for EscalateCAPTURE
"""

import os
import sys
import ast
import xlrd
import logging
import argparse as ap

from log import init
from capture import specify
from capture import devconfig
from utils import globals


def escalatecapture(rxndict, vardict):
    """Point of entry into the data pipeline

    Manages processing calls to specify, generate, and prepare --> leads to execute

    :param rxndict: dictionary of Excel-specified params
    :param vardict: dictionary of dev-specified params
    :return None:
    """
    modlog = logging.getLogger('capture.escalatecapture')
    modlog.info("Initializing specify")
    specify.datapipeline(rxndict, vardict)


def linkprocess(linkfile):
    """TODO: what was this going to be for?"""
    return


def build_rxndict(rxnvarfile):
    """Read Template file and return a dict representation

    The rxndict is a mapping of Variables => Values (column B => column d) in the
    uncommented rows of the reaction excel file

    :param rxnvarfile: path to excel file containing reaction specification
    :return rxndict: dictionary representation of reaction specification
    """
    rxndict = {}
    varfile = rxnvarfile
    wb = xlrd.open_workbook(varfile)
    sheet = wb.sheet_by_name('WF1')
    for i in range(sheet.nrows):
        commentval = sheet.cell(i, 0).value
        if commentval == '#':
            continue
        else:
            cell_dict_value = sheet.cell(i, 3).value
            cell_dict_id = sheet.cell(i, 1).value
            cell_dict_type = sheet.cell(i, 4).value
            if cell_dict_id == "":
                pass
            if cell_dict_type == 'list':
                rxndict[cell_dict_id] = ast.literal_eval(cell_dict_value)
            else:
                rxndict[cell_dict_id.strip()] = cell_dict_value
    return rxndict


if __name__ == "__main__":

    parser = ap.ArgumentParser(description='Generate experimental run data')
    parser.add_argument('Variables', type=str,
        help='Target xls file containing run information specified by the user\
             format should be "filename.xlsx"') 
    parser.add_argument('-s', '--ss', default=0, type=int, choices=[0, 1, 2],
        help='0 - quasi-random experiments generate, 1 - Generates stateset\
             for exp_1 user specified reagents, 2 - generate prototype run for\
             exp_1 user specified reagents') 
    parser.add_argument('-d', '--debug', default=0, type=int, choices=[0, 1],
        help='0 - complete run generation and upload to google drive,\
             1 - local debugging with no data upload,')

    args = parser.parse_args()
    challengeproblem = args.ss
    debug = args.debug

    # vardict will hold variables configured by developers
    vardict = {}

    vardict['exefilename'] = args.Variables
    vardict['max_robot_reagents'] = devconfig.max_robot_reagents
    vardict['RoboVersion'] = devconfig.RoboVersion
    vardict['challengeproblem'] = challengeproblem
    vardict['debug'] = debug
    vardict['volspacing'] = devconfig.volspacing
    vardict['maxreagentchemicals'] = devconfig.maxreagentchemicals
    vardict['solventlist'] = devconfig.solventlist

    vardict['lab_vars'] = devconfig.lab_vars
    # rxndict will hold variables specified in the Excel interface
    # see build_rxndict docs for a more detailed discussion.
    rxndict = build_rxndict(vardict['exefilename'])
    rxndict['challengeproblem'] = challengeproblem

    # TODO these interdependencies are sloppy, separate concerns
    # >>> also, what is lab? I'm not sure what this label is referencing...
    #  It is reference which lab is this experiment going to be run at. LBL, HC, etc.
    vardict['filereqs'] = devconfig.labfiles(rxndict['lab'])

    globals.set_lab(rxndict['lab'])

    # TODO dicts can be modified in place
    rxndict, vardict = init.runuidgen(rxndict, vardict) 

    loggerfile = init.buildlogger(rxndict)
    rxndict['logfile'] = loggerfile  # TODO stick this in rxndict inside of buildlogger

    # log the initial state of the run
    init.initialize(rxndict, vardict)

    # TODO: >>>> insert variable tests here <<<<

    escalatecapture(rxndict, vardict)
