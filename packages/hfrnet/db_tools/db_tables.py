import logging
from hfrnet.utils_funcs.lib_rtv import DatabaseError, RtvProcess
from hfrnet.db_tools.db_manager import db_manager
from datetime import timedelta
_log = logging.getLogger()


def read_domain(db_class, configureVals):
        # Check for valid domain
        sqlquery = (f"SELECT description, id FROM domain WHERE name = "
                    f"'{configureVals.domain}'")
        result_list = db_class.get_query(sqlquery)
        # % Expect exactly one record to match
        n = len(result_list)
        if n == 0:
            _log.error(f"{configureVals.domain} is not defined in the configuration "
                        f"database")
            db_class.close()
            raise DatabaseError()
        elif n > 2:
            _log.error(f"{configureVals.domain} returned {n} rows where only one expected")
            db_class.close()
            raise DatabaseError()
        
        configureVals.domain_id = result_list['id'][0]
        # --- success
        
        
def read_resolution(db_class, configureVals):
        # %% Check for valid resolution
        sqlquery = (f"SELECT id FROM resolution WHERE name = "
                    f"'{configureVals.resolution}'")
        result_list = db_class.get_query(sqlquery)
        
        # % Expect exactly one record to match
        n = len(result_list)
        if n != 1:
            if n == 0:
                    _log.error(f"Resolution {configureVals.resolution} is not defined in the "
                                f"database for domain {configureVals.domain}")
                    db_class.close()
                    raise DatabaseError()
            else:
                    _log.error(f"Resolution query for {configureVals.domain} : "
                                f"{configureVals.resolution} "
                                f"returned {n} rows where only one expected")
                    db_class.close()
                    raise DatabaseError()
        configureVals.resolution_id = result_list['id'][0]
	
def read_methods(db_class, mconfigurevals, mrtvparameters, mstcparameters,
                 mltaparameters, process_list):
        # Get realtime process(es) to run, the methods table
        sqlquery = f"SELECT p.name,m.name,m.description,rp.save_as FROM realtime_process rp "\
                   f"JOIN domain d ON d.id = rp.domain_id "\
                   f"JOIN resolution r ON r.id = rp.resolution_id "\
                   f"JOIN process p ON p.id = rp.process_id "\
                   f"JOIN combine_method m ON m.id = p.combine_method_id "\
                   f"WHERE rp.status = 'enabled' "\
                   f"AND d.name = '{mconfigurevals.domain}' "\
                   f"AND r.name = '{mconfigurevals.resolution}' "\
                   f"ORDER BY rp.priority"

        result_list = db_class.get_query(sqlquery)
        # % Return if there are no processes found to run
        
        n = len(result_list['name'])
        if n == 0:
            _log.error(f"there are no processes found to run")
            db_class.close()
            raise DatabaseError()
                
        # RTV uwls Unweighted Least Squares ascii,netcdf
        # STC uwls Unweighted Least Squares ascii,netcdf
        # LTA uwls Unweighted Least Squares ascii,netcdf

        _log.info("--------------------------------------------------------------")
        
        for i in range(n):
            process_list.append(
                RtvProcess(result_list['name'][i], result_list['name_2'][i],
                           result_list['description'][i], result_list['save_as'][i]))
        
        for row in process_list:
            _log.info(f"{row.name}, {row.method}, {row.methoddesc}, {row.saveas}")
        
        for row in process_list:
            processname = row.name
            methodname = row.method
            if processname.lower() == "rtv":
                _log.info("--rtv--")
                sqlquery = f"SELECT " \
                           f"p.max_age,p.min_rad_sites,p.min_radials,p.max_rad_speed," \
                           f"p.grid_search_radius,p.max_rtv_speed,p.uwls_max_hdop," \
                           f"p.uwls_max_hdop_ascii,p.uwls_max_hdop_nc " \
                           f"FROM rtv_parameter p " \
                           f"JOIN domain d ON d.id = p.domain_id " \
                           f"JOIN resolution r ON r.id = p.resolution_id " \
                           f"JOIN combine_method m ON m.id = p.combine_method_id " \
                           f"WHERE m.name = '{methodname.lower()}' " \
                           f"AND d.name = '{mconfigurevals.domain}' " \
                           f"AND r.name = '{mconfigurevals.resolution}'"
                
                result_list = db_class.get_query(sqlquery)
                
                nrows = len(result_list['max_age'])
                
                
                if nrows == 0:
                    _log.error(f"RTV parameters are not defined for "
                               f"{mconfigurevals.resolution} and {mconfigurevals.domain}")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows > 1:
                    _log.error(f"RTV parameter query for {mconfigurevals.domain} "
                               f"{mconfigurevals.resolution} returned {n} rows where only "
                               f"one expected")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows == 1:
                    # collect the parameters
                    tmp = dict(result_list)
                    mrtvparameters.max_age = tmp['max_age'][0]
                    mrtvparameters.grid_search_radius = tmp['grid_search_radius'][0]
                    mrtvparameters.max_rad_speed = tmp['max_rad_speed'][0]
                    mrtvparameters.max_rtv_speed = tmp['max_rtv_speed'][0]
                    mrtvparameters.min_rad_sites = tmp['min_rad_sites'][0]
                    mrtvparameters.min_radials = tmp['min_radials'][0]
                    mrtvparameters.uwls_max_hdop = tmp['uwls_max_hdop'][0]
                    mrtvparameters.uwls_max_hdop_ascii = tmp['uwls_max_hdop_ascii'][0]
                    mrtvparameters.uwls_max_hdop_nc = tmp['uwls_max_hdop_nc'][0]
            
            # ------------------------------------------------------------
            elif processname.lower() == "stc":
                _log.info("--stc--")
                sqlquery = f"SELECT " \
                           f"p.min_temporal_coverage,p.max_age,p.max_error  " \
                           f"FROM stc_parameter p " \
                           f"JOIN domain d ON d.id = p.domain_id " \
                           f"JOIN resolution r ON r.id = p.resolution_id " \
                           f"JOIN combine_method m ON m.id = p.combine_method_id " \
                           f"WHERE m.name = '{methodname.lower()}' " \
                           f"AND d.name = '{mconfigurevals.domain}' " \
                           f"AND r.name = '{mconfigurevals.resolution}'"
                result_list = db_class.get_query(sqlquery)
                
                nrows = len(result_list['max_error'])
                _log.info(nrows)
                if nrows == 0:
                    _log.error(f"STC parameters are not defined for "
                               f"{mconfigurevals.resolution} and {mconfigurevals.domain}")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows > 1:
                    _log.error(f"STC parameter query for {mconfigurevals.domain} "
                               f"{mconfigurevals.resolution} returned {n} rows where only "
                               f"one expected")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows == 1:
                    # collect the parameters
                    tmp = dict(result_list)
                    mstcparameters.min_temporal_coverage = tmp['min_temporal_coverage'][0]
                    mstcparameters.max_age = tmp['max_age'][0]
                    mstcparameters.max_error = tmp['max_error'][0]
                    # ------------------------------------------------------------
            elif processname.lower() == "lta":
                _log.info("--lta--")
                sqlquery = f"SELECT " \
                           f"p.min_month_temporal_coverage,p.min_year_temporal_coverage," \
                           f"p.max_error  " \
                           f"FROM lta_parameter p " \
                           f"JOIN domain d ON d.id = p.domain_id " \
                           f"JOIN resolution r ON r.id = p.resolution_id " \
                           f"JOIN combine_method m ON m.id = p.combine_method_id " \
                           f"WHERE m.name = '{methodname.lower()}' " \
                           f"AND d.name = '{mconfigurevals.domain}' " \
                           f"AND r.name = '{mconfigurevals.resolution}'"
                result_list = db_class.get_query(sqlquery)
                
                nrows = len(result_list['max_error'])
                _log.info(nrows)
                if nrows == 0:
                    _log.error(f"LTA parameters are not defined for "
                               f"{mconfigurevals.resolution} and {mconfigurevals.domain}")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows > 1:
                    _log.error(f"LTA parameter query for {mconfigurevals.domain} "
                               f"{mconfigurevals.resolution} returned {n} rows where only "
                               f"one expected")
                    db_class.close()
                    raise DatabaseError()
                
                elif nrows == 1:
                    # collect the parameters
                    # mltaparameters = dict(result_list)
                    tmp = dict(result_list)
                    mltaparameters.min_month_temporal_coverage = \
                    tmp['min_month_temporal_coverage'][0]
                    mltaparameters.min_year_temporal_coverage = \
                    tmp['min_year_temporal_coverage'][0]
            
            else:
                _log.error(f"Unknown process {processname}"
                           f"obtained, no parameters obtained")
                db_class.close()
                raise DatabaseError()

def read_site_table(configObj):
    
    # Connect to the configuration database
    
    with db_manager(configObj.confdb) as db_class:
        
        # Build & execute query
        sqlquery = (
            'SELECT s.network,s.name '
            'FROM site s '
            'JOIN site_config c ON s.id = c.site_id '
            'JOIN domain d ON c.domain_id = d.id '
            'JOIN resolution r ON c.resolution_id = r.id '
            f"WHERE d.name LIKE '{configObj.domain}' "
            f"AND r.name LIKE '{configObj.resolution}' "
            'GROUP BY s.network,s.name')
        
        sites_list = db_class.get_query(sqlquery)

    # % Expect exactly one record to match
    nRows = len(sites_list['name'])
    
    if nRows == 0:
        errmsg = (f'No sites defined for RTV {configObj.resolution} '
                  f'{configObj.domain} processing')
        _log.error(errmsg)

        raise DatabaseError()

    elif nRows > 0:
        msg = f'Found {nRows} sites associated with {configObj.domain} {configObj.resolution}'
        _log.info(msg)
    return sites_list
    # ------------------------------------

