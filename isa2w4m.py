#!/usr/bin/env python3
# vi: fdm=marker

import argparse
import sys
import os.path
import re
import glob
import collections
from string import Template
from isatools import isatab as ISATAB

# Check Python version
if sys.hexversion < 0x03040000:
    sys.exit("Python 3.4 or newer is required to run this program.")

class FilenameTemplate(Template):
    delimiter='%'

# Error message {{{1
################################################################

def error(msg):
    print('ERROR: ' + msg, file = sys.stderr)
    sys.exit(1)
    
# Information message {{{1
################################################################

def info(msg):
    if not QUIET:
        print('INFO: ' + msg)

# Read arguments {{{1
################################################################

def read_args():
    
    s1 = 'You can use it as a template, where %%s will be replaced by the study name and %%a by the assay filename.'
	
    # Default values
    dft_output_dir = '.'
    dft_sample_file = '%s-%a-sample-metadata.tsv'
    dft_variable_file = '%s-%a-variable-metadata.tsv'
    dft_matrix_file = '%s-%a-sample-variable-matrix.tsv'
    
    parser = argparse.ArgumentParser(description='Script for extracting assays from ISATab data and outputing in W4M format.')
    parser.add_argument('-a', help = 'Extract all assays.', dest = 'all_assays', action = 'store_true')
    parser.add_argument('-i', help = 'Input directory containing the ISA-Tab files.', dest = 'input_dir', required = True)
    parser.add_argument('-f', help = 'Filename of the assay to extract. If unset, the first assay of the chosen study will be used.',   dest = 'assay_filename')
    parser.add_argument('-n', help = 'Filename of the study to extract. If unset, the first study found will be used.', dest = 'study_filename')
    parser.add_argument('-d', help = 'Set output directory. Default is "' + dft_output_dir + '".', dest = "output_dir", default = dft_output_dir)
    parser.add_argument('-s', help = 'Output file for sample metadata. ' + s1 + ' Default is "' + dft_sample_file.replace('%', '%%') + '".', dest = "sample_output", default = dft_sample_file)
    parser.add_argument('-v', help = 'Output file for variable metadata. ' + s1 + ' Default is "' + dft_variable_file.replace('%', '%%') + '".', dest = 'variable_output', default = dft_variable_file)
    parser.add_argument('-m', help = 'Output file for sample x variable matrix. ' + s1 + ' Default is "' + dft_matrix_file.replace('%', '%%') + '".', dest = 'matrix_output', default = dft_matrix_file)
    parser.add_argument('-S', help = 'Filter out NA values in the specified sample metadata columns. The value is a comma separated list of column names.',   dest = 'samp_na_filering')
    parser.add_argument('-V', help = 'Filter out NA values in the specified variable metadata columns. The value is a comma separated list of column names.', dest = 'var_na_filering')
    parser.add_argument('-q', help = 'Quiet.', dest = 'quiet', action = 'store_true')
    args = parser.parse_args()
    args = vars(args)
 
    # Split comma separated list
    for opt in ['samp_na_filering', 'var_na_filering']:
        if opt in args and args[opt] is not None:
            args[opt] = args[opt].split(',')
            
    return args
    
# Select study {{{1
################################################################

def select_study(investigation_file, study_filename = None):
    
    investigation = load_investigation(investigation_file)
    study = None
    
    # More than one study and no study specified
    if len(investigation.studies) > 1 and study_filename is None :
        error('The investigation file "' + investigation_file + '" contains more than one study. You need to select one of them.')
 
    # Search for specified study
    if study_filename is not None:
        
        # Loop on all studies
        for s in investigation.studies:
            if s.filename == study_filename:
                study = s
                break

        # Specified study not found
        if study is None:
            error('Study "' + study_filename + '" not found in investigation file "' + investigation_file + '".')
        
    # Take first one
    if study is None and len(investigation.studies) > 0 :
        study = investigation.studies[0]
        
    return study
    
# Select assays {{{1
################################################################

def select_assays(study, assay_filename = None, all_assays = False):
    
    assays = []
    
    # Search for specified assay
    if assay_filename is not None and not all_assays:
        
        # Loop on all assays
        for a in study.assays:
            if a.filename == assay_filename:
                assays.append(a)
                break
            
        # Specified assay not found
        if len(assays) == 0 :
            error('Assay "' + assay_filename + '" not found.')
    
    # Take all assays
    elif all_assays:
        assays = study.assays
        
    # Take first one
    else:
        assays = study.assays[0:1]

    return assays
    
# Get data file {{{1
################################################################

