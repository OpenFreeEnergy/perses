import numpy as np
import yaml
from perses.analysis import Analysis
import glob

def collect_file_conditions(experiment_directory):
    """
    Collect the experiment files for each condition of phase, ncmc steps, sterics, and geometry intervals.
    This assumes there is one output for each experimental condition.

    Parameters
    ----------
    experiment_directory : str
        The path to where the experiments were conducted

    Returns
    -------
    condition_files : dict of tuple: str
        The filename for each condition
    """
    condition_files = {}
    yaml_filenames = glob.glob(experiment_directory)
    for filename in yaml_filenames:
        with open(filename, 'r') as yamlfile:
            experiment_options = yaml.load(yamlfile)
            phase = "explicit" if experiment_options['phase'] == "solvent" else "vacuum"
            data_filename = experiment_options['output_filename']
            ncmc_length = experiment_options['ncmc_switching_times'][phase]
            sterics = experiment_options['use_sterics'][phase]
            geometry_intervals = experiment_options['geometry_divisions'][phase]

            condition_files[(phase, ncmc_length, sterics, geometry_intervals)] = data_filename

    return condition_files

def collect_logP_accept(condition_files):
    """
    Given a set of files specifying conditions, extract the logP_accept of each and store in a data structure

    Parameters
    ----------
    condition_files : dict of tuple: str
        Should have the format (phase, ncmc_length, sterics, geometry_intervals) : filename

    Returns
    -------
    logP_accept_conditions: dict of tuple: np.array
        the logP_accept (minus sams weights) for each set of conditions
    """
    logP_accept_conditions = {}
    for condition, filename in condition_files.items():
        try:
            analyzer = Analysis(filename)
            logP_without_sams = analyzer.extract_logP_values(condition[0], "logP_accept", subtract_sams=True)
            logPs_flat_list = []
            for value in logP_without_sams.values():
                logPs_flat_list.extend(value)
            logP_array = np.array(logPs_flat_list)
            logP_accept_conditions[condition] = logP_array
        except Exception as e:
            print(str(e))
            print("Unable to process {}".format(filename))
            continue

    return logP_accept_conditions