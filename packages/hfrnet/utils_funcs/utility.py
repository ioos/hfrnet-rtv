import sys
import os
import traceback
import six
from pathlib import Path
from datetime import datetime, timedelta, date, time, timezone
from dateutil import parser
import calendar
from decimal import Decimal
from math import cos, sin, sqrt
import math
import numpy as np
from scipy.io import savemat, loadmat
import pickle
import h5py
from polycircles import polycircles
import shapely
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import geopandas as gpd
import pandas as pd
from geographiclib.geodesic import Geodesic
#----- for land and grid files
# from hfrnet.utils_funcs.lib_rtv import LandInfo
import json
import netCDF4 as nc4
import logging
from datetime import datetime, timedelta

_log = logging.getLogger()

def warning(*args, **kwargs):
    print(args, **kwargs, file=sys.stderr)

def save_ascii(filename, data):

    # Build save dir, as needed
    #folder = os.path.dirname(filename)
    folder = Path(filename).parent
    Path(folder).mkdir(parents=True, exist_ok=True)
    if not Path(folder).exists():
        return False, f'Failed to make dir {folder}'

    #with open(filename, 'w') as fp:
    #    fp.write(f'{data[0]:8.4f} {data[1]:9.4f} {data[2]:7.0f} {data[3]:7.0f}\n')
    #    return True, ''

    np.savetxt(filename, data.T, fmt='%8.4f %9.4f %7.0f %7.0f')
    return True, ''

def save_mat(filename, data):

    # Build save dir, as needed
    #folder = os.path.dirname(filename)
    folder = Path(filename).parent
    Path(folder).mkdir(parents=True, exist_ok=True)
    if not Path(folder).exists():
        return False, f'Failed to make dir {folder}'

    # savemat(filename, data)
    # save as pickle as datetime is not supported in savemat
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return True, ''

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
    if hasattr(d, 'keys'):
        keys = [k for k in d.keys() if not k.startswith('__')]
        data = _dict()
        for k in keys:
            data[k] = process_record(d[k])
        return data
    #print(d)
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
        traceback.print_exc(file=sys.stdout)

    return data

def read_total_file(filename):
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
        traceback.print_exc(file=sys.stdout)

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
    end_date = datetime.strptime(etime, '%Y%m%d%H%M%S%f')
    
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
    
    # Convert the dictionary of arrays to a numpy array
    # numpy_array = {key: np.array(value) for key, value in dicts.items()}
    
    # with open(f"{mfile}/{domain}.json", 'r') as file:
    #     dicts = json.load(file)
    #     # land_dict = [LandInfo(d['region'], d['polygon'], d['length']) for d in dicts]
    return dicts

#------------------------------------------------
#------------------------------------------------
#------------------------------------------------
def load_grid(mfile, domain, res, rtvInfoObj):
    """
    Read the grid netcdf file given the domain and res and put it in an array of
    dictionary
    """
    if rtvInfoObj.grid_search_radius == np.floor(rtvInfoObj.grid_search_radius):
        scircle_xfield = f"ocean_x_scircle{rtvInfoObj.grid_search_radius:.0f}km"
        scircle_yfield = f"ocean_y_scircle{rtvInfoObj.grid_search_radius:.0f}km"
    
    elif rtvInfoObj.grid_search_radius * 1000 == np.floor(
            rtvInfoObj.grid_search_radius * 1000):
        scircle_xfield = f"ocean_x_scircle{rtvInfoObj.grid_search_radius * 1000:.0f}m"
        scircle_yfield = f"ocean_y_scircle{rtvInfoObj.grid_search_radius * 1000:.0f}m"
    
    else:
        _log.fatal(f"Invalid grid search radius of {rtvInfoObj.grid_search_radius}"
                  "km. Value must be a whole number when represented in meters")
        
    with nc4.Dataset(f"{mfile}/{domain}{res}.nc", 'r') as ds:
        rtvInfoObj.x_range = np.array(ds.variables["x_range"][:])
        rtvInfoObj.y_range = np.array(ds.variables["y_range"][:])

        dd = np.array(ds.variables["dd"][:])
        rtvInfoObj.dx = dd[0]
        rtvInfoObj.dy = dd[1]
        rtvInfoObj.size = np.array(ds.variables["size"][:])
        rtvInfoObj.ocean_indices = np.array(ds.variables["ocean_indices"][:])
        rtvInfoObj.ocean_xy = np.array(ds.variables["ocean_xy"][:,:])
        setattr(rtvInfoObj, scircle_xfield,
                np.array(ds.variables[f"{scircle_xfield}"][:, :]))
        setattr(rtvInfoObj, scircle_yfield,
                np.array(ds.variables[f"{scircle_yfield}"][:, :]))

        rtvInfoObj.resolution_km  = ds.getncattr('resolution_km')
        rtvInfoObj.projection  = ds.getncattr('projection')
        return rtvInfoObj

