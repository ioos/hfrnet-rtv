"""filenames.py"""

import logging
from pathlib import Path
from copy import deepcopy

from hfrnet.utils_funcs.lib_rtv import FileLocations
import hfrnet.utils_funcs.constsHFR as constsHFR

_log = logging.getLogger()

def filenames(configObj, rtvProcessObj, fileLocObj, time, process=None,
              subprocess=None, institution_acronym='SIO'):
    """
     FILENAMES Generate process paths & filenames

        filenames(configObj, rtvProcessObj, fileLocObj, time, process, 
                  subprocess, institution_acronym) 
        updates or adds fields to the c.total structure which define the paths
        and file names for all files to be exported (MAT, ASCII, & NetCDF) for
        the given process, domain, resolution, and timestamp.

        Unless process is provided, the process defined in rtvProcessObj is used
        to determine the process to return filenames and paths for.  Otherwise,
        if process is provided, filenames and paths for the named process are
        returned. Valid process names are 'rtv', 'stc' and 'lta'.  The
        additional parameter subprocess is only required for 'lta' where
        possible options are 'month' or 'year'.

        HF-Radar Network
        Scripps Institution of Oceanography
        Coastal Observing Research and Development Center
    """

    retFileLoc = deepcopy(fileLocObj)
    # Define process based on input
    # Use optional input, if provided
    if process is not None:

        # Verify subprocess is provided for lta
        if process.casefold() == 'lta'  and  subprocess is None:
            _log.fatal("Subprocess input required for lta")

    else:
        # Otherwise, obtain from configuration structure

        # Verify process field & name are defined in config structure
        if rtvProcessObj.name:
            process = rtvProcessObj.name.casefold()
            
            # Verify subprocess is defined in config for lta
            if process == 'lta':
                if rtvProcessObj.subprocess_name:
                    subprocess = rtvProcessObj.subprocess_name.casefold()
                else:
                    _log.fatal("Undefined subprocess field or key in "
                               "configuration structure,(required for lta)")
        else:
            _log.fatal("Undefined process name in configuration structure")

    # Obtain process specific paths & filenames
    if process == 'rtv':
        retFileLoc = getRtvFilenames(fileLocObj, configObj, rtvProcessObj, time,
                                     institution_acronym)
    elif process ==  'stc':
        retFileLoc = getStcFilenames(fileLocObj, configObj, rtvProcessObj, time,
                                     institution_acronym)
    elif process == 'lta':
        
        if subprocess.casefold() == (constsHFR.CONFIGS_DICT['month']).casefold():
            retFileLoc = getLtaMonthFilenames(fileLocObj, configObj,
                                              rtvProcessObj, time, institution_acronym)

        elif subprocess.casefold() == (constsHFR.CONFIGS_DICT['year']).casefold():
            retFileLoc = getLtaYearFilenames(fileLocObj, configObj,
                                             rtvProcessObj, time, institution_acronym)
        else:
            msg = f"Unknown subprocess {subprocess}"
            _log.fatal(msg)
    else:
        msg = f"Unknown subprocess {subprocess}"
        _log.fatal(msg)

    return retFileLoc

