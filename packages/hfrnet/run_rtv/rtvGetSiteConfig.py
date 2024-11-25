"""rtvGetSiteConfig"""

import logging
from copy import deepcopy
import numpy as np
from hfrnet.utils_funcs.lib_rtv import SiteInfo
from hfrnet.utils_funcs.database import Database

_log = logging.getLogger()

def rtvGetSiteConfig(configObj, siteInfoObj, t):
    """
    % RTVGETSITECONFIG Obtains time-dependent site configurations
    %
    %    siteConfig = rtvGetSiteConfig( configObj, siteInfoObj,  time) obtains
    %    time-dependent HF-RADAR site configurations from the database for the
    %    domain, resolution, and time being processed.
    %
    %    Required configuration structure fields are:
    %
    %        domain
    %        resolution
    %        confdb
    %
    %    Sites obtained and their parameters are written to the site field in
    %    the configuration object.
    %
    %
    %    HF-Radar Network
    %    Scripps Institution of Oceanography
    %    Coastal Observing Research and Development Center
    """

    # Connect to the configuration database
    conn = Database(user=configObj.confdb.user,
                    password=configObj.confdb.password)
    conn.connect()
    conn.use('rtvproc')

    if not conn.is_open():
        errmsg = 'Failed to connect to configuration database'
        _log.error(errmsg)

    # Build & execute query
    sqlquery = (
        'SELECT s.network,s.name,c.beampattern,c.use_radial_minute,s.id '
        'FROM site s '
        'JOIN site_config c ON c.site_id = s.id '
        'JOIN domain d ON c.domain_id = d.id '
        'JOIN resolution r ON c.resolution_id = r.id '
        f"WHERE d.name LIKE '{configObj.domain}' "
        f"AND r.name LIKE '{configObj.resolution}' "
        f"AND c.start_time <= '{t}' AND "
        f"( c.end_time > '{t}' OR ISNULL(c.end_time) )")

    try:
        results = conn.sql(sqlquery, as_dict=1)

    except Exception as e:

        errmsg = f'Configuration database query error {str(e)}'
        _log.error(errmsg)

    conn.close()
    nRows = len(results)

    if nRows == 0:
        # No sites configured
        return configObj

    if nRows > 0:
        # Verify we got a unique list of sites (i.e. no duplicate configs for a
        # given site)
        ids = [r.id for r in results]
        _, idx = np.unique(ids, return_index=True)
        if len(ids) != len(idx):
            idx = np.setxor1d(idx, np.arange(len(ids)))
            errmsg = (f'Found {len(idx)} site(s) with overlapping configurations; '
                f'{",".join([results[i].name for i in idx])}')
            _log.error(errmsg)

        for I in range(nRows):
            siteInfoObj_temp = SiteInfo()
            siteInfoObj_temp.network = results[I].network
            siteInfoObj_temp.name = results[I].name
            siteInfoObj_temp.beampattern = results[I].beampattern
            siteInfoObj_temp.useMinute = results[I].use_radial_minute

            siteInfoObj.append(deepcopy(siteInfoObj_temp))

            # Check minute range
            if siteInfoObj[I].useMinute > 59:
                errmsg = (f'{configObj.site.network[I]}:{configObj.site.name[I]}'
                          f' useMinute value of {configObj.site.useMinute[I]} '
                          f'is out of range. Valid range is [0-59]')
                _log.error(errmsg)

    return siteInfoObj
