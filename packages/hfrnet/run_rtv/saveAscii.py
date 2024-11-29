"""saveAscii"""

import logging
import numpy as np

_log = logging.getLogger()


def saveAscii(rtvProcessObj, fileLocObj, rtvInfoObj, totObj):
    '''
    % SAVEASCII Export velocity data to ASCII file
    %
    %    saveAscii(rtvProcessObj, fileLocObj, rtvInfoObj,totObj) saves rtvproc
    %    total velocity data products to a simple ASCII file consisting of 4 columns:
    %    latitude, longitude, u (eastward) velocity, and v (northward)
    %    velocity.
    %    The process name is obtained from the configuration
    %    structure's process field.  For rtv processing, the velocities are
    %    filtered by the rtv field's uwls_max_hdop_ascii value prior on export.
    %
    %    HF-Radar Network
    %    Scripps Institution of Oceanography
    %    Coastal Observing Research and Development Center
    '''

    mask = None
    data = None
    name = rtvProcessObj.name.casefold()
    if name == 'rtv':
        mask = totObj.hdop <= rtvInfoObj.uwls_max_hdop_ascii
        data = np.array([totObj.lat[mask], totObj.lon[mask],
                         totObj.u_xvel[mask], totObj.v_yvel[mask]])

    elif name in ['stc', 'lta']:
        mask = np.logical_not(np.isnan(totObj.uAvg))
        lat = totObj.grid.ocean_xy[1, :]
        lon = totObj.grid.ocean_xy[0, :]
        data = np.array([lat[mask], lon[mask],
                         totObj.uAvg[mask], totObj.vAvg[mask]])

    else:
        msg = f"Undefined process {name}"
        _log.error(msg)
        raise ValueError(msg)

    try:
        np.savetxt(fileLocObj.asciipathfile, data.T, fmt='%8.4f %9.4f %7.0f %7.0f')
        msg = f"Saved file {fileLocObj.asciipathfile}"
        _log.info(msg)
    except Exception as e:
        msg = f"Error saving {fileLocObj.asciipathfile}: {str(e)}"
        _log.error(msg)
