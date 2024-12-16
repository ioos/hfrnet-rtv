"""rtv"""

import logging
import numpy as np

from hfrnet.run_rtv.rtvGetProcessTimes import rtvGetProcessTimes
from hfrnet.run_rtv.rtvGetSiteConfig import rtvGetSiteConfig
from hfrnet.run_rtv.rtvLoadRadials import rtvLoadRadials
from hfrnet.run_rtv.rtvComputeTotals import rtvComputeTotals
from hfrnet.run_rtv.rtvMergeData import rtvMergeData
from hfrnet.run_rtv.rtvProcessMetadata import rtvProcessMetadata
from hfrnet.run_rtv.rtvSaveNetcdf import rtvSaveNetcdf
from hfrnet.utils_funcs.filenames import filenames
from hfrnet.run_rtv.saveAscii import saveAscii
from hfrnet.run_rtv.saveNetcdf import saveNetcdf
from hfrnet.db_tools.db_tables import update_state_time

_log = logging.getLogger()

def rtv(configObj, siteInfoObj, fileLocObj, rtvProcessObj, rtvInfoObj, compTotObj, land_list
        , grid) -> str:
    """
    RTV Process radials to totals

    tNewRtvFiles = rtv( ) loads available radial data, computes
    total solutions, and saves results based on configuration parameters
    provided in c while logging to the logger object.

    Configuration parameters are defined in the structure c where the
    fields are required:
        process
        domain
        resolution
        landfile
        gridfile
        total
        getExternalProcessMetadata
        confdb

    The reprocess field is defined during reprocessing. The landmask and
    total grid are loaded into the land and grid fields, respectively.

    Processing iterates over each time step where the time-dependent site
    configurations are obtained for the domain and resolution, radial
    files are loaded, totals are computed and merged with any previous
    solutions, then finally saved to all configured formats which may
    include MAT, ASCII, and NetCDF files.

    State tracking is performed during near real-time processing only and
    is not used during reprocessing.  The current and new state are
    obtained from rtvGetProcessTimes and the new state is written after
    all processing is completed.
    """

    processTimes = []
    if configObj.reprocess:
        processTimes = configObj.times
    else:
        processTimes = rtvGetProcessTimes(configObj, rtvInfoObj, rtvProcessObj)

    if processTimes and len(processTimes) > 0:
        errmsg = (f"Obtained {len(processTimes)} hour(s) to process between: "
                  f"{processTimes[0]} and {processTimes[-1]}")
        _log.info(errmsg)
    else:
        _log.warning("No new radials found")
        return None

    #------- this uses the json and netcdf file
    compTotObj.land = land_list
    landInfoObj_list = land_list


    compTotObj.grid = grid

    index = -1
    newFileMask = np.full(len(processTimes), False)

    #Loop over all the processing times
    for CalcTime in processTimes:
        _log.info(f"------------- Processing Time :: {CalcTime}")
        #increment index
        index = index + 1

        # Get/generate filename
        fileNameList = filenames(configObj, rtvProcessObj, fileLocObj, CalcTime)

        siteInfoObj = rtvGetSiteConfig(configObj, siteInfoObj, CalcTime)

        if len(siteInfoObj) == 0:
            log_message = "No sites configured for RTV processing at this time"
            _log.warning(log_message)
            continue

        if len(siteInfoObj) < rtvInfoObj.min_rad_sites:
            log_message = (f"{len(siteInfoObj)} < {rtvInfoObj.min_rad_sites}, "
                           "continue to next time interval")
            _log.warning(log_message)
            continue

        #load radial data; will have to be a big module
        radials = rtvLoadRadials(configObj, siteInfoObj, fileNameList,
                                 rtvInfoObj, landInfoObj_list, CalcTime)

        nSites = len(radials)
        #do checks on nSites
        if nSites < 2:
            log_message = (f"No of sites = {nSites} which is not enough to proceed this"
                           f" time:: {CalcTime}. continue to next time interval")
            _log.warning(log_message)
            continue

        _log.info(f"------------- Done rtvLoadRadials")

        #compute totals
        U_tot = rtvComputeTotals(compTotObj, radials, rtvInfoObj)

        if len(U_tot.nRads) == 0:
            _log.warning("No total solutions returned")
            continue
            
        _log.info(f"------------- Done rtvComputeTotals")

        # Add history and merge with previous solutions
        radials, U_tot =  rtvMergeData(fileLocObj, configObj,
                                       radials, U_tot)

        metaDataObj = rtvProcessMetadata(rtvProcessObj, configObj)
        if np.any(U_tot.hdop <= rtvInfoObj.uwls_max_hdop_nc):
            
            _log.info(f"------------- Saving uwls total files in netcdf format")
            rtvSaveNetcdf(metaDataObj, configObj, fileNameList,
                          rtvInfoObj, rtvProcessObj, CalcTime,
                          U_tot, radials)
            _log.info(f"Saving uwls total files in ascii format")
            saveAscii(rtvProcessObj, fileNameList, rtvInfoObj, U_tot)


            _log.info(f"Saving uwls total intermemedaite files in netcdf format")
            #save intermediate file (greater precision)
            allInfo = {'metaDataObj': metaDataObj.to_dict(),
                       'configObj': configObj.to_dict(),
                       'rtvInfoObj': rtvInfoObj.to_dict(),
                       'processObj': rtvProcessObj.to_dict()}
            allInfo_dict = {'c':allInfo, 't':CalcTime, 'U':U_tot.to_dict(),
                            'r': [r.to_dict() for r in radials]}
            saveNetcdf(fileNameList.intermed_filepath, allInfo_dict)

            _log.info(f"Update the process {rtvProcessObj.name} time in the state table")
            update_state_time(configObj,rtvProcessObj.name.casefold(), CalcTime)

        else:
            _log.info( 'No total solutions below netcdf hdop threshold' )
        
        _log.info(f" Set the processing time:: {CalcTime} for averages processes")
        newFileMask[index] = True

    # FIX: update state in database

    #return only new files left
    newRtvFiles = processTimes[newFileMask]

    return newRtvFiles