def now_hour():
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    t = datetime.now(timezone.utc)
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour)

def eomday(t):
    days_in_month = calendar.monthrange(t.year, t.month)[1]
    return datetime(t.year, t.month, days_in_month)

def now_second():
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    t = datetime.now(timezone.utc)
    return t.replace(second=t.second, microsecond=0, minute=t.minute, hour=t.hour)

def datenum(d):
    return 366 + d.toordinal() + (d - datetime.fromordinal(d.toordinal())).total_seconds()/(24*60*60)

def hour_range(start, end, step=1):
    cur = start
    while cur < end:
        yield cur
        cur += timedelta(hours=step)

def next_month_start(t):
    # return the start day of the next month
    return (datetime(year=t.year, month=t.month, day=1) + timedelta(days=32)).replace(day=1)

def next_month(t):
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
    # return the start day of the prev month
    return (datetime(year=t.year, month=t.month, day=1) + timedelta(days=-1)).replace(day=1)

def prev_month(t):
    try:
        prevmonthdate = t.replace(month=t.month-1)
    except ValueError:
        if t.month == 1:
            prevmonthdate = t.replace(year=t.year-1, month=12)
        else:
            # prev month is too short to have "same date"
            prevmonthdate = eomday(t.replace(month=t.month-1, day=1))
    return prevmonthdate

def month_range(start, end, step=1):
    cur = start
    while cur < end:
        yield cur
        for s in range(step):
            cur = next_month(cur)

def azimuth(lat1, lat2, long1, long2):
    brng = Geodesic.WGS84.Inverse(lat1, long1, lat2, long2)['azi1']
    return brng

def cart2pol(x, y):
    rho = np.sqrt(np.array(x)**2 + np.array(y)**2)
    phi = np.arctan2(y, x)
    return(phi, rho)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)

def scircle1(lat, lon, radius, num=99):
    polycircle = polycircles.Polycircle(latitude=lat, longitude=lon,  radius=radius*1e3, number_of_vertices=num)
    verticles = np.array(polycircle.vertices)
    return verticles[:, 0], verticles[:, 1]

#import line_profiler
#@profile
def inpolygon(xq, yq, xv, yv):
    rst = []
    polygon = Polygon(list(zip(xv, yv)))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)

    pts = shapely.points(xq, yq)
    return polygon.touches(pts) | polygon.contains(pts)

def km2deg(km, radius=6371):
    degree = km*360/(np.pi*radius*2)
    return degree

