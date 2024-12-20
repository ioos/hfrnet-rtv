#!/usr/bin/env python

"""processRtv"""

import logging
from datetime import timedelta, datetime, timezone
import numpy as np

from hfrnet.utils_funcs.lib_rtv import RtvProcess
from hfrnet.run_rtv import rtv
from hfrnet.utils_funcs.filenames import filenames
from hfrnet.run_rtv.sumAvg import SumAndAvg
from hfrnet.run_rtv.stcSaveNetcdf import stcSaveNetcdf
from hfrnet.run_rtv.ltaSaveNetcdf import ltaSaveNetcdf
from hfrnet.run_rtv.saveNetcdf import saveNetcdf
from hfrnet.run_rtv.rtvProcessMetadata import rtvProcessMetadata
from hfrnet.utils_funcs.utility import load_land, load_grid, ltaRunConfig
from hfrnet.db_tools.db_tables import update_state_time
import hfrnet.utils_funcs.constsHFR as constsHFR

_log = logging.getLogger()

def processRtv(configObj, siteInfoObj, fileLocObj, rtvProcessObj, rtvInfoObj,
               stcLtaInfoObj, compTotObj):
    """

    Processes all RTV products

    processRtv( domain, resolution, configFunction ) processes all RTV
    products for the given domain and resolution based on configuration
    parameters obtained by configFunction.  This form is typically used
    in near real-time processing.  Process locking is mandatory and
    prevents concurrent instances for the given domain and resulution from
    running.
    
    processRtv( ..., reprocessTimes, reprocessLock ) is the form used
    during reprocessing where additional inputs reprocessTimes and
    reprocessLock define the times to be reprocessed and whether or not
    process locking should be used. Process locking is optional during
    reprocessing and has a default value of true.  Whether or not
    locking should be used depends on whether or not the reprocessing
    overlaps with data that are still within the near real-time processing
    window.  The same lock file is used for near-real time processing and
    reprocessing.  The reprocessTimes input should be a vector of 1 or
    more datetime values.

    Inputs:
        domain         - character array
        resolution     - character array
        configFunction - character array
        reprocessTimes - datetime vector (optional)
        reprocessLock  - logical (optional, default=true)

    The configFunction must be a function in the runtime environment's
    path or otherwise be defined with its full path. It must return all
    required configuration parameters for this and any subsequent
    functions. A general overview is provided in configFunction while
    operational branches serve as working examples.

    Processing is defined by the configuration structure's processes field
    which is a table of processes listed in order of processing. Supported
    processing options are real-time vector (rtv), sub-tidal current
    (stc), and long-term averages (lta).  Only the unweightted
    least-squares (uwls) method is supported.  Reprocessing parameters are
    saved to the configuration structure's reprocess field as a map.

    Use runRtv to call processRtv in batch mode from the command-line.

    """
    process = RtvProcess()

    domain = configObj.domain.lower()
    #load land and grid files
    land = load_land(fileLocObj.landfile, domain)
    grid = None
    gridvar = f'{domain}{configObj.resolution}'
    try:
        grid = load_grid(fileLocObj.gridfile, domain,
                         configObj.resolution, rtvInfoObj)
        if len(grid.size) < 1:
            grid.size = np.array([0, 0], dtype=int)
    except Exception as e:
        errmsg = f'Error loading variable {gridvar} from {fileLocObj.gridfile}: {str(e)}'
        _log.error(errmsg)

    newRtvFiles = []
    nProcesses = len(rtvProcessObj)
    for iProcess in range(nProcesses):

        process = rtvProcessObj[iProcess]

        if process.method != 'uwls':
            message = f"ERROR: Only 'uwls' methods are supported, not {process.method}"
            _log.warning(message)
            continue

        if process.name.casefold() == 'rtv':

            newRtvFiles = rtv.rtv(configObj, siteInfoObj, fileLocObj,
                                  process, rtvInfoObj, compTotObj, land, grid)
            if len(newRtvFiles) == 0:
                _log.info('No rtv files created or updated')
            else:
                msg = f'Created or updated {len(newRtvFiles)} rtv files'
                _log.info(msg)

        if process.name.casefold() == 'stc':

            for iTime in newRtvFiles:
                #offset time to the center of the 25 hr window
                center_time = iTime - timedelta(hours=12)
                sumAvg = SumAndAvg('25 Hour', configObj, process,
                                   fileLocObj, center_time, stcLtaInfoObj)
                sumObj = sumAvg.get_sum()
                avgObj = sumAvg.get_avg()

                metaDataObj = rtvProcessMetadata(process, configObj)
                fileNameList = filenames(configObj, process,
                                         fileLocObj, center_time)
                avgObj.land = land
                avgObj.grid = grid
                stcInfoObj = stcLtaInfoObj.stcInfo

                #save intermediate file
                allInfo = {'metaDataObj': metaDataObj.to_dict(),
                           'configObj': configObj.to_dict(),
                           'stcInfoObj': stcInfoObj.to_dict(),
                           'process': process.to_dict()}
                allInfo_dict = {'c': allInfo, 'tc': center_time, 'A': sumObj.to_dict()}
                
                saveNetcdf(fileNameList.intermed_filepath, allInfo_dict)
                _log.info(f"Saving stc total intermemedaite files in netcdf format")
                stcSaveNetcdf(metaDataObj, configObj,
                              fileNameList, stcInfoObj,
                              process, center_time, avgObj)

                time_curr = datetime.now(timezone.utc).strftime(constsHFR.DATETIME_FORMAT)
                _log.info(f"Update the process {process.name} time {time_curr} in the state table")                
                update_state_time(configObj, process.name.casefold(), time_curr)


        if process.name.casefold() == 'lta':
            newRtvFiles = [configObj.runTime]
            for iTime in newRtvFiles:

                doMonthly, doYearly, monthTime, yearTime = ltaRunConfig(iTime, configObj, process)

                if doMonthly:

                    #calculation
                    sumAvg = SumAndAvg("monthly", configObj, process,
                                       fileLocObj, monthTime, stcLtaInfoObj)
                    sumObj = sumAvg.get_sum()
                    avgObj = sumAvg.get_avg()

                    #metadata and filenames for output
                    avgObj.land = land
                    avgObj.grid = grid
                    metaDataObj = rtvProcessMetadata(process, configObj)
                    fileNameList = filenames(configObj, process,
                                             fileLocObj, monthTime)

                    #save intermediate file
                    allInfo = {'metaDataObj': metaDataObj.to_dict(),
                               'configObj': configObj.to_dict(),
                               'stcLtaInfoObj': stcLtaInfoObj.to_dict(),
                               'process': process.to_dict()}
                    allInfo_dict = {'c': allInfo, 't': iTime, 'S': sumObj.to_dict()}
                    
                    _log.info(f"------------- Saving monthly total files in netcdf "
                              f"format")
                    saveNetcdf(fileNameList.intermed_filepath, allInfo_dict)

                    #save final file
                    _log.info(f"------------- Saving intermmediate monthly total files "
                              f"in netcdf format")
                    ltaSaveNetcdf(metaDataObj, configObj,
                                  fileNameList, stcLtaInfoObj,
                                  process, iTime, avgObj)

                    time_curr = datetime.now(timezone.utc).strftime(constsHFR.DATETIME_FORMAT)
                    _log.info(f"Update the process {process.name} time {time_curr} in the state table")
                    update_state_time(configObj, process.name.casefold(), time_curr)
   
                if doYearly:
                    #calculation
                    sumAvgYear = SumAndAvg("annual", configObj, process,
                                       fileLocObj, yearTime, stcLtaInfoObj)
                    sumObjYear = sumAvgYear.get_sum()
                    avgObjYear = sumAvgYear.get_avg()

                    #metadata and filenames for output
                    avgObjYear.land = land
                    avgObjYear.grid = grid
                    metaDataObj = rtvProcessMetadata(process, configObj)
                    fileNameList = filenames(configObj, process,
                                             fileLocObj, yearTime)
                    #save final file
                    _log.info(f"------------- Saving annual total files in netcdf format")
                    ltaSaveNetcdf(metaDataObj, configObj,
                                  fileNameList, stcLtaInfoObj,
                                  process, iTime, avgObjYear)

                    time_curr = datetime.now(timezone.utc).strftime(constsHFR.DATETIME_FORMAT)
                    _log.info(
                        f"Update the process {process.name} time {time_curr} in the state table")
                    update_state_time(configObj, process.name.casefold(), time_curr)