def get_data_file(assay):
    
    data_filename = None
    
    # Look for data files in assay
    for df in assay.data_files:
        m = re.match('^m_.*\.(tsv|txt)$', df.filename)
        if m is not None:
            if data_filename is not None:
                error('Found two data files ("', data_filename, '" and "', df.filename, '") in assay "', assay.filename, '".')
            info('Found data file "' + df.filename + '".')
            data_filename = df.filename
            
    # No data file
    if data_filename is None:
        error('Found no data file in assay "', assayfilename, '".')
        
    return data_filename
    
# Get assay data frame {{{1
################################################################

def get_assay_df(input_dir, assay):
    return ISATAB.read_tfile(os.path.join(input_dir, assay.filename))
    
# Get measures data frame {{{1
################################################################

def get_measures_df(input_dir, assay):
    data_filename = get_data_file(assay)
    array = ISATAB.read_tfile(os.path.join(input_dir, data_filename))
    return array

# Get study data frame {{{1
################################################################

def get_study_df(input_dir, study):
    return ISATAB.read_tfile(os.path.join(input_dir, study.filename))

# Make names {{{1
################################################################

def make_names(u, uniq = False):
 
    v = u[:]
    j = 0
    for i in range(len(v)):
        
        # Create missing names
        if v[i] == '':
            v[i] = 'X' + ('' if j == 0 else ('.' + str(j)))
            j += 1
            
        # Remove unvanted characters
        else:
            v[i] = re.sub(r'[^A-Za-z0-9_.]', '.', v[i])
            
    # Make sure all elements are unique  
    if uniq:
        # List all indices of items
        item_indices = collections.defaultdict(list)
        for i, x in enumerate(v):
            item_indices[x].append(i)
            
        # Look for duplicates
        for x in item_indices.keys():
            
            # Is this item duplicated?
            if len(item_indices[x]) > 1:
                
                # Rename all duplicates
                j = 1
                for i in item_indices[x][1:]:
                    while True:
                        new_name = v[i] + "." + str(j)
                        if new_name not in item_indices:
                            break
                        j += 1
                    v[i] = new_name
        
    return v
    
# Make variable names {{{1
################################################################

def make_variable_names(assay_df):

    var_names = None
 
    # Make variable names from data values
    for col in ['mass_to_charge', 'retention_time']:
        try:
            if var_names is None:
                var_names = assay_df[col].values
            else:
                var_names = [ s + ('' if str(t) == '' else ('_' + str(t))) for s, t in zip(var_names, assay_df[col].values)]
        except:
            pass
    
    # Normlize names
    var_names = make_names(var_names)

    return var_names

# Get investigation file {{{1
################################################################

def get_investigation_file(input_dir):

    # Search for file
    investigation_files = glob.glob(os.path.join(input_dir, 'i_*.txt'))
    
    # No file
    if len(investigation_files) == 0:
        error('No investigation file found.')
        
    # More than one file
    if len(investigation_files) > 1:
        error('Found more than one investigation file.')
        
    # File found
    investigation_file = investigation_files[0]
    info('Found investigation file "' + investigation_file + '".')
    
    return investigation_file
    
# Load investigation {{{1
################################################################

def load_investigation(investigation_file):
    f = open(investigation_file, 'r')
    investigation = ISATAB.load(f)
    return investigation
    
# Get sample names {{{1
################################################################

def get_sample_names(assay, assay_df, measures_df):
    
    # Get sample names
    sample_names = [sample.name for sample in assay.materials['samples']]
    measures_cols = measures_df.axes[1]
    
    # XXX If the column 'Sample Name' of the assay file contains duplicated names, then `assay.materials['samples']]` will return less sample names than there are. It may happen that, as in MTBLS404 with the column 'Extract Name', another column contains "real" sample names that are all different.
    if len(sample_names) != assay_df.shape[0] or any([x not in measures_cols for x in sample_names]):
        # TODO send warning message
        for col in assay_df.axes[1]:
            n = assay_df.get(col).tolist()
            if len(n) == len(set(n)) and all([x in measures_cols for x in n]):
                sample_names = n
                break

    return sample_names

# Make sample metadata {{{1
################################################################

def make_sample_metadata(study_df, assay_df, sample_names, normalize = True):
    
    # Normalize column names
    study_df.set_axis(1, make_names(study_df.axes[1].tolist()))
    assay_df.set_axis(1, make_names(assay_df.axes[1].tolist()))
    
    # Merge data frames
    sample_metadata = assay_df.merge(study_df, on = 'Sample.Name', sort = False)

    # Normalize
    if (normalize):
        norm_sample_names = make_names(sample_names, uniq = True)
        sample_metadata.insert(0, 'sample.name', norm_sample_names)
        sample_metadata.set_axis(1, make_names(sample_metadata.axes[1].tolist(), uniq = True))

    return sample_metadata

# Make variable metadata
################################################################