def scxsc(p1, r1, p2, r2):
    # p1 = Coordinates of Point 1: latitude, longitude. This serves as the center of circle 1. Ex: (36.110174,  -90.953524)
    # r1 = Radius of circle 1 in meters
    # p2 = Coordinates of Point 2: latitude, longitude. This serves as the center of circle 1. Ex: (36.110174,  -90.953524)
    # r2 = Radius of circle 2 in meters
    '''
    1. Convert (lat, lon) to (x,y,z) geocentric coordinates.
    As usual, because we may choose units of measurement in which the earth has a unit radius
    '''
    x_p1 = Decimal(cos(math.radians(p1[1]))*cos(math.radians(p1[0])))  # x = cos(lon)*cos(lat)
    y_p1 = Decimal(sin(math.radians(p1[1]))*cos(math.radians(p1[0])))  # y = sin(lon)*cos(lat)
    z_p1 = Decimal(sin(math.radians(p1[0])))                           # z = sin(lat)
    x1 = (x_p1, y_p1, z_p1)

    x_p2 = Decimal(cos(math.radians(p2[1]))*cos(math.radians(p2[0])))  # x = cos(lon)*cos(lat)
    y_p2 = Decimal(sin(math.radians(p2[1]))*cos(math.radians(p2[0])))  # y = sin(lon)*cos(lat)
    z_p2 = Decimal(sin(math.radians(p2[0])))                           # z = sin(lat)
    x2 = (x_p2, y_p2, z_p2)
    '''
    2. Convert the radii r1 and r2 (which are measured along the sphere) to angles along the sphere.
    By definition, one nautical mile (NM) is 1/60 degree of arc (which is pi/180 * 1/60 = 0.0002908888 radians).
    '''
    #r1 = Decimal(math.radians((r1_meter/1852) / 60)) # r1_meter/1852 converts meter to Nautical mile.
    #r1 = Decimal(math.radians(km2deg(r1_meter/1000)))
    r1 = Decimal(math.radians(r1))
    #r2 = Decimal(math.radians((r2_meter/1852) / 60))
    #r2 = Decimal(math.radians(km2deg(r2_meter/1000)))
    r2 = Decimal(math.radians(r2))
    '''
    3. The geodesic circle of radius r1 around x1 is the intersection of the earth's surface with an Euclidean sphere
    of radius sin(r1) centered at cos(r1)*x1.

    4. The plane determined by the intersection of the sphere of radius sin(r1) around cos(r1)*x1 and the earth's surface
    is perpendicular to x1 and passes through the point cos(r1)x1, whence its equation is x.x1 = cos(r1)
    (the "." represents the usual dot product); likewise for the other plane. There will be a unique point x0 on the
    intersection of those two planes that is a linear combination of x1 and x2. Writing x0 = ax1 + b*x2 the two planar
    equations are;
       cos(r1) = x.x1 = (a*x1 + b*x2).x1 = a + b*(x2.x1)
       cos(r2) = x.x2 = (a*x1 + b*x2).x2 = a*(x1.x2) + b
    Using the fact that x2.x1 = x1.x2, which I shall write as q, the solution (if it exists) is given by
       a = (cos(r1) - cos(r2)*q) / (1 - q^2),
       b = (cos(r2) - cos(r1)*q) / (1 - q^2).
    '''
    q = Decimal(np.dot(x1, x2))

    if q**2 != 1 :
        a = (Decimal(cos(r1)) - Decimal(cos(r2))*q) / (1 - q**2)
        b = (Decimal(cos(r2)) - Decimal(cos(r1))*q) / (1 - q**2)
        '''
        5. Now all other points on the line of intersection of the two planes differ from x0 by some multiple of a vector
        n which is mutually perpendicular to both planes. The cross product  n = x1~Cross~x2  does the job provided n is
        nonzero: once again, this means that x1 and x2 are neither coincident nor diametrically opposite. (We need to
        take care to compute the cross product with high precision, because it involves subtractions with a lot of
        cancellation when x1 and x2 are close to each other.)
        '''
        n = np.cross(x1, x2)
        '''
        6. Therefore, we seek up to two points of the form x0 + t*n which lie on the earth's surface: that is, their length
        equals 1. Equivalently, their squared length is 1:
        1 = squared length = (x0 + t*n).(x0 + t*n) = x0.x0 + 2t*x0.n + t^2*n.n = x0.x0 + t^2*n.n
        '''
        x0_1 = [a*f for f in x1]
        x0_2 = [b*f for f in x2]
        x0 = [sum(f) for f in zip(x0_1, x0_2)]
        '''
          The term with x0.n disappears because x0 (being a linear combination of x1 and x2) is perpendicular to n.
          The two solutions easily are   t = sqrt((1 - x0.x0)/n.n)    and its negative. Once again high precision
          is called for, because when x1 and x2 are close, x0.x0 is very close to 1, leading to some loss of
          floating point precision.
        '''
        if (np.dot(x0, x0) <= 1) & (np.dot(n,n) != 0): # This is to secure that (1 - np.dot(x0, x0)) / np.dot(n,n) > 0
            t = Decimal(sqrt((1 - np.dot(x0, x0)) / np.dot(n,n)))
            t1 = t
            t2 = -t

            i1 = x0 + t1*n
            i2 = x0 + t2*n
            '''
            7. Finally, we may convert these solutions back to (lat, lon) by converting geocentric (x,y,z) to geographic
            coordinates. For the longitude, use the generalized arctangent returning values in the range -180 to 180
            degrees (in computing applications, this function takes both x and y as arguments rather than just the
            ratio y/x; it is sometimes called "ATan2").
            '''

            i1_lat = math.degrees( math.asin(i1[2]))
            i1_lon = math.degrees( math.atan2(i1[1], i1[0] ) )
            ip1 = (i1_lat, i1_lon)

            i2_lat = math.degrees( math.asin(i2[2]))
            i2_lon = math.degrees( math.atan2(i2[1], i2[0] ) )
            ip2 = (i2_lat, i2_lon)
            return ip1, ip2
        elif (np.dot(n,n) == 0):
            return None, None #("The centers of the circles can be neither the same point nor antipodal points.")
        else:
            return None, None #("The circles do not intersect")
    else:
        return None, None #("The centers of the circles can be neither the same point nor antipodal points.")

