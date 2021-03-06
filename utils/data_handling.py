"""Useful stuff that has no proper home
"""
import pandas as pd
from pandas.core.indexing import IndexingError
import logging
import re

import capture.devconfig as config
from utils import globals
from utils.globals import lab_safeget

modlog = logging.getLogger(__name__)

def get_explicit_experiments(rxnvarfile, only_volumes=True):
    """Extract reagent volumes for the manually specified experiments, if there are any.

    :param rxnvarfile: the Template
    :param only_volumes: only return the experiment Reagent volumes
    :return:
    """
    explicit_experiments = pd.read_excel(io=rxnvarfile, sheet_name='ManualExps')
    # remove empty rows:
    explicit_experiments = explicit_experiments[~explicit_experiments['Manual Well Number'].isna()]
    # remove unnused reagents:
    try:
        explicit_experiments = explicit_experiments.loc[:, explicit_experiments.sum() != 0]
    except IndexingError:
        modlog.error('Manual runs not fully specified. Please be sure to fully enumerate all desired runs and fill empties with "0"')
        import sys
        sys.exit()

    if only_volumes:
        explicit_experiments = explicit_experiments.filter(regex='Reagent\d \(ul\)').astype(int)

    return explicit_experiments


def get_reagent_number_as_string(reagent_str):
    """Get the number from a string representation"""
    reagent_alias = lab_safeget(config.lab_vars, globals.get_lab(), 'reagent_alias')
    reagent_pat = re.compile('([Rr]eagent|{})(\d+)'.format(reagent_alias))
    return reagent_pat.match(reagent_str).group(2)


def abstract_reagent_colnames(df, inplace=True):
    """Replace instances of 'Reagent' with devconfig.REAGENT_ALIAS

    :param df: dataframe to rename
    :return: None or pandas.DataFrame (depending on inplace)
    """
    reagent_alias = lab_safeget(config.lab_vars, globals.get_lab(), 'reagent_alias')
    result = df.rename(columns=lambda x: re.sub('[Rr]eagent', reagent_alias, x), inplace=inplace)
    return result


def flatten(L):
    """Flatten a list recursively

    Inspired by this fun discussion: https://stackoverflow.com/questions/12472338/flattening-a-list-recursively

    np.array.flatten did not work for irregular arrays
    and itertools.chain.from_iterable cannot handle arbitrarily nested lists

    :param L: A list to flatten
    :return: the flattened list
    """
    if L == []:
        return L
    if isinstance(L[0], list):
        return flatten(L[0]) + flatten(L[1:])
    return L[:1] + flatten(L[1:])


def update_sheet_column(sheet, data, col_index, start_row):
    """
    :param sheet: the gsheet object to update
    :param data: iterable of values to place in sheet, starting at (col_index, start_row)
    :param col_index: A sheet column header in [A, B, ..., AA, AB, ...]
    :param start_row: index of the row at which to begin updating sheet
    :return: None
    """

    stop_row = len(data) + start_row - 1
    range_spec = '{col:s}{start:d}:{col:s}{stop:d}'.format(col=col_index, start=start_row, stop=stop_row)
    col = sheet.range(range_spec)
    for i, cell in enumerate(col):
        cell.value = data[i]

    sheet.update_cells(col)
    return


def build_experiment_names_df(rxndict, vardict):
    experiment_names = []
    for exp_i in range(1, rxndict['totalexperiments'] + 1):
        experiment_names.extend(
            [rxndict.get('exp{i}_name'.format(i=exp_i),
                         'Experiment {i}'.format(i=exp_i))
            ] * int(rxndict['exp{i}_wells'.format(i=exp_i)])
        )

    if rxndict['manual_wells']:
        explicit_experiments = get_explicit_experiments(vardict['exefilename'], only_volumes=False)
        experiment_names.extend(explicit_experiments['Manual Well Custom ID'].values.tolist())

    return pd.DataFrame({'Experiment Names': experiment_names})


def get_user_actions(rxndict, sheet):
    """We are EXPLICITLY EXTRACTING the user actions here. These numbers were gotten be examining the sheet object.
    If we are adding future actions, they each need to be of the form:

    userActions[n] = {sheet.cell(cellIndex_(n-1) + 1, 1).value: sheet.cell(cellIndex_(n-1) + 1, 3).value}

    Each action should be in its own subdict. This is so that we save both the key (which is the string user action
    and the value. Then, go update experiment_interface.generate_experiment_specification_file such that
    we add in the new k/v pairs as is done in that file.

    :param rxndict:
    :param sheet: excel sheet object
    :return:
    """
    userActions = {}
    userActions[0] = {sheet.cell(107, 3).value: sheet.cell(106, 3).value}
    userActions[1] = {sheet.cell(109, 3).value: sheet.cell(108, 3).value}
    # add new userActions here.

    rxndict['user_actions'] = userActions


def get_used_reagent_nums(rxndict):
    expoverviews = [rxndict[k] for k in rxndict.keys() if re.match('^exp\d+$', k)]
    return flatten(expoverviews)