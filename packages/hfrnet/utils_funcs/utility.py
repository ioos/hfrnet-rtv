"""Contains functions needed for processing"""

import os
from datetime import datetime, timedelta, timezone, date, time
import calendar
import logging
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
import netCDF4 as nc4
from dateutil import parser
import h5py

from hfrnet.utils_funcs.lib_rtv import RtvProcess, Grid
from hfrnet.utils_funcs import constsHFR
from hfrnet.db_tools.db_tables import get_state_time
from hfrnet.run_rtv.saveNetcdf import loadNetcdf

_log = logging.getLogger()


class _dict(dict):
    """dict like object that exposes keys as attributes"""
    def __getattr__(self, key):
        if key not in self or key.startswith("__"):
            raise AttributeError()
        ret = self.get(key, None)
        return ret
    def __setattr__(self, key, value):
        self[key] = value
    def __getstate__(self):
        return self
    def __setstate__(self, d):
        self.update(d)
    def update(self, d=None, **kwargs):
        """update and return self -- the missing dict feature in python"""
        if d:
            super().update(d)
        if kwargs:
            super().update(kwargs)
        return self

    def copy(self):
        return _dict(dict(self).copy())

def process_record(d):
    """gets info of processes"""
    if hasattr(d, 'keys'):
        keys = [k for k in d.keys() if not k.startswith('__')]
        data = _dict()
        for k in keys:
            data[k] = process_record(d[k])
        return data

    if not hasattr(d, 'dtype'):
        return d
    if d.dtype.names is None:
        if len(d) == 1 and d.dtype.name == 'object':
            return process_record(d[0])
        if hasattr(d, 'shape'):
            if len(d.shape) <= 1 or sorted(d.shape)[-2] == 1:
                d = np.array(d).flatten()
        return d
    data = _dict()
    for name in d.dtype.names:
        data[name] = process_record(d[name])
    return data

def read_total_file(filename):
    """read total radial file"""
    data = {'info': {}, 'data': {}}
    try:
        try:
            raw = loadmat(filename)
            data['info']['version'] = raw.get('__version__', '')
            data['info']['header'] = raw.get('__header__', '')
            data['info']['globals'] = raw.get('__globals__', '')

            data['data'] = process_record(raw)
        except Exception:
            _log.info("Loading netCDF4 file")
            data = loadNetcdf(filename)

    except Exception as e:
        msg = f"Could not load {filename}: {e}"
        _log.error(msg)

    return data

#------------------------------------------------
#------------------------------------------------
#------------------------------------------------
def generate_time_spans(stime, etime):
    """
    
    :param stime: start time
    :param etime: end time
    :return: numpy array of times
    # Function to generate numpy array of 1 hr time spans
 
    """
    # Convert the input strings to datetime objects
    start_date = datetime.strptime(stime, '%Y%m%d%H%M%S%f')
    start_date = start_date.replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(etime, '%Y%m%d%H%M%S%f')
    end_date = end_date.replace(tzinfo=timezone.utc)

    # Generate the time spans
    time_spans = []
    current_time = start_date
    while current_time <= end_date:
        time_spans.append(current_time)
        current_time += timedelta(hours=1)

    # Convert the list to a numpy array
    time_spans_array = np.array(time_spans)

    return time_spans_array
#------------------------------------------------
#------------------------------------------------
#------------------------------------------------
# Define a function to convert strings to floats and integers

def convert_numbers(dictobj):
    """
    
    :param dictobj: is the class of a single region with parameters:
    region, polygon, length in string format
    :return: dictobj with all strs converted into numbers
    """

    #-- convert str to floats
    for i in range(len(dictobj['region'])):
        dictobj['region'][i] = float(dictobj['region'][i])

    for i in range(len(dictobj['polygon'])):
        dictobj['polygon'][i] = float(dictobj['polygon'][i])
    dictobj['length'] = int(dictobj['length'])

    #-- convert into numpy arrays
    dictobj['polygon'] = (np.array(dictobj['polygon']).reshape(dictobj['length'], 2,
                                                               order='F'))
    dictobj['region'] = np.array(dictobj['region'])
    return dictobj


def load_land(mfile, domain):
    """
    Read the land json file given the domain and put it in an array of dictionary
    """
    dicts = []
    # Read JSON data from a file
    with open(f"{mfile}/{domain}.json", 'r') as file:
        dicts = json.load(file, object_hook=convert_numbers)

    return dicts

#------------------------------------------------
#------------------------------------------------
def load_grid(mfile, domain, res, rtvInfoObj):
    """
    Read the grid netcdf file given the domain and res and put it in an array of
    dictionary
    """
    scircle_xfield = ""
    scircle_yfield = ""
    if rtvInfoObj.grid_search_radius == np.floor(rtvInfoObj.grid_search_radius):
        scircle_xfield = f"ocean_x_scircle{rtvInfoObj.grid_search_radius:.0f}km"
        scircle_yfield = f"ocean_y_scircle{rtvInfoObj.grid_search_radius:.0f}km"

    elif rtvInfoObj.grid_search_radius * 1000 == np.floor(
            rtvInfoObj.grid_search_radius * 1000):
        scircle_xfield = f"ocean_x_scircle{rtvInfoObj.grid_search_radius * 1000:.0f}m"
        scircle_yfield = f"ocean_y_scircle{rtvInfoObj.grid_search_radius * 1000:.0f}m"

    else:
        msg = (f"Invalid grid search radius of {rtvInfoObj.grid_search_radius}"
               "km. Value must be a whole number when represented in meters")
        _log.fatal(msg)
        raise ValueError(msg)

    grid = Grid()
    with nc4.Dataset(f"{mfile}/{domain}{res}.nc", 'r') as ds:

        grid.x_range = np.array(ds.variables["x_range"][:])
        grid.y_range = np.array(ds.variables["y_range"][:])

        dd = np.array(ds.variables["dd"][:])
        grid.dx = dd[0]
        grid.dy = dd[1]
        grid.size = np.array(ds.variables["size"][:])
        grid.ocean_indices = np.array(ds.variables["ocean_indices"][:])
        grid.ocean_xy = np.array(ds.variables["ocean_xy"][:,:])
        setattr(grid, scircle_xfield,
                np.array(ds.variables[f"{scircle_xfield}"][:, :]))
        setattr(grid, scircle_yfield,
                np.array(ds.variables[f"{scircle_yfield}"][:, :]))

        grid.resolution_km  = ds.getncattr('resolution_km')
        grid.projection  = ds.getncattr('projection')
        return grid

def now_hour(inTime = None):
    """ Returns datetime at top of current hour"""
    if inTime:
        t = inTime
    else:
        t = datetime.now(timezone.utc)
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour)

def eomday(t):
    """Gets end of month"""
    days_in_month = calendar.monthrange(t.year, t.month)[1]
    return datetime(t.year, t.month, days_in_month)

def now_second(inTime = None):
    """ Returns current datetime to nearest second, no microsecond"""
    if inTime:
        t = inTime
    else:
        t = datetime.now(timezone.utc)
    return t.replace(second=t.second, microsecond=0, minute=t.minute,
                     hour=t.hour)

def hour_range(start, end, step=1):
    """ranges of hours"""
    cur = start
    while cur < end:
        yield cur
        cur += timedelta(hours=step)

def next_month_start(t):
    """return the start day of the next month"""
    return (datetime(year=t.year, month=t.month, day=1) +
            timedelta(days=32)).replace(day=1)

def next_month(t):
    """return the next month"""
    try:
        nextmonthdate = t.replace(month=t.month+1)
    except ValueError:
        if t.month == 12:
            nextmonthdate = t.replace(year=t.year+1, month=1)
        else:
            # next month is too short to have "same date"
            nextmonthdate = eomday(t.replace(month=t.month+1, day=1))
    return nextmonthdate

def prev_month_start(t):
    """return the start day of the prev month"""
    return (datetime(year=t.year, month=t.month, day=1) + timedelta(days=-1)).replace(day=1)

def prev_month(t):
    """return the previous month's date"""
    try:
        prevmonthdate = t.replace(month=t.month-1)
    except ValueError:
        if t.month == 1:
            prevmonthdate = t.replace(year=t.year-1, month=12)
        else:
            # prev month is too short to have "same date"
            prevmonthdate = eomday(t.replace(month=t.month-1, day=1))
    return prevmonthdate

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S.%f"
DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
def get_datetime(datetime_str=None):
    """get datetime in different instances"""
    if not datetime_str:
        return datetime.now(timezone.utc)

    if isinstance(datetime_str, (datetime, timedelta)):
        return datetime_str

    if isinstance(datetime_str, (list, tuple)):
        return datetime(datetime_str)

    if isinstance(datetime_str, date):
        return datetime.combine(datetime_str, time())

    # dateutil parser does not agree with dates like 0000-00-00
    if not datetime_str or (datetime_str or "").startswith("0000-00-00"):
        return None

    try:
        return datetime.strptime(datetime_str, DATETIME_FORMAT)
    except ValueError:
        return parser.parse(datetime_str)


def set_history(A, msg):
    """ Append to NetCDF history"""
    if not hasattr(A, 'history'):
        A.history = []
        h = _dict()
        h.timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        h.program = os.path.basename(__file__)
        h.user = os.getenv('USER') or 'unknown user'
        h.message = msg
        A.history.append(h)

def get_processes():
    """
       Get a list of processes based on the input time
    """
    process_list = []
    stdRtvProcess = RtvProcess()
    stdRtvProcess.name = "rtv"
    stdRtvProcess.method = "uwls"
    stdRtvProcess.methoddesc = "Unweighted Least Squares"
    stdRtvProcess.saveas = "ascii,netcdf"
    process_list.append(stdRtvProcess)

    stdRtvProcess2 = RtvProcess()
    stdRtvProcess2.name = "stc"
    stdRtvProcess2.method = "uwls"
    stdRtvProcess2.methoddesc = "Unweighted Least Squares"
    stdRtvProcess2.saveas = "ascii,netcdf"
    process_list.append(stdRtvProcess2)