# RTV paths & files
def getRtvFilenames(fileLocObj, configObj, rtvProcessObj, t,
                    institution_acronym):
    """files needed for the 'rtv' running mode"""

    retObj = fileLocObj

    def find_file(directory, file_format):
        """search for file which matches config"""

        data_file = Path(directory)
        search_par = (f"rtv_*{configObj.domain}*{configObj.resolution}*"
                      f"{rtvProcessObj.method}*{t.strftime('%Y_%m_%d_%H%M')}*"
                      f".{file_format}")
        if file_format == 'nc':
            search_par = (f"{t.strftime('%Y%m%d%H%M')}"
                          f"*_hfr"
                          f"*_{configObj.domain}"
                          f"*_{configObj.resolution}"
                          f"*_rtv"
                          f"*_{rtvProcessObj.method}"
                          f"*_{institution_acronym.upper()}.{file_format}")

        data_file = list(data_file.glob(f"{search_par}"))
        if len(data_file) == 1:
            return Path(data_file[0])

        data_file_no25hr = [iFile for iFile in data_file if '25hr' not in str(iFile)]
        if len(data_file_no25hr) == 1:
            return Path(data_file_no25hr[0])

        msg = f"{file_format} not found: {data_file_no25hr}, {directory}/{search_par}"
        _log.warning(msg)
        return ""

    # Mat-file
    retObj.mdir = Path(fileLocObj.input_dir, t.strftime("%Y_%m"))

    retObj.mfilename = (f"rtv_{configObj.domain}_{configObj.resolution}_"
                        f"{rtvProcessObj.method}_{t.strftime('%Y_%m_%d_%H%M')}.mat")

    # Get the relevant file
    retObj.mpathfile = find_file(retObj.mdir, 'mat')

    if retObj.mpathfile == "":
        retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    retObj.input_matfile = retObj.mpathfile

    # ASCII
    retObj.asciidir = retObj.output_dir

    fileLocObj.asciifilename = (f"rtv"
                                f"_{configObj.domain}"
                                f"_{configObj.resolution}"
                                f"_{rtvProcessObj.method}"
                                f"_{t.strftime('%Y_%m_%d_%H%M')}.asc")

    # Get the relevant file
    retObj.asciipathfile = Path(fileLocObj.asciidir,
                                fileLocObj.asciifilename)

    # NetCDF
    retObj.ncdir = Path(retObj.mdir, 'NetCDF')

    retObj.ncfilename = (f"{t.strftime('%Y%m%d%H%M')}"
                         f"_hfr"
                         f"_{configObj.domain}"
                         f"_{configObj.resolution}"
                         f"_rtv"
                         f"_{rtvProcessObj.method}"
                         f"_{institution_acronym.upper()}.nc")

    #retObj.ncfilename = (f"rtv-{configObj.domain}-{configObj.resolution}-uwls"
     #                    f"_v1r0_hfr_s{startTime}_e{endTime}_c{creationTime}.nc")

    retObj.ncpathfile = find_file(retObj.ncdir, 'nc')
    if retObj.ncpathfile == "":
        retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)

    retObj.output_ncfile = Path(retObj.output_dir, retObj.ncfilename)

    return retObj


# STC paths & files
def getStcFilenames(fileLocObj, configObj, rtvProcessObj, t, institution_acronym):
    """files for 'stc' running method"""

    retObj = fileLocObj
    # Mat-file
    retObj.mdir = Path(fileLocObj.input_dir, t.strftime('%Y_%m'))

    retObj.mfilename = (f"rtv-25hrAvg_{configObj.domain}_"
                        f"{configObj.resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y_%m_%d_%H%M')}.mat")

    retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    # ASCII
    retObj.asciidir = retObj.output_dir

    retObj.asciifilename = (f"rtv-25hrAvg_{configObj.domain}_"
                            f"{configObj.resolution}_{rtvProcessObj.method}_"
                            f"{t.strftime('%Y_%m_%d_%H%M')}.asc")

    retObj.asciipathfile = Path(fileLocObj.asciidir,
                                fileLocObj.asciifilename)

    # NetCDF
    retObj.ncdir = Path(retObj.mdir, 'NetCDF')

    retObj.ncfilename = (f"{t.strftime('%Y%m%d%H%M')}_hfr_"
                         f"{configObj.domain}_{configObj.resolution}_"
                         f"rtv_{rtvProcessObj.method}_25hr_average_" 
                         f"{institution_acronym.upper()}.nc")

    retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)
    retObj.output_ncfile = Path(fileLocObj.output_dir, retObj.ncfilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-monthSum_{configObj.domain}_"
                                  f"{configObj.resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")
    
    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    return retObj

