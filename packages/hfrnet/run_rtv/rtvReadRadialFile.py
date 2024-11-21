"""rtvReadRadialFile"""

import re
import logging
import numpy as np
from hfrnet.utils_funcs.lib_rtv import RadialInfo
from hfrnet.utils_funcs.math_funcs import azimuth, cart2pol

_log = logging.getLogger()

def rtvReadRadialFile(inFile):
    """
    % RTVREADRADIALFILE Read lluv radial file to structure
    %
    %    radialObj = rtvReadRadialFile( inFile ) reads the radial file defined in the
    %    structure and returns a structure containing radial data used during RTV
    %    processing. The radial file format must be lluv.  The radar location is
    %    used to compute speed and heading fields from radial velocity if they
    %    aren't directly available in the file.
    %
    %    Input used:
    %        inFile.fullfile - radial file name (including the full path if not on
    %                     the MATLAB path)
    %        inFile.lat      - radar latitude (deg N)
    %        inFile.lon      - radar longitude (deg E)
    %
    %    Output:
    %        r - Structure of radial velocity data including the fields:
    %
    %            latitude
    %            longitude
    %            speed
    %            heading
    %            range (if available)
    %            vflag (if available)
    %
    %    The heading is returned in polar convention (counterclockwise from the
    %    +x axis).  The range and vflag fields are only returned if they're
    %    available in the file.
    %
    %    See also RTVLOADRADIALS
    %
    %    HF-Radar Network
    %    Scripps Institution of Oceanography
    %    Coastal Observing Research and Development Center
    """

    NUM_DEGREES = 360
    RIGHT_ANGLE = 90

    # Check file exists
    if not (inFile.fullfile).is_file():
        msg = f'readRadialFile:fileNotFound {inFile.fullfile} not found'
        _log.error(msg)


    # Get LLUV Table Column Names
    # Note: found it was faster to just get the header info then use LOAD than
    # it was to continue with the open file and fgetl to load the rest of the data.
    try:
        fid = open(inFile.fullfile, 'r')
    except Exception as e:
        msg = f'readRadialFile:fopenErr {str(e)}'
        _log.error(msg)

    tableType = ''
    columnIndex = {}
    while 1:

        tline = fid.readline()

        if not tline:
            break

        # Look for column names if the current table is the right type
        if tableType == 'LLUV':
            m = re.match(r'^%TableColumnTypes:((\s*\w+\s*)+)', tline)

            # Table column name match; save & break
            if m is not None:
                m = m.groups()[0].strip().split()
                for I in range(len(m)):
                    columnIndex[m[I]] = I

                break


        # Keep looking for the LLUV table if we haven't found it yet
        else:
            m = re.match(r'^%TableType:\s*LLUV', tline)
            if m is not None:
                tableType = 'LLUV'

    fid.close()

    # Check we got required colunm names
    if len(columnIndex) == 0:
        _log.error('readRadialFile:noColumnName: No column names were found')
    elif 'LOND' not in columnIndex:
        _log.error('readRadialFile:missingColumnName: Longitude column (LOND) not found')
    elif 'LATD' not in columnIndex:
        _log.error('readRadialFile:missingColumnName: Latitude column (LATD) not found')
    elif 'HEAD' not in columnIndex:
        _log.warning('readRadialFile:missingColumnName: '
                     'Radial heading column (HEAD) not found')
    elif 'VELO' not in columnIndex:
        _log.warning('readRadialFile:missingColumnName: Radial velocity'
                     ' column (VELO) not found')
    elif 'RNGE' not in columnIndex:
        _log.warning('readRadialFile:missingColumnName: Radial range '
                     'column (RNGE) not found')


    # Load data
    radialInfoObj = RadialInfo()
    d = np.loadtxt(inFile.fullfile, comments="%")

    if d.size == 0:
        _log.error('readRadialFile:noDataLoaded: '
                   'Load function returned an empty array. No data in radial file?')

    else:
        # Radial location
        radialInfoObj.latitude = d[:, columnIndex['LATD']]
        radialInfoObj.longitude = d[:, columnIndex['LOND']]

        # Radial heading (toward origin)
        if 'HEAD' in columnIndex:

            # Convert deg CW from N to deg CCW from E
            radialInfoObj.heading = (RIGHT_ANGLE - d[:, columnIndex['HEAD']]) % NUM_DEGREES

        else:

            # Compute bearing from each radial to the origin
            az = azimuth(radialInfoObj.latitude, radialInfoObj.longitude,
                         inFile.lat, inFile.lon)

            # Convert deg CW from N to deg CCW from E
            radialInfoObj.heading = (RIGHT_ANGLE - az) % NUM_DEGREES

        # Radial speed
        if "VELO" in columnIndex:
            radialInfoObj.speed = d[:, columnIndex['VELO']]

        elif 'VELU'  in columnIndex and 'VELV' in columnIndex:

            # Convert radial vector to polar coords (speed and bearing)
            rdir, rspd = cart2pol(d[:, columnIndex['VELU']], d[:, columnIndex['VELV']])

            # Convert rad to deg
            rdir = np.rad2deg(rdir)

            # Find difference in bearing (binary result, either 0 or 180)
            dd = round(np.abs(radialInfoObj.heading - rdir)) % NUM_DEGREES

            # 180 deg differences imply direction away from radar which gets a
            # negative value by convention
            mask = dd > 10 # allow for some error observed in small velocities
            rspd[mask] = -rspd[mask]
            radialInfoObj.speed = rspd

        else:
            _log.error('readRadialFile:missingColumnName:  '
                       'Radial velocity components (VELU & VELV) not found')

        # Radial range (from origin)
        if 'RNGE' in columnIndex:
            radialInfoObj.range = d[:, columnIndex['RNGE']]

        # Radial flags
        if 'VFLG' in columnIndex:
            radialInfoObj.vflag = d[:, columnIndex['VFLG']]

    return radialInfoObj
