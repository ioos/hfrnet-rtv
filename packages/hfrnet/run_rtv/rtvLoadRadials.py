"""rtvLoadRadials"""

import re
import logging
from pathlib import Path

import numpy as np

from hfrnet.utils_funcs.lib_rtv import RadialInfo
from hfrnet.run_rtv.rtvReadRadialFile import rtvReadRadialFile

from hfrnet.utils_funcs.utility import _dict, read_total_file
from hfrnet.utils_funcs.math_funcs import  km2deg, scircle1, inpolygon, scxsc
from hfrnet.db_tools.db_tables import get_files_list_radialtable

_log = logging.getLogger()

def _update_key(d):
    """Rename result columns and convert to structure"""
    m = {'t': 't', 'net': 'network', 'sta': 'site', 'patterntype': 'beampattern',
         'file_arrival_time': 'arrivaltime', 'lat': 'lat', 'lon': 'lon', 
         'range_res': 'rangeres', 'range_bin_end': 'rangeend', 
         'manufacturer': 'manufacturer', 'dfile': 'file', 'dir': 'dir'}
    return _dict((m.get(key, key), value) for (key, value) in d.items())

def rtvLoadRadials(configObj, siteInfoObj, fileLocObj, rtvInfoObj, landInfoObj, calcTime):
    """
    % RTVLOADRADIALS Loads radial data for RTV processing
    %
    %    radials = rtvLoadRadials( configObj, siteInfoObj, fileLocObj, rtvInfoObj, 
    %                              landInfoObj, calcTime )
    %    returns a structure containing
    %    radial data from all sites for the given hour of RTV processing.
    %    Data are provided for the preferred beam pattern and filtered by
    %    velocity flag (if available), speed threshold, and landmasked.
    %
    %    Only data from 'new' sites that have potential overlap with
    %    neighboring sites are returned. Overlap is determined by using small
    %    circles at each site's origin with radius computed from the site's
    %    range resolution and last range cell. With the exception of reprocessing,
    %    'new' sites are defined as sites whose file arrival time are greater than
    %    or equal to the current rtv state time.
    %
    %    Reprocessing, indicated by the existance of the 'reprocess' field in
    %    configObj bypasses radial selection by arrival time such that all available
    %    radial files for the given timestamp are obtained and all are
    %    considered 'new'.
    %
    %    Previous total solutions for the same domain, resolution, and time are
    %    checked to ensure radial selection parameters are consistent.  During
    %    reprocessing, this function errors out as it is expected that any
    %    previous data has already been removed.  During near real-time
    %    processing, site selection parameters are modified based on previous
    %    runs to ensure consistency.
    %
    %    Inputs:
    %
    %        (configObj, siteInfoObj, fileLocObj, rtvInfoObj, landInfoObj) - Structures 
    %                    containing configuration parameters
    %        calcTime      - Datetime (scalar)
    %
    %    Outputs:
    %
    %     radials - Radial data structure with fields:
    %            isnew
    %            network
    %            site
    %            sitelatitude
    %            sitelongitude
    %            patterntype
    %            manufacturer
    %            file
    %            dir
    %            latitude
    %            longitude
    %            speed
    %            heading
    %            maxrange
    %
    %    Specific configuration fields required by rtvLoadRadials are:
    %
    %        domain
    %        grid_search_radius
    %        max_rad_speed
    %        new_state
    %        site
    %        raddb
    %        land
    %
    %    and, during reprocessing, the following fields are also required:
    %        reprocess
    %
    %
    %    HF-Radar Network
    %    Scripps Institution of Oceanography
    %    Coastal Observing Research and Development Center
    """

    # Initialize return values
    radials = [] # isempty returns true

    # Ensure radial selection consistent with previous run(s)
    # Check if a file already exists
    last = None

    if fileLocObj.mpathfile.is_file():

        # Load previous radial dataset
        try:
            last = read_total_file(fileLocObj.mpathfile, '-mat', 'r')
            errmsg = f'Loaded radial structure from prior run ({fileLocObj.mpathfile})'
            _log.info(errmsg)

        except Exception as e:
            errmsg = (f'Failed to load radial structure from prior run ('
                      f'{fileLocObj.mpathfile}): {str(e)}')
            _log.warning(errmsg)
            _log.warning('Cannot ensure consistent radial selection if results are '
                         'combined with previous run(s)')

    else:
        errmsg = f'{fileLocObj.mpathfile} not found, no pre-existing radial data'
        _log.debug(errmsg)

    # Modify radial selection as needed based on previous run(s)
    if last is not None:
        nMod = 0

        # Loop over each site defined in the config
        for iSiteInfo in siteInfoObj:

            # Look for a site/network match in existing radial data
            siteMatch = ((iSiteInfo.network == np.array([rr.network for rr in last.r])) &
                         (iSiteInfo.name == np.array([rr.site for rr in last.r])))

            if not np.any(siteMatch):
                continue


            # Error out if there is more than one matched record
            if np.count_nonzero(siteMatch) > 1:

                errmsg = (f'Found two records of radial data from {iSiteInfo.network}:'
                          f'{iSiteInfo.name} in previous radial data structure '
                          f'loaded from {fileLocObj.mpathfile}')
                _log.error(errmsg)

            # Check that the patterntypes are consistent
            siteMatch = np.argwhere(siteMatch)[0][0]
            if iSiteInfo.beampattern[0] != last.r[siteMatch].patterntype:

                if 'i' == last.r[siteMatch].patterntype:
                    iSiteInfo.beampattern = 'ideal'

                elif 'm' == last.r[siteMatch].patterntype:
                    iSiteInfo.beampattern = 'measured'

                else:
                    errmsg = (f'Unknown beam pattern type {last.r[siteMatch].patterntype}'
                              f' found for {iSiteInfo.network}:{iSiteInfo.name}'
                              ' in previous radial data structure loaded from '
                              f'{fileLocObj.mpathfile}')
                    _log.error(errmsg)

                errmsg = (f"Modified {iSiteInfo.network }:{iSiteInfo.name} "
                          f"selection to use {iSiteInfo.beampattern} radials for "
                          f"consistency with previous run(s)")
                _log.info(errmsg)

                nMod = nMod + 1

            # Check that useMinutes is consistent
            if iSiteInfo.useMinute != last.r[siteMatch].t.minute:

                iSiteInfo.useMinute = last.r[siteMatch].t.minute

                errmsg = (f'Modified {iSiteInfo.network}:{iSiteInfo.name} '
                          f'selection to use radials from {iSiteInfo.useMinute} '
                          f'minute(s) for consistency with previous run(s)')
                _log.info(errmsg)

                nMod = nMod + 1

        # Logging
        if nMod > 0:
            msg = (f'{nMod} modifications made to radial site parameters based'
                   ' on previous runs')
            _log.info(msg)

        else:
            _log.debug('No modification needed to current radial config based on '
                       'previous runs')

    # Build radial query
    q = []
    results, nfiles = get_files_list_radialtable(configObj, calcTime, siteInfoObj)

    # Note: t +/- 30 min. is a query optimization
    if results:
        q = results

    # Log & remove any records that have NULL where data should be required
    rmRecordIndex = np.zeros(nfiles, dtype=bool)

    for I in range(nfiles):
        
        q[I] = _update_key(q[I])
        fileInfo = q[I]

        if (fileInfo.file == "" or fileInfo.dir == "" or
            np.isnan(fileInfo.lat) or np.isnan(fileInfo.lon) or
            (not configObj.reprocess and (fileInfo.arrivaltime == ""))):
            rmRecordIndex[I] = True
            errmsg = (f'Radialfiles record {fileInfo.network}:{fileInfo.site} '
                      f'({fileInfo.beampattern} {fileInfo.t} is missing required fields,'
                      ' removing from processing')
            _log.warning(errmsg)

    if np.any(rmRecordIndex):
        for I in range(nSite-1, -1, -1):
            if rmRecordIndex[I]:
                del q[I]

    nq = len(q)
    newRadialIndex = None
    # Index new radials
    if configObj.reprocess:
        newRadialIndex = np.ones(nq, dtype=bool)

    else:
        newRadialIndex = np.zeros(nq, dtype=bool)

        for I in range(nq):

            if q[I].arrivaltime >= rtvInfoObj.current_state:

                newRadialIndex[I] = True
                errmsg = (f'New radial from {q[I].network}:{q[I].site} '
                          f'({q[I].beampattern}) arrived at {q[I].arrivaltime}')
                _log.debug(errmsg)

            else:
                errmsg = (f'Obtained radial from {q[I].network}:{q[I].site}'
                          f'({q[I].beampattern})')
                _log.debug(errmsg)

    nNewRadials = np.count_nonzero(newRadialIndex)
    if nNewRadials:

        if configObj.reprocess:
            errmsg = f'{nNewRadials} radial(s) to be reprocessed'
            _log.info(errmsg)

        else:
            errmsg = f'{nNewRadials} new radial(s) to be processed'
            _log.info(errmsg)
    else:
        return radials

    # Find sites that potentially overlap with new data
    loadRadialIndex = np.zeros(nq, dtype=bool)

    # Define small circle radius buffer amount
    #
    # The small circle radius is typically extended beyond the maximum range
    # by ~3% of the range resolution to account for small differences observed
    # between small circle estimates of data range and actual radial locations.
    buf = 0.05

    # Pre-compute small circles
    sc = [_dict({'lat': [], 'lon':[]})]*len(newRadialIndex)
    for I in range(len(newRadialIndex)):

        # Site range
        #   If range resolution or end metadata are either NaN (NULL) or less than zero,
        #   assume metadata is bad or unavailable and fall back to a max range value
        if (q[I].rangeend is None or q[I].rangeres is None or
            q[I].rangeend <= 0 or q[I].rangeres <= 0):

            q[I].siterange = 300 + rtvInfoObj.grid_search_radius

            errmsg = (f'Missing radial range resolution or end from {q[I].network}:'
                      f'{q[I].site}, setting siterange to {q[I].siterange } km')
            _log.warning(errmsg)
        else:
            q[I].siterange = q[I].rangeres * q[I].rangeend + buf * q[I].rangeres + \
                rtvInfoObj.grid_search_radius

        # Small circle using WGS84, adding grid search radius and fraction of
        # range resolution
        sc[I].lat, sc[I].lon = scircle1(q[I].lat, q[I].lon, q[I].siterange)


    # Iterate over each new site
    for I in range(len(newRadialIndex)):

        if not newRadialIndex[I]:
            continue

        # Iterate over every other site
        for J in range(len(newRadialIndex)):

            # Skip self
            if I == J:
                continue

            # Skip sites that have already been selected for loading
            if loadRadialIndex[J]:
                continue

            # Check if this site's origin is inside the new site's domain
            is_in = inpolygon([q[J].lon], [q[J].lat], sc[I].lon, sc[I].lat)
            if is_in[0]:
                loadRadialIndex[I] = True
                loadRadialIndex[J] = True
                continue

            # Check if the new site's origin is inside this site's domain
            is_in = inpolygon([q[I].lon], [q[I].lat], sc[J].lon, sc[J].lat)
            if is_in[0]:
                loadRadialIndex[I] = True
                loadRadialIndex[J] = True
                continue

            # Look for intersection of sites
            ip1, ip2 = scxsc((q[I].lat, q[I].lon), km2deg(q[I].siterange),
                (q[J].lat, q[J].lon), km2deg(q[J].siterange))

            if ip1 is None:
                # No intersection
                continue

            if ip1 == ip2:
                # Tangential intersection
                continue

            # Site pair intersection, plan to load
            loadRadialIndex[I] = True
            loadRadialIndex[J] = True

    # Log results
    for I in range(len(newRadialIndex)):
        if not newRadialIndex[I]:
            continue

        if not loadRadialIndex[I]:
            errmsg = f'No overlap found with new data from {q[I].network}:{q[I].site}'
            _log.info(errmsg)


    nLoadRadials = np.count_nonzero(loadRadialIndex)
    if nLoadRadials:
        errmsg = f'{nLoadRadials} radial files to be loaded for processing'
        _log.info(errmsg)
    else:
        _log.info('No potential data overlap with new radials')
        return radials


    #% Obtain data from sites
    nLand = len(landInfoObj)
    n = 0
    for I in range(len(loadRadialIndex)):
        if not loadRadialIndex[I]:
            continue

        n = n + 1

        # Define local path to radials
        if (configObj.raddb == 'israddirregex' and
            configObj.raddb == 'raddirreplace'):
            q[I].dir = re.sub(configObj.raddb.raddirregex,
                              configObj.raddb.raddirreplace, q[I].dir)
        # FIX: to be removed
        q[I].dir = q[I].dir.replace(str(fileLocObj.radial_remote_dir),
                                    str(fileLocObj.radial_local_dir))
        q[I].fullfile = Path(f"{q[I].dir}/{q[I].file}")

        # Load radial data
        d = None
        try:
            d = rtvReadRadialFile(q[I])
            msg = (f'Loaded {len(d.latitude)} radials from {q[I].file} '
                   f' ({n} of {nLoadRadials})')
            _log.info(msg)

        except Exception as e:
            errmsg = f': {str(e)}'
            _log.error(errmsg)

        if d is None:
            continue

        # VFLG filtering
        if hasattr(d, "vflag"):

            idx = d.vflag == 128
            if nIdx > 0:

                d.latitude = d.latitude[~idx]
                d.longitude = d.longitude[~idx]
                d.speed = d.speed[~idx]
                d.heading = d.heading[~idx]

                if hasattr(d, "range"):
                    d.range = d.range[~idx]
                errmsg = f'Removed {nIdx} velocity flagged radials'
                _log.debug(errmsg)

                if not d.latitude:
                    errmsg = (f'No radial data left from {q[I].file}'
                              f' after velocity flag filtering')
                    _log.info(errmsg)
                    continue

            d.pop('vflag', None)

        # Speed thresholding
        idx = abs(d.speed) > rtvInfoObj.max_rad_speed
        nIdx = np.sum(idx)

        if nIdx > 0:

            d.latitude = d.latitude[~idx]
            d.longitude = d.longitude[~idx]
            d.speed = d.speed[~idx]
            d.heading = d.heading[~idx]

            if hasattr(d, "range"):
                d.range = d.range[~idx]

            errmsg = (f'Removed {nIdx} radials with speed greater than '
                      f'{rtvInfoObj.max_rad_speed} cm/s')
            _log.debug(errmsg)

            if not d.latitude:
                errmsg = f'No radial data left from {q[I].file} after speed thresholding'
                _log.info(errmsg)
                continue


        # Landmasking
        #
        # Approximate data domain as a rectangle
        dLim = [np.max(d.latitude), np.min(d.latitude),
                np.max(d.longitude), np.min(d.longitude)]

        # Loop over each land polygon
        nOverLand = 0

        for J in range(nLand):

            # # If land and data rectangles overlap...
            #---- this is the new land
            if (dLim[0] >= landInfoObj[J]['region'][1] and
                dLim[1] <= landInfoObj[J]['region'][0] and
                dLim[2] >= landInfoObj[J]['region'][3] and
                dLim[3] <= landInfoObj[J]['region'][2]):  ##ok<AND2>

                # ... see if any radials fall inside the land polygon ...
                is_in = inpolygon(d.longitude, d.latitude,
                                  landInfoObj[J]['polygon'][:,0],
                                  landInfoObj[J]['polygon'][:,1])

                # ... and remove any data falling over land
                if np.any(is_in):
                    d.latitude = d.latitude[~is_in]
                    d.longitude = d.longitude[~is_in]
                    d.speed = d.speed[~is_in]
                    d.heading = d.heading[~is_in]

                    if hasattr(d, 'range'):
                        d.range = d.range[~is_in]

                    nOverLand = nOverLand + sum(is_in)




        if nOverLand > 0:
            errmsg = f'Removed {nOverLand} radials falling over land'
            _log.debug(errmsg)

            if len(d.latitude) == 0:
                errmsg = f'No radial data left from {q[I].file} after land masking'
                _log.info(errmsg)
                continue



        # Save loaded data
        if not radials:
            ri = 0

        radials.append(RadialInfo())
        radials[ri].isNew = newRadialIndex[I]
        radials[ri].time = q[I].t
        radials[ri].network = q[I].network
        radials[ri].site = q[I].site
        radials[ri].sitelatitude = q[I].lat
        radials[ri].sitelongitude = q[I].lon
        radials[ri].patterntype = q[I].beampattern
        radials[ri].manufacturer = q[I].manufacturer
        radials[ri].file = q[I].file
        radials[ri].dir = q[I].dir
        radials[ri].latitude = d.latitude
        radials[ri].longitude = d.longitude
        radials[ri].speed = d.speed
        radials[ri].heading = d.heading

        # maxrange field
        if hasattr(d, "range"):
            if q[I].rangeres is None or q[I].rangeres <= 0:

                # Use 6km as range resolution if unavailable
                radials[ri].maxrange = np.max(d.range) + buf * 6
                errmsg = (f'Missing radial range resolution from {q[I].network}:'
                          f' {q[I].site}, using 6km range resolution to estimate maxrange')
                _log.warning(errmsg)

            else:

                # Use all available information
                radials[ri].maxrange = max(d.range) + buf * q[I].rangeres


        else:

            # Use 300km as overall max range when range isn't available
            radials[ri].maxrange = 300
            errmsg = (f'Missing radial range data from {q[I].file}'
                      ', setting maxrange to 300 km')
            _log.info(errmsg)


        ri = ri + 1

    return radials
