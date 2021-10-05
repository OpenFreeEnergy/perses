"""
CLI utility to automatically run benchmarks using data from the open force field protein-ligand benchmark at
https://github.com/openforcefield/protein-ligand-benchmark

It requires internet connection to function properly, by connecting to the mentioned repository.
"""
# TODO: Use plbenchmarks when conda package is available.

import argparse
import os
import urllib.request
import yaml


# global variables
base_repo_url = "https://github.com/openforcefield/protein-ligand-benchmark"


# helper functions
def concatenate_files(input_files, output_file):
    """
    Concatenate files given in input_files iterator into output_file.
    """
    with open(output_file, 'w') as outfile:
        for filename in input_files:
            with open(filename) as infile:
                for line in infile:
                    outfile.write(line)


def run_relative_perturbation(lig_a_idx, lig_b_idx, tidy=True):
    """
    Perform relative free energy simulation using perses CLI.

    Parameters
    ----------
        lig_a_idx : int
            Index for first ligand (ligand A)
        lig_b_idx : int
            Index for second ligand (ligand B)
        tidy : bool, optional
            remove auto-generated yaml files.

    Expects the target/protein pdb file in the same directory to be called 'target.pdb', and ligands file
    to be called 'ligands.sdf'.
    """
    print(f'Starting relative calculation of ligand {lig_a_idx} to {lig_b_idx}')
    trajectory_directory = f'out_{lig_a_idx}_{lig_b_idx}'
    new_yaml = f'relative_{lig_a_idx}_{lig_b_idx}.yaml'

    # generate yaml file
    # TODO: template.yaml file is configured for Tyk2, check if the same options work for others.
    with open(f'template.yaml', "r") as yaml_file:
        options = yaml.load(yaml_file, Loader=yaml.FullLoader)
    options['protein_pdb'] = 'target.pdb'
    options['ligand_file'] = 'ligands.sdf'
    options['old_ligand_index'] = lig_a_idx
    options['new_ligand_index'] = lig_b_idx
    options['trajectory_directory'] = f'{trajectory_directory}'
    with open(new_yaml, 'w') as outfile:
        yaml.dump(options, outfile)

    # run the simulation
    os.system(f'perses-relative {new_yaml}')

    print(f'Relative calculation of ligand {lig_a_idx} to {lig_b_idx} complete')

    if tidy:
        os.remove(new_yaml)


# Defining command line arguments
# fetching targets from github repo
# TODO: This part should be done using plbenchmarks API - once there is a conda pkg
targets_url = f"{base_repo_url}/raw/master/data/targets.yml"
with urllib.request.urlopen(targets_url) as response:
    targets_dict = yaml.safe_load(response.read())
# get the possible choices from targets yaml file
target_choices = targets_dict.keys()

arg_parser = argparse.ArgumentParser(description='CLI tool for running perses protein-ligand benchmarks.')
arg_parser.add_argument(
    "--target",
    type=str,
    help="Target biomolecule, use openff's plbenchmark names.",
    choices=target_choices,
    required=True
)
arg_parser.add_argument(
    "--edge",
    type=int,
    help="Edge index (0-based) according to edges yaml file in dataset. Ex. --edge 5 (for sixth edge)",
    required=True
)
args = arg_parser.parse_args()
target = args.target

# Fetch protein pdb file
# TODO: This part should be done using plbenchmarks API - once there is a conda pkg
target_dir = targets_dict[target]['dir']
pdb_url = f"{base_repo_url}/raw/master/data/{target_dir}/01_protein/crd/protein.pdb"
pdb_file, _ = urllib.request.urlretrieve(pdb_url)

# Fetch cofactors crystalwater pdb file
# TODO: This part should be done using plbenchmarks API - once there is a conda pkg
cofactors_url = f"{base_repo_url}/raw/master/data/{target_dir}/01_protein/crd/cofactors_crystalwater.pdb"
cofactors_file, _ = urllib.request.urlretrieve(cofactors_url)

# Concatenate protein with cofactors pdbs
concatenate_files((pdb_file, cofactors_file), 'target.pdb')

# Fetch ligands sdf files and concatenate them in one
# TODO: This part should be done using plbenchmarks API - once there is a conda pkg
ligands_url = f"{base_repo_url}/raw/master/data/{target_dir}/00_data/ligands.yml"
with urllib.request.urlopen(ligands_url) as response:
    ligands_dict = yaml.safe_load(response.read())
ligand_files = []
for ligand in ligands_dict.keys():
    ligand_url = f"{base_repo_url}/raw/master/data/{target_dir}/02_ligands/{ligand}/crd/{ligand}.sdf"
    ligand_file, _ = urllib.request.urlretrieve(ligand_url)
    ligand_files.append(ligand_file)
# concatenate sdfs
concatenate_files(ligand_files, 'ligands.sdf')

# run simulation
# fetch edges information
# TODO: This part should be done using plbenchmarks API - once there is a conda pkg
edges_url = f"{base_repo_url}/raw/master/data/{target_dir}/00_data/edges.yml"
with urllib.request.urlopen(edges_url) as response:
    edges_dict = yaml.safe_load(response.read())
edges_list = list(edges_dict.values())  # suscriptable edges object - note dicts are ordered for py>=3.7
# edge list to access by index
edge_index = args.edge  # read from cli arguments
edge = edges_list[edge_index]
ligand_a_name = edge['ligand_a']
ligand_b_name = edge['ligand_b']
# ligands list to get indices -- preserving same order as upstream yaml file
ligands_list = list(ligands_dict.keys())
lig_a_index = ligands_list.index(ligand_a_name)
lig_b_index = ligands_list.index(ligand_b_name)
run_relative_perturbation(lig_a_index, lig_b_index)