def make_variable_metadata(measures_df, sample_names, variable_names, normalize = True):
    
    # Get variable columns from measures data frame
    all_cols = measures_df.axes[1].tolist()
    variable_cols = [x for x in all_cols if x not in sample_names]
    variable_metadata = measures_df.get(variable_cols)
    
    # Add variable names as columns
    variable_metadata.insert(0, 'variable.name', variable_names)

    # Normalize
    if normalize:
        variable_metadata.set_axis(1, make_names(variable_metadata.axes[1].tolist(), uniq = True))
    
    return variable_metadata
    
# Make matrix {{{1
################################################################

def make_matrix(measures_df, sample_names, variable_names, normalize = True):
    
    # Take all sample columns from measures data frame
    sample_variable_matrix = measures_df.get(sample_names)
    
    # Check that we got all columns
    if sample_variable_matrix is None or len(sample_variable_matrix.axes[1]) != len(sample_names):
        raise Exception('Some or all sample names were not found among the column names of the data array.')

    # Add variable names as columns
    sample_variable_matrix.insert(0, 'variable.name', variable_names)

    # Normalize sample names
    if normalize:
        norm_sample_names = make_names(sample_names, uniq = True)
        norm_sample_names.insert(0, 'variable.name')
        sample_variable_matrix.set_axis(1, norm_sample_names)

    return sample_variable_matrix

# Convert to W4M {{{1
################################################################

def convert2w4m(input_dir, study_filename = None, assay_filename = None, all_assays = False):
    
    # Select study
    investigation_file = get_investigation_file(input_dir)
    study = select_study(investigation_file, study_filename)
    if study is None:
        info('No studies found in investigation file.')
        return
    info('Processing study "' + study.filename + '".')
    
    # Select assays
    assays = select_assays(study = study, assay_filename = assay_filename, all_assays = all_assays)
    
    # Loop on all assays
    w4m_assays = []
    for assay in assays:
        info('Processing assay "' + assay.filename + '".')
        study_df = get_study_df(input_dir, study)
        assay_df = get_assay_df(input_dir, assay)
        measures_df = get_measures_df(input_dir, assay)
        variable_names = make_variable_names(measures_df)
        sample_names = get_sample_names(assay = assay, assay_df = assay_df, measures_df = measures_df)
        sample_metadata = make_sample_metadata(study_df = study_df, assay_df = assay_df, sample_names = sample_names, normalize = True)
        variable_metadata = make_variable_metadata(measures_df = measures_df, sample_names = sample_names, variable_names = variable_names, normalize = True)
        sample_variable_matrix = make_matrix(measures_df = measures_df, sample_names = sample_names, variable_names = variable_names, normalize = True)
        w4m_assays.append(dict( samp = sample_metadata, var = variable_metadata, mat = sample_variable_matrix, filename = assay.filename, study = study.identifier))
        
    return w4m_assays
 
# Write data frame {{{1
################################################################

def write_data_frame(df, output_dir, template_filename, study, assay):
    filename = FilenameTemplate(template_filename).substitute(s = study, a = assay)
    if output_dir is not None:
        filename = os.path.join(output_dir, filename)
    df.to_csv(path_or_buf = filename, sep = "\t", na_rep = 'NA')
    
# Write assays into files {{{1
################################################################

def write_assays(assays, output_dir, samp_file, var_file, mat_file):
 
    # Create output directory if necessary
    if output_dir is not None and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Make dict for file names
    filenames = dict(samp = samp_file, var = var_file, mat = mat_file)
    
    # Loop on all assays
    for assay in assays:
        for df in ['samp', 'var', 'mat']:
            write_data_frame(df = assay[df], output_dir = output_dir, template_filename = filenames[df], study = assay['study'], assay = assay['filename'])
    
# Filter NA values {{{1
################################################################

def filter_na_values(assays, table, cols):
    
    # Loop on all assays
    for assay in assays:
        assay[table].dropna(axis = 0, how = 'all', subset = make_names(cols), inplace = True)
        
# Main {{{1
################################################################

if __name__ == '__main__':
    
    # Parse command line arguments
    args_dict = read_args()
    QUIET = False
    if args_dict['quiet'] is not None:
        QUIET = args_dict['quiet']
    
    # Convert assays to W4M 3 tables format
    assays = convert2w4m(input_dir = args_dict['input_dir'], study_filename = args_dict['study_filename'], assay_filename = args_dict['assay_filename'], all_assays = args_dict['all_assays'])
    
    # Filter NA values
    if args_dict['samp_na_filering'] is not None:
        filter_na_values(assays, table = 'samp', cols = args_dict['samp_na_filering'])
    if args_dict['var_na_filering'] is not None:
        filter_na_values(assays, table = 'var', cols = args_dict['var_na_filering'])
    
    # Write into files
    write_assays(assays, output_dir = args_dict['output_dir'], samp_file = args_dict['sample_output'], var_file = args_dict['variable_output'], mat_file = args_dict['matrix_output'])