'''
Example: The output of below is  [(36.989311051533505, -88.15142628069133), (38.2383796094578, -92.39048549120287)]

         intersection_points = intersection((37.673442, -90.234036), 107.5*1852, (36.109997, -90.953669), 145*1852)
         print(intersection_points)
'''

def double(val):
    return np.float64(val)

def single(val):
    return np.float32(val)

def int16(val):
    return np.int16(val)

def int32(val):
    return np.int32(val)

def now_datetime():
    return datetime.now(timezone.utc)

def next_datetime(days=0, hours=0, minutes=0):
    return now_datetime() + timedelta(days=days, hours=hours, minutes=minutes)

def time_stamp(t=None):
    if isinstance(t, six.string_types):
        return t
    if t is None:
        t = now_datetime()
    return t.strftime('%Y-%m-%d %H:%M:%S')

def to_time(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S.%f"
DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
def get_datetime(datetime_str=None):
    if not datetime_str:
        return now_datetime()

    if isinstance(datetime_str, (datetime, timedelta)):
        return datetime_str

    elif isinstance(datetime_str, (list, tuple)):
        return datetime(datetime_str)

    elif isinstance(datetime_str, date):
        return datetime.combine(datetime_str, time())

    # dateutil parser does not agree with dates like 0000-00-00
    if not datetime_str or (datetime_str or "").startswith("0000-00-00"):
        return None

    try:
        return datetime.strptime(datetime_str, DATETIME_FORMAT)
    except ValueError:
        return parser.parse(datetime_str)

def to_int(v, default=0):
    try:
        return int(v)
    except ValueError:
        return default

def to_float(v, default=0.0):
    try:
        return float(v)
    except ValueError:
        return default

def arange(start, end, step):
    return np.arange(start, end + step/2.0, step)

def set_2darray_by_index(u, idx, v):
    sz = u.shape
    u = u.transpose().flatten()
    u[idx-1] = v
    u = u.reshape((sz[1], sz[0])).transpose()
    return u

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

def get_processes(times, info):
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
    
    
    
    
