#!/usr/bin/env python

import numpy as np

from hfrnet.utils_funcs.lib_rtv import Grid, LandInfo


class SumAvgInfo:
    """
       Info after doing average calculation
    """
    def __init__(self):
        self.nGood = []
        self.uSum = []
        self.vSum = []
        self.u2Sum = []
        self.v2Sum = []
        self.uMin = []
        self.uMax = []
        self.vMin = []
        self.vMax = []
        self.uAvg = []
        self.vAvg = []
        self.uVar = []
        self.vVar = []
        self.grid = Grid()
        self.land = LandInfo([], [], 0)

class StcInfo:
    """
       Stc info needed to do calculations properly
    """
    def __init__(self):
        self.max_age = np.float64(0)
        self.max_error = np.float64(0)
        self.min_temporal_coverage = np.float64(0)

class LtaInfo:
    """
       Lta info needed to do calculations properly
    """
    def __init__(self):
        self.min_month_temporal_coverage = np.float64(0)
        self.min_year_temporal_coverage = np.float64(0)
        self.max_error = np.float64(0)

class StcLtaInfo:
    """
       Needed to do calculations properly
    """
    def __init__(self):
        self.stcInfo = StcInfo()
        self.ltaInfo = LtaInfo()
