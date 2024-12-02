"""rtvGetProcessTimes"""

import logging
from datetime import datetime, timedelta
import numpy as np

from hfrnet.utils_funcs.utility import now_second, now_hour
# from hfrnet.db_tools.state import State
from hfrnet.db_tools.db_tables import read_site_table, read_files_times_radialtable


_log = logging.getLogger()


def rtvGetProcessTimes(rtvProcessObj, configObj, rtvInfoObj):
    """
    # RTVGETPROCESSTIMES Obtain RTV times to process
    #
    #    times = rtvGetProcessTimes(configObj, rtvInfoObj) returns a datetime vector of hours that
    #    need to be processed for RTV solutions based on new radial data. Messages
    #    are written to the logger class and all other configuration properties are
    #    obtained from the structure c. The current and new (but not yet updated)
    #    state values are written to c for reference. It is up to the calling
    #    function to write the state value.
    #
    #    Inputs:
    #        configObj, rtvInfoObj - Structures containing configuration parameters
    #           #
    #    Outputs:
    #        time                      - Datetime vector of RTV hours to be
    #                                 processed based on availability of new
    #                                 radial data.
    #        c.rtv('current_state') - Datetime of current rtv state
    #        c.rtv('new_state')     - Datetime of new (but not updated) rtv
    #                                 state
    #
    #    Specific configuration fields required by rtvGetProcessTimes are:
    #        domain
    #        resolution
    #        confdb
    #        rtv('max_age')
    #        raddb
    #
    #    New radials are defined by the file arrival time age and rtv state.
    #    Radials newer than the rtv state are considered 'new' and will be
    #    selected for processing. The selection of new radials is also limited
    #    to a maximum data age, defined in hours by rtv('max_age'), taken relative
    #    to the current time. If no state is defined, all radials arriving
    #    since the maximum data age will be selected.
    #
    #    See also RTV, STATE, LOGGER
    #
    #    HF-Radar Network
    #    Scripps Institution of Oceanography
    #    Coastal Observing Research and Development Center
    """

    # Initialize return values
    t = []
    rtvInfoObj.current_state = None
    rtvInfoObj.new_state = None
    #------------------------------------- will be fixed
    # ## Define radial file arrival time search window
    # # Oldest data time to process
    # minTime = now_hour() - timedelta(hours=rtvInfoObj.max_age)
    # #minTime.Format = 'yyyy-MM-dd HH:mm:ss.S'
    #
    # # Check state
    # state = State(configObj.domain, configObj.domain_id,
    #               configObj.resolution, configObj.resolution_id,
    #               rtvProcessObj.name.lower(), configObj.confdb)
    # state.get()
    state.time = None
    #-------------------------

    # Set start time to arbitrairly old value if no state is defined - let
    # minTime select new radials
    if state.time is None:
        rtvInfoObj.current_state = datetime.fromisoformat('1970-01-01')
        msg = (f"No rtv state defined. Using maximum data age of {rtvInfoObj.max_age}"
               f' hours to find radials since {minTime}')
        _log.info(msg)
    else:
        rtvInfoObj.current_state = state.time
        msg = f"Obtained rtv state time of {rtvInfoObj.current_state}"
        _log.info(msg)

    # Define the end time of the search window
    rtvInfoObj.new_state = now_second() - timedelta(seconds=10)
    msg = f"Radial search window ends on {rtvInfoObj.new_state}"
    _log.debug(msg)

    ## Find all sites associated with the domain and resolution
    sites_list = read_site_table(configObj)

    time_list = read_files_times_radialtable(configObj, rtvInfoObj, sites_list, minTime)
    
    if len(time_list) == 0:
        return t

    ## Find unique dates (hours) to process
    # Assign process times
    t = [datetime.fromtimestamp(r[0]) for r in time_list]

    # Shift radials >= :30 to the top of the next hour
    for i, iTime in enumerate(t):
        if iTime.minute >= 30:
            t[i] = (iTime + timedelta(hour=1)).replace(minute=0, second=0, microsecond=0)

    # Shift radials > :00 & < :30 to the top of the current hour
    for i, iTime in enumerate(t):
        if iTime.minute < 30:
            t[i] = iTime.replace(minute=0, second=0, microsecond=0)

    # Find unique values to process
    t = np.unique(t)

    return t
