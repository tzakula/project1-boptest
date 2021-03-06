# -*- coding: utf-8 -*-
"""
Implements the parsing and code generation for signal exchange blocks.

The steps are:
1) Compile Modelica code into fmu
2) Use signal exchange block id parameters to find block instance paths and 
read any associated KPIs.
3) Write Modelica wrapper around instantiated model and associated KPI list.
4) Export as wrapper FMU and save KPI json.

"""

from pyfmi import load_fmu
from pymodelica import compile_fmu
import os
import json

def parse_instances(model_path, file_name):
    '''Parse the signal exchange block class instances using fmu xml.

    Parameters
    ----------
    model_path : str
        Path to modelica model
    file_name : list
        Path(s) to modelica file and required libraries not on MODELICAPATH.
        Passed to file_name parameter of pymodelica.compile_fmu() in JModelica.

    Returns
    -------
    instances : dict
        Dictionary of overwrite and read block class instance lists.
        {'Overwrite': [str], 'Read': [str]}
    kpis : dict
        Dictionary of kpi instance lists.
        {'kpi_name' : [list of instances]}

    '''

    # Compile fmu
    fmu_path = compile_fmu(model_path, file_name)
    # Load fmu
    fmu = load_fmu(fmu_path)
    # Check version
    if fmu.get_version() != '2.0':
        raise ValueError('FMU version must be 2.0')
    # Get all parameters
    allvars =   fmu.get_model_variables(variability = 0).keys() + \
                fmu.get_model_variables(variability = 1).keys()
    # Initialize dictionaries
    instances = {'Overwrite':[], 'Read':[]}
    kpis = {}
    # Find instances of 'Overwrite' or 'Read'
    for var in allvars:
        # Overwrite
        if 'boptestOverwrite' in var:
            label = 'Overwrite'
        # Read
        elif 'boptestRead' in var:
            label = 'Read'
        # KPI
        elif 'KPIs' in var:
            label = 'kpi'
        else:
            continue
        # Get instance name
        instance = '.'.join(var.split('.')[:-1])
        # Save instance
        if label is not 'kpi':
            instances[label].append(instance)
        else:
            for kpi in fmu.get(var)[0].split(','):
                if kpi is '':
                    continue
                elif kpi in kpis:
                    kpis[kpi].append(_make_var_name(instance,style='output'))
                else:
                    kpis[kpi] = [_make_var_name(instance,style='output')]
    # Clean up
    os.remove(fmu_path)
    os.remove(fmu_path.replace('.fmu', '_log.txt'))

    return instances, kpis

def write_wrapper(model_path, file_name, instances):
    '''Write the wrapper modelica model and export as fmu

    Parameters
    ----------
    model_path : str
        Path to orginal modelica model
    file_name : list
        Path(s) to modelica file and required libraries not on MODELICAPATH.
        Passed to file_name parameter of pymodelica.compile_fmu() in JModelica.
    instances : dict
        Dictionary of overwrite and read block class instance lists.
        {'Overwrite': [str], 'Read': [str]}

    Returns
    -------
    fmu_path : str
        Path to the wrapped modelica model fmu
    wrapped_path : str
        Path to the wrapped modelica model

    '''

    # Define wrapper modelica file path
    wrapped_path = 'wrapped.mo'
    # Open file
    with open(wrapped_path, 'w') as f:
        # Start file
        f.write('model wrapped "Wrapped model"\n')
        # Add inputs for every overwrite block
        f.write('\t// Input overwrite\n')
        input_signals = dict()
        input_activate = dict()
        for block in instances['Overwrite']:
            # Add to signal input list
            input_signals[block] = _make_var_name(block,style='input_signal')
            # Add to signal activate list
            input_activate[block] = _make_var_name(block,style='input_activate')
            # Instantiate input signal
            f.write('\tModelica.Blocks.Interfaces.RealInput {0} "Signal for overwrite block {1}";\n'.format(input_signals[block], block))
            # Instantiate input activation
            f.write('\tModelica.Blocks.Interfaces.BooleanInput {0} "Activation for overwrite block {1}";\n'.format(input_activate[block], block))
        # Add outputs for every read block
        f.write('\t// Out read\n')
        for block in instances['Read']:
            # Instantiate input signal
            f.write('\tModelica.Blocks.Interfaces.RealOutput {0} = mod.{1}.y "Measured signal for {1}";\n'.format(_make_var_name(block,style='output'), block))
        # Add original model
        f.write('\t// Original model\n')
        f.write('\t{0} mod(\n'.format(model_path))
        # Connect inputs to original model overwrite and activate signals
        for i,block in enumerate(instances['Overwrite']):
            f.write('\t\t{0}(uExt(y={1}),activate(y={2}))'.format(block, input_signals[block], input_activate[block]))
            if i == len(instances['Overwrite'])-1:
                f.write(') "Original model with overwrites";\n')
            else:
                f.write(',\n')
        # End file
        f.write('end wrapped;')
    # Export as fmu
    fmu_path = compile_fmu('wrapped', [wrapped_path]+file_name)

    return fmu_path, wrapped_path

def export_fmu(model_path, file_name):
    '''Parse signal exchange blocks and export boptest fmu and kpi json.

    Parameters
    ----------
    model_path : str
        Path to orginal modelica model
    file_name : list
        Path(s) to modelica file and required libraries not on MODELICAPATH.
        Passed to file_name parameter of pymodelica.compile_fmu() in JModelica.

    Returns
    -------
    fmu_path : str
        Path to the wrapped modelica model fmu
    kpi_path : str
        Path to kpi json

    '''

    # Get signal exchange instances and kpis
    instances, kpis = parse_instances(model_path, file_name)
    # Write wrapper and export as fmu
    fmu_path, wrapped_path = write_wrapper(model_path, file_name, instances)
    # Write kpi json
    kpi_path = os.path.join(os.getcwd(), 'kpis.json')
    with open(kpi_path, 'w') as f:
        json.dump(kpis, f)
    
    return fmu_path, kpi_path

def _make_var_name(block, style):
    '''Make a variable name from block instance name.
    
    Parameters
    ----------
    block : str
        Instance name of block
    style : str
        Style of variable to be made.
        "input_signal"|"input_activate"|"output"
        
    Returns
    -------
    var_name : str
        Variable name associated with block
        
    '''

    # General modification
    name = block.replace('.', '_')
    # Specific modification
    if style is 'input_signal':
        var_name = '{0}_u'.format(name)
    elif style is 'input_activate':
        var_name = '{0}_activate'.format(name)
    elif style is 'output':
        var_name = '{0}_y'.format(name)
    else:
        raise ValueError('Style {0} unknown.'.format(style))

    return var_name
        

if __name__ == '__main__':
    # Define model
    model_path = 'SimpleRC'
    mo_path = 'SimpleRC.mo'
    # Parse and export
    fmu_path, kpi_path = export_fmu(model_path, [mo_path])
    # Print information
    print('Exported FMU path is: {0}'.format(fmu_path))
    print('KPI json path is: {0}'.format(kpi_path))