def read_files_times_radialtable(configObj, rtvInfoObj, sites_list, minTime ):
    # Check for valid domain
    # Connect to the configuration database
    with db_manager(configObj.raddb) as db_class:
    
        # Build & execute query
        sqlquery = ('SELECT FROM_UNIXTIME(r.time) '
                    'FROM radialfiles r '
                    'JOIN network n ON n.network_id = r.network_id '
                    'JOIN site s ON s.site_id = r.site_id '
                    f"WHERE (r.file_arrival_time >= '{rtvInfoObj.current_state}') "
                    f"AND r.file_arrival_time < '{rtvInfoObj.new_state}' "
                    f"AND FROM_UNIXTIME(r.time) >= '{minTime}' "
                    'AND ( ' )
        # Site conditions
        nSite = len(sites_list)
        for i in range(nSite):
    
            # Network and site
            network_tmp = sites_list["network"][i]
            name_tmp = sites_list["name"][i]
            sqlquery = (f'{sqlquery}'
                        f"( n.net = '{network_tmp}' AND s.sta = '{name_tmp}')")
    
            # End statement
            if i == nSite - 1:
                sqlquery = f"{sqlquery} )"
            else:
                sqlquery = f"{sqlquery} OR "

        time_list = db_class.get_query(sqlquery)
    
    # % Expect exactly one record to match
    nRows = len(time_list['FROM_UNIXTIME(r.time)'])
    
    msg = f'Found {nRows} sites associated with {configObj.domain} {configObj.resolution}'
    _log.info(msg)
    return time_list['FROM_UNIXTIME(r.time)']
    # ------------------------------------

def get_files_list_radialtable(configObj, calcTime, siteInfoObj):
    # Check for valid domain
    # Connect to the configuration database
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
    
    with db_manager(configObj.raddb) as db_class:
        sqlquery = ('SELECT '
                    'FROM_UNIXTIME(r.time) AS t,n.net,s.sta,patterntype,file_arrival_time,'
                    'lat,lon,range_res,range_bin_end,manufacturer,dfile,dir '
                    'FROM radialfiles r '
                    'JOIN network n ON n.network_id = r.network_id '
                    'JOIN site s ON s.site_id = r.site_id '
                    f"WHERE FROM_UNIXTIME(r.time) >= '{calcTime - timedelta(minutes=30)}' "
                    f"AND FROM_UNIXTIME(r.time) < '{calcTime + timedelta(minutes=30)}' ")
        
        # Site conditions
        nSite = len(siteInfoObj)
        
        if nSite > 0:
            sqlquery = f"{sqlquery}AND ( "
        for i in range(nSite):
            # Network and site
            network_temp = siteInfoObj['network'][i]
            name_temp = siteInfoObj['name'][i]
            beampattern_temp = siteInfoObj['beampattern'][i]
            useMinute_temp = siteInfoObj['useMinute'][i]
            sqlquery = (f'{sqlquery}'
                        f"( n.net = '{network_temp}' AND s.sta = '{name_temp}' ")
            
            # Beampattern
            if beampattern_temp == 'ideal':
                sqlquery = f"{sqlquery}AND r.patterntype = 'i' "
            elif beampattern_temp == 'measured':
                sqlquery = f"{sqlquery}AND r.patterntype = 'm' "
            else:
                errmsg = f'Unknown beam pattern type {beampattern_temp}'
                _log.error(errmsg)
            
            # Radial timestamp
            if useMinute_temp == 0:
                tr = calcTime.strftime(DATETIME_FORMAT)
            elif useMinute_temp > 0 and useMinute_temp < 30:
                tr = (calcTime + timedelta(minutes=useMinute_temp)).strftime(
                    DATETIME_FORMAT)
            elif useMinute_temp >= 30 and useMinute_temp < 60:
                tr = ((calcTime - timedelta(minutes=60 - useMinute_temp)).
                      strftime(DATETIME_FORMAT))
            else:
                tr = ""
                errmsg = (
                    f'useMinute value of {useMinute_temp} is out of range '
                    f'for site {network_temp}:{name_temp}. Value must [0-59]')
                _log.error(errmsg)
            
            sqlquery = f"{sqlquery}AND FROM_UNIXTIME(FLOOR(r.time/60)*60) = '{tr}')"
            
            # End statement
            if i == nSite - 1:
                sqlquery = f"{sqlquery})"
            else:
                sqlquery = f"{sqlquery} OR "
        
        files_list = db_class.get_query(sqlquery)
        
        # % Expect exactly one record to match
        nRows = len(files_list['name'])
        
        if nRows == 0:
            errmsg = f'No match found in the radial table'
            _log.error(errmsg)
            
    return files_list
    
    
    
