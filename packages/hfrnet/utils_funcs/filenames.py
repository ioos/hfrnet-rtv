"""filenames.py"""

import logging
import calendar
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
from hfrnet.utils_funcs.lib_rtv import FileLocations
from hfrnet.utils_funcs import constsHFR

_log = logging.getLogger()

def filenames(configObj, rtvProcessObj, fileLocObj, time, process=None,
              subprocess=None):
    """
     FILENAMES Generate process paths & filenames

        filenames(configObj, rtvProcessObj, fileLocObj, time, process, 
                  subprocess)
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
            raise ValueError("Subprocess input required for lta")

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
                    raise ValueError("Subprocess input required for lta")
        else:
            _log.fatal("Undefined process name in configuration structure")
            raise ValueError(f"Invalid process name: {process}")

    # Obtain process specific paths & filenames
    if process == 'rtv':
        retFileLoc = getRtvFilenames(fileLocObj, configObj, rtvProcessObj, time)

    elif process ==  'stc':
        retFileLoc = getStcFilenames(fileLocObj, configObj, rtvProcessObj, time)

    elif process == 'lta':

        if subprocess.casefold() == (constsHFR.CONFIGS_DICT['month']).casefold():
            retFileLoc = getLtaMonthFilenames(fileLocObj, configObj,
                                              rtvProcessObj, time)

        elif subprocess.casefold() == (constsHFR.CONFIGS_DICT['year']).casefold():
            retFileLoc = getLtaYearFilenames(fileLocObj, configObj,
                                             rtvProcessObj, time)
        else:
            msg = f"Unknown subprocess {subprocess}"
            _log.fatal(msg)
            raise ValueError(f"Invalid subprocess name: {subprocess}")
    else:
        msg = f"Unknown process {process}"
        _log.fatal(msg)
        raise ValueError(f"Invalid process name: {process}")

    return retFileLoc


def find_file(domain, resolution, method, time, directory, file_format):
    """search for file which matches config"""
    
    data_file = Path(directory)
    search_par = (f"rtv_*{domain}*{resolution}*"
                  f"{method}*{time.strftime('%Y_%m_%d_%H%M')}*"
                  f".{file_format}")
    if file_format == 'nc':
        search_par = (f"{time.strftime('%Y%m%d%H%M')}"
                      f"*_hfr"
                      f"*_{domain}"
                      f"*_{resolution}"
                      f"*_rtv"
                      f"*_{method}"
                      f"*.{file_format}")
        
    data_file = list(data_file.glob(f"{search_par}"))
    if len(data_file) == 1:
        return data_file[0]
        
    data_file_no25hr = [iFile for iFile in data_file if '25hr' not in str(iFile)]
    if len(data_file_no25hr) == 1:
        return data_file_no25hr[0]
        
    msg = f"{file_format} not found: {data_file_no25hr}, {directory}/{search_par}"
    _log.warning(msg)
    return ""


# RTV paths & files
def getRtvFilenames(fileLocObj, configObj, rtvProcessObj, t):
    """files needed for the 'rtv' running mode"""

    retObj = fileLocObj
    domain = configObj.domain.casefold()
    resolution = configObj.resolution.casefold()
    method = rtvProcessObj.method.casefold()

    # Mat-file
    retObj.mdir = Path(fileLocObj.input_dir, t.strftime("%Y_%m"))

    retObj.mfilename = (f"rtv_{domain}_{resolution}_"
                        f"{method}_{t.strftime('%Y_%m_%d_%H%M')}.mat")

    # Get the relevant file
    retObj.mpathfile = find_file(domain, resolution, method, t, retObj.mdir, 'mat')

    if retObj.mpathfile == "":
        retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    retObj.input_matfile = retObj.mpathfile

    # ASCII
    retObj.asciidir = retObj.output_dir

    start_time = t.strftime(constsHFR.NCCF_FORMAT)
    end_time = t.strftime(constsHFR.NCCF_FORMAT)
    creation_time = datetime.now(timezone.utc).strftime(constsHFR.NCCF_FORMAT)
    fileLocObj.asciifilename = (f"rtv-{domain}-{resolution}-{method}_v1r0_hfr"
                                f"_s{start_time}_e{end_time}_c{creation_time}.asc")

    # Get the relevant file
    retObj.asciipathfile = Path(fileLocObj.asciidir,
                                fileLocObj.asciifilename)

    # NetCDF
    retObj.ncdir = Path(retObj.mdir, 'NetCDF')

    retObj.ncfilename = (f"{t.strftime('%Y%m%d%H%M')}"
                         f"_hfr"
                         f"_{domain}"
                         f"_{resolution}"
                         f"_rtv"
                         f"_{method}"
                         f".nc")

    retObj.ncpathfile = find_file(domain, resolution, method, t, retObj.ncdir, 'nc')
    if retObj.ncpathfile == "":
        retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)

    retObj.ncfilename = retObj.asciifilename.replace(".asc", ".nc")
    retObj.output_ncfile = Path(retObj.output_dir, retObj.ncfilename)

    return retObj


# STC paths & files
def getStcFilenames(fileLocObj, configObj, rtvProcessObj, t):
    """files for 'stc' running method"""

    retObj = fileLocObj
    domain = configObj.domain.casefold()
    resolution = configObj.resolution.casefold()
    # Mat-file
    #retObj.mdir = Path(fileLocObj.input_dir, t.strftime('%Y_%m'))

    #retObj.mfilename = (f"rtv-25hrAvg_{configObj.domain}_"
      #                  f"{configObj.resolution}_{rtvProcessObj.method}_"
     #                   f"{t.strftime('%Y_%m_%d_%H%M')}.mat")

    #retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    # ASCII
    retObj.asciidir = retObj.output_dir

    start_time = t.strftime(constsHFR.NCCF_FORMAT)
    end_time = t.strftime(constsHFR.NCCF_FORMAT)
    creation_time = datetime.now(timezone.utc).strftime(constsHFR.NCCF_FORMAT)
    retObj.asciifilename = (f"rtv-{domain}-{resolution}-25h-avg"
                            "_v1r0_hfr"
                            f"_s{start_time}_e{end_time}_c{creation_time}.asc")

    retObj.asciipathfile = Path(fileLocObj.asciidir,
                                fileLocObj.asciifilename)

    # NetCDF
    retObj.ncdir = Path(retObj.mdir, 'NetCDF')

    retObj.ncfilename = retObj.asciifilename.replace(".asc", ".nc")

    retObj.output_ncfile = Path(fileLocObj.output_dir, retObj.ncfilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-monthSum_{configObj.domain}_"
                                  f"{configObj.resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")

    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    return retObj

# LTA Month paths & files
def getLtaMonthFilenames(fileLocObj, configObj, rtvProcessObj, t):
    """files for the 'month' average calc"""

    retObj = fileLocObj
    domain = configObj.domain.casefold()
    resolution = configObj.resolution.casefold()

    # Mat-file (sum)
    retObj.msumdir = Path(fileLocObj.input_dir, 'long_term_averages',
                          t.strftime('%Y/%m'))

    retObj.msumfilename = (f"rtv-monthSum_{domain}_"
                           f"{resolution}_{rtvProcessObj.method}_"
                           f"{t.strftime('%Y%m')}.mat")

    retObj.msumpathfile = Path(fileLocObj.msumdir, fileLocObj.msumfilename)

    # Input rtv file
    retObj = getRtvFilenames(fileLocObj, configObj, rtvProcessObj, t)
    retObj.input_dir = fileLocObj.input_dir
    retObj.input_matfile = retObj.mpathfile

    ### Output files
    # Mat-file (average)
    retObj.mdir = fileLocObj.output_dir

    retObj.mfilename = (f"rtv-monthAvg_{domain}_"
                        f"{resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y%m')}.mat")

    retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)


    # ASCII (average)
    retObj.asciidir = fileLocObj.output_dir

    dayOfWeek, last = calendar.monthrange(t.year, t.month)
    start_time = (t.replace(day=1, hour=0, minute=0, second=0)).strftime(constsHFR.NCCF_FORMAT)
    end_time = (t.replace(day=last, hour=23, minute=59, second=59)).strftime(constsHFR.NCCF_FORMAT)
    creation_time = datetime.now(timezone.utc).strftime(constsHFR.NCCF_FORMAT)
    retObj.asciifilename = (f"rtv-{domain}-{resolution}"
                            "-month-avg_v1r0_hfr"
                            f"_s{start_time}_e{end_time}_c{creation_time}.asc")

    retObj.asciipathfile = Path(fileLocObj.asciidir, fileLocObj.asciifilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-monthSum_{domain}_"
                                  f"{resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")

    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    # NetCDF (average)
    retObj.ncdir = fileLocObj.output_dir

    retObj.ncfilename = retObj.asciifilename.replace(".asc", ".nc")

    retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)
    retObj.output_ncfile = retObj.ncpathfile

    return retObj

# LTA Year paths & files
def getLtaYearFilenames(fileLocObj, configObj, rtvProcessObj, t):
    """files for the 'year' average calculation"""

    retObj = FileLocations()
    domain = configObj.domain.casefold()
    resolution = configObj.resolution.casefold()

    retObj.output_dir = fileLocObj.output_dir

    retObj.mfilename = (f"rtv-monthSum_{domain}_"
                        f"{resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y%m')}.mat")
    retObj.input_dir = Path(fileLocObj.input_dir, 'long_term_averages',
                            t.strftime('%Y'), t.strftime('%m'))
    retObj.input_matfile = Path(retObj.input_dir, retObj.mfilename)

    # Mat-file
    retObj.mdir = Path(fileLocObj.output_dir, 'long_term_averages',
                       t.strftime('%Y'))

    retObj.mfilename = (f"rtv-annualAvg_{domain}_"
                        f"{resolution}_{rtvProcessObj.method}_"
                        f"{t.strftime('%Y')}.mat")

    retObj.mpathfile = Path(retObj.mdir, retObj.mfilename)

    #intermediate file
    retObj.intermed_filename = (f"rtv-annualSum_{domain}_"
                                  f"{resolution}_{rtvProcessObj.method}_"
                                  f"{t.strftime('%Y%m')}.nc")

    retObj.intermed_filepath = Path(fileLocObj.output_dir, retObj.intermed_filename)

    # ASCII
    retObj.asciidir = retObj.output_dir

    retObj.mfilename = (f"rtv_{domain}_{resolution}_"
                        f"{rtvProcessObj.method}_" 
                        f"{t.strftime('%Y_%m_%d_%H%M')}.mat")

    start_time = (t.replace(month=1, day=1, hour=0, minute=0, second=0)
                  .strftime(constsHFR.NCCF_FORMAT))
    end_time = (t.replace(month=12, day=31, hour=23, minute=59, second=59)
                .strftime(constsHFR.NCCF_FORMAT))
    creation_time = datetime.now(timezone.utc).strftime(constsHFR.NCCF_FORMAT)
    retObj.asciifilename = (f"rtv-{domain}-{resolution}-ann-avg_v1r0_hfr"
                            f"s{start_time}_e{end_time}_c{creation_time}.asc")

    retObj.asciipathfile = Path(retObj.asciidir, retObj.asciifilename)

    # NetCDF
    retObj.ncdir = retObj.output_dir

    retObj.ncfilename = retObj.asciifilename.replace(".asc", ".nc")

    retObj.ncpathfile = Path(retObj.ncdir, retObj.ncfilename)
    retObj.output_ncfile = retObj.ncpathfile

    return retObj