# LTA Month paths & files
def getLtaMonthFilenames(fileLocObj, configObj, rtvProcessObj, t,
                         institution_acronym):
    """files for the 'month' average calc"""

    retObj = fileLocObj
    # Mat-file (sum)
    retObj.msumdir = Path(fileLocObj.input_dir, 'long_term_averages',
                          t.strftime('%Y/%m'))

    retObj.msumfilename = (f"rtv-monthSum_{configObj.domain}_"
                           f"{configObj.resolution}_{rtvProcessObj.method}_"
                           f"{t.strftime('%Y%m')}.mat")

    retObj.msumpathfile = Path(fileLocObj.msumdir, fileLocObj.msumfilename)

    # Input rtv file
    retObj = getRtvFilenames(fileLocObj, configObj, rtvProcessObj, t,
                    institution_acronym)
    retObj.input_dir = fileLocObj.input_dir
    retObj.input_matfile = retObj.mpathfile

    ### Output files
    # Mat-file (average)
    retObj.mdir = fileLocObj.output_dir

    retObj.mfilename = (f"rtv-monthAvg_{configObj.domain}_"
                        f"{configObj.resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y%m')}.mat")

    retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)


    # ASCII (average)
    retObj.asciidir = fileLocObj.output_dir

    retObj.asciifilename = (f"rtv-monthAvg_{configObj.domain}_"
                            f"{configObj.resolution}_{rtvProcessObj.method}_"
                            f"{t.strftime('%Y%m')}.asc")

    retObj.asciipathfile = Path(fileLocObj.asciidir, fileLocObj.asciifilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-monthSum_{configObj.domain}_"
                                  f"{configObj.resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")

    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    # NetCDF (average)
    retObj.ncdir = fileLocObj.output_dir

    retObj.ncfilename = (f"{t.strftime('%Y%m')}_hfr_{configObj.domain}_"
                         f"{configObj.resolution}_rtv_{rtvProcessObj.method}_"
                         f"month_average_{institution_acronym.upper()}.nc")

    retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)
    retObj.output_ncfile = retObj.ncpathfile

    return retObj

# LTA Year paths & files
def getLtaYearFilenames(fileLocObj, configObj, rtvProcessObj, t, institution_acronym):
    """files for the 'year' average calculation"""

    retObj = FileLocations()

    retObj.output_dir = fileLocObj.output_dir

    retObj.mfilename = (f"rtv-monthSum_{configObj.domain}_"
                        f"{configObj.resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y%m')}.mat")
    retObj.input_dir = Path(fileLocObj.input_dir, 'long_term_averages',
                            t.strftime('%Y'), t.strftime('%m'))
    retObj.input_matfile = Path(retObj.input_dir, retObj.mfilename)

    # Mat-file
    retObj.mdir = Path(fileLocObj.output_dir, 'long_term_averages',
                       t.strftime('%Y'))

    retObj.mfilename = (f"rtv-annualAvg_{configObj.domain}_"
                        f"{configObj.resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y')}.mat")

    retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-annualSum_{configObj.domain}_"
                                  f"{configObj.resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")
    
    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    # ASCII
    retObj.asciidir = retObj.output_dir

    retObj.mfilename = (f"rtv_{configObj.domain}_{configObj.resolution}_"
                        f"{rtvProcessObj.method}_" 
                        f"{t.strftime('%Y_%m_%d_%H%M')}.mat")

    retObj.asciifilename = (f"rtv-annualAvg_{configObj.domain}_"
                            f"{configObj.resolution}_{rtvProcessObj.method}_"
                            f"{t.strftime('%Y')}.asc")

    retObj.asciipathfile = Path(retObj.asciidir, retObj.asciifilename)

    # NetCDF
    retObj.ncdir = retObj.mdir

    retObj.ncfilename = (f"{t.strftime('%Y')}_hfr_{configObj.domain}_"
                         f"{configObj.resolution}_rtv_" 
                         f"{rtvProcessObj.method}_annual_average_"
                         f"{institution_acronym.upper()}.nc")

    retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)
    retObj.output_ncfile = retObj.ncpathfile

    return retObj