def load_mat(filename):
    data = {'info': {}, 'data': {}}
    try:
        try:
            raw = loadmat(filename)
        except:
            raw = h5py.File(filename,'r')

        data['info']['version'] = raw.get('__version__', '')
        data['info']['header'] = raw.get('__header__', '')
        data['info']['globals'] = raw.get('__globals__', '')

        data['data'] = process_record(raw)
    except:
        _log.info("Could not load file")

    return data

#########################################################################
def create_CCAP_filename_s_e(stime, etime, alg_ver, unit_name, ext):
    """
    :param config_dict: contains the yaml config file
    :return: the ccap file name
    """
    # example file name
    # unit_v01r1_GPM_s202105191345190_e202105191258000_c202208092344126.log

    ctime = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-5]

    file_name = f'{unit_name}_{alg_ver}_none_s{stime}_e{etime}_c{ctime}{ext}'
    return file_name

#########################################################################
#########################################################################
#########################################################################

def setup_log_filename(my_pkgint, added_name=""):
    """
    :param my_pkgint: contains the interface of the unit object
    It sets up the logfile for the entire unit logging object
    :param added_name: any optional string added to the unit name
    """
    # --------------------- create the log file
    log_dir = Path(my_pkgint.config['directory.log'])
    stime = f"{my_pkgint.config['time.start_date']}"
    etime = f"{my_pkgint.config['time.end_date']}"
    algo_ver = f"{my_pkgint.config['production.version']}"

    run_logfile = create_CCAP_filename_s_e(stime, etime,
                                           algo_ver,
                                           f"{added_name}", ".log")
    handler = logging.FileHandler(f"{log_dir}/{run_logfile}")
    date_format = '%Y-%m-%d %H:%M:%S'
    full_format = '%(asctime)s - %(levelname)s - (%(name)s:%(funcName)s) - %(message)s'

    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(fmt=full_format, datefmt=date_format))

    my_log = logging.getLogger()
    my_log.addHandler(handler)

    return handler

def rtvNcid(metadataObj, configObj, rtvProcessObj, currTime):
    """
    %    Generates NetCDF ACDD ID attribute value
    %
    %    id = rtvNcid(metadataObj, configObj, rtvProcessObj, time) returns
    %    an id string for the NetCDF Attribute Convention for Data 
    %    Discovery (ACDD) metadata standard.
    %
    %    The id is comprised of the data timestamp (t) and metadata contained
    %    in the configuration structures including the institution acronym,
    %    process method, process name, subprocess (if defined), domain and
    %    resolution.
    %
    %    Used in RTVSAVENETCDF, STCSAVENETCDF, LTASAVENETCDF
    %
    %    HF-Radar Network
    %    Scripps Institution of Oceanography
    %    Coastal Observing Research and Development Center
    """

    if rtvProcessObj.subprocess and rtvProcessObj.subprocess_name:

        ncid = (f"{currTime.strftime('%Y%m%d%H%M')}{metadataObj.institution_acronym.lower()}"
                f"hfr{rtvProcessObj.method}{rtvProcessObj.name}{rtvProcessObj.subprocess_name}"
                f"{configObj.domain}{configObj.resolution}")
    else:

        ncid = (f"{currTime.strftime('%Y%m%d%H%M')}{metadataObj.institution_acronym.lower()}"
                f"hfr{rtvProcessObj.method}{rtvProcessObj.name}"
                f"{configObj.domain}{configObj.resolution}")

    return ncid



def ltaRunConfig(rtvTime, configObj, rtvProcessObj):
    """Determine if need to do monthly/yearly average"""

    reprocessing = configObj.reprocess
    doMonthly = False
    doYearly = False
    timeNow = datetime.now(timezone.utc)
    timeMonthly = rtvTime
    timeYearly = rtvTime

    if reprocessing:

        #if timeNow is a month more than the reprocess date, then do monthly avg
        if (timeNow.month - rtvTime.month) >= 1:
            doMonthly = True

        #if reprocess date if previous year, then do yearly avg
        if (timeNow.year - rtvTime.year) >= 1:
            doYearly = True

    else:#NRT

        #have to get state from database to see if it's already been done
        state_time, state_cvs = get_state_time(configObj, rtvProcessObj.name.lower())

        if rtvTime.day >= constsHFR.MONTH_AVG_MIN_DAY:
            doMonthly = True

            month_diff = timeNow.month - state_time.month
            # Average has already been done this month
            if month_diff == 0:
                doMonthly = False
            elif month_diff == 1:
                doMonthly = True
            else:
                msg = ("Error: time difference in month between db state time"
                       f"and current time inproper: {month_diff}")
                _log.error(msg)

            if doMonthly:
                #replace the month in the datetime to do previous month's average
                timeMonthly = rtvTime.replace(day=1) - timedelta(days=7)

        if rtvTime > constsHFR.YEAR_AVG_MIN_DATE:
            doYearly = True

            #check if average has been done
            if state_time.year == timeNow.year:
                doYearly = False

            if doYearly:
                #replace year to do previous year's average
                timeYearly = rtvTime.replace(year=rtvTime.year -1)

    return (doMonthly, doYearly, timeMonthly, timeYearly)
