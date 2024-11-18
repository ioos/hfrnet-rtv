"""SumAndAvg"""

import logging
from datetime import timedelta
from pathlib import Path
import calendar
import numpy as np
from hfrnet.utils_funcs.lib_sumavg import SumAvgInfo
from hfrnet.utils_funcs.lib_rtv import RtvTotals
from hfrnet.utils_funcs.utility import read_total_file
import hfrnet.utils_funcs.filenames as filenames

_log = logging.getLogger()

class SumAndAvg:
    """

       Use this class to compute the sums and averages over the different time
       periods:  25 Hour Avg, Monthly, and Annual.  

       Input: 
             config:  Which type of average to compute.  Set to
                      '25 Hour', 'Monthly', 'Annual'
             configObj: resolution and domain info 
             rtvProcessObj: Process info needed for filenames
             fileLocObj: Where files are located
             time: Timestamp of date(s) to process
             stc_lta_infoObj:  Database info used for calculations

       Output:
              S - SumAvgTotal object containing the following fields:
                nGood: Number of observations
                uSum:  Sum of u
                vSum:  Sum of v
                u2Sum: Sum of u^2
                v2Sum: Sum of v^2
                uMin:  Minimum u
                uMax:  Maximum u
                vMin:  Minimum v
                vMax:  Maximum v
                uAvg:  Average u
                vAvg:  Average v
                uVar:  Variance u
                vVar:  Variance v

       Main functions:
              get_sum:  gets the sum of total radial velocities for given time
              get_avg:  gets the average of the radials; NOTE: can only be done after sum
              get_sum_and_avg:  does both the sum and average 
    """


    MODES = ["25 hour", "monthly", "annual"]
    HOURS_IN_DAY = 24

    def __init__(self, mode, configObj, rtvProcessObj, fileLocObj,
                 time, stc_lta_infoObj):
        """
           Create all the different variables needed to run
        """
        self.mode = mode
        self.time = time
        self.stcLtaInfoObj = stc_lta_infoObj
        self.rtvProcessObj = rtvProcessObj
        self.rtvProcessObj.subprocess_name = self.mode
        self.configObj = configObj
        self.fileLocObj = fileLocObj
        self.sumavgObj = SumAvgInfo()
        self.rtvTotObj = RtvTotals()
        self.fileList = []
        self.nLoadedFiles = 0
        self.completedSum = False

        if self.mode.casefold() not in MODES:
            raise ValueError(f"Must have mode be one of: {self.MODES}")


    def get_file_list(self):
        """
           Get the proper list of files based on time
        """
        if self.mode == self.MODES[0]:
            self.fileList = self.get_25Hr_list(self.time)
        elif self.mode == self.MODES[1]:
            self.fileList = self.get_monthly_list(self.time)
        elif self.mode == self.MODES[2]:
            self.fileList = self.get_annual_list(self.time)
        else:
            raise ValueError(f"Must have 'config' be one of: {self.MODES}")

    def get_files(self, fileList):
        """
            Get path to the file for each time
        """
        fileList2 = []
        for time in fileList:
            fileLocTemp = None
            if self.mode == self.MODES[0]:#25-hour
                fileLocTemp = filenames.filenames(self.configObj,
                                                  self.rtvProcessObj,
                                                  self.fileLocObj, time, 'rtv')
            else:
                fileLocTemp = filenames.filenames(self.configObj,
                                                  self.rtvProcessObj,
                                                  self.fileLocObj, time,
                                                  subprocess=self.mode)
            fileList2.append(fileLocTemp)

        return fileList2

    def get_25Hr_list(self, center_time):
        """
        Make the timestamp list +/- 12 hours
        """

        start_time = center_time - timedelta(hours=12)
        end_time = center_time + timedelta(hours=12)
        temp_time = start_time
        time_period = [start_time]
        while temp_time < end_time:
            temp_time += timedelta(hours=1)
            time_period.append(temp_time)

        time_period = self.get_files(time_period)

        return time_period

    def get_monthly_list(self, time_month):
        """
           Gets list of hours between start and end of month of 'time'
        """
        dayOfWeek, last = calendar.monthrange(time_month.year, time_month.month)
        start_of_month = time_month.replace(day=1)
        end_of_month = time_month.replace(day=last, hour=23)
        temp_time = start_of_month
        time_period = [temp_time]

        while temp_time < end_of_month:
            temp_time += timedelta(hours=1)
            time_period.append(temp_time)

        time_period = self.get_files(time_period)

        return time_period

    def get_annual_list(self, time_cent):
        """
           Gets list of months between start and end of year of 'time'
        """
        temp_time = time_cent.replace(month=1, day=1)
        time_period = [temp_time]
        month_tmp = 2
        max_months_in_year = 13
        while month_tmp < max_months_in_year:
            temp_time = temp_time.replace(month=month_tmp)
            time_period.append(temp_time)
            month_tmp = month_tmp + 1

        time_period = self.get_files(time_period)

        return time_period

    def get_config_bools(self) -> (bool, bool, bool):
        """
           Want bools for each config condition
        """
        is25Hr = False
        isMonthly = False
        isAnnual = False
        if self.mode == self.MODES[0]:
            is25Hr = True
        elif self.mode == self.MODES[1]:
            isMonthly = True
        elif self.mode == self.MODES[2]:
            isAnnual = True
        else:
            raise ValueError(f"Must have 'config' be one of: {self.MODES}")

        return (is25Hr, isMonthly, isAnnual)

    def initalize_sumavg(self, sumavgObj, rtvTotObj) -> SumAvgInfo:
        """
           Need to initalize the object when it's the first file
        """

        nGridPts = len(rtvTotObj.grid.ocean_indices)
        sumavgObj.grid = rtvTotObj.grid
        sumavgObj.lat = rtvTotObj.lat
        sumavgObj.lon = rtvTotObj.lon
        sumavgObj.nGood = np.zeros(nGridPts)
        sumavgObj.uSum = np.zeros(nGridPts)
        sumavgObj.vSum = np.zeros(nGridPts)
        sumavgObj.u2Sum = np.zeros(nGridPts)
        sumavgObj.v2Sum = np.zeros(nGridPts)
        sumavgObj.uMin = np.full(nGridPts, np.nan)
        sumavgObj.vMin = np.full(nGridPts, np.nan)
        sumavgObj.uMax = np.full(nGridPts, np.nan)
        sumavgObj.vMax = np.full(nGridPts, np.nan)
        sumavgObj.uAvg = np.zeros(nGridPts)
        sumavgObj.vAvg = np.zeros(nGridPts)
        sumavgObj.uVar = np.zeros(nGridPts)
        sumavgObj.vVar = np.zeros(nGridPts)

        return sumavgObj

    def initalize_sumavg_annual(self, sumavgObj, matlabU):
        """
           Annual should initalize to the first month's
        """
        sumavgObj.grid = matlabU.grid
        sumavgObj.lat = matlabU.lat
        sumavgObj.lon = matlabU.lon
        sumavgObj.nGood = matlabU.nGood.astype(np.float32)
        sumavgObj.uSum = matlabU.uSum
        sumavgObj.vSum = matlabU.vSum
        sumavgObj.u2Sum = matlabU.u2sum
        sumavgObj.v2Sum = matlabU.v2sum
        sumavgObj.uMin = matlabU.uMin
        sumavgObj.vMin = matlabU.vMin
        sumavgObj.uMax = matlabU.uMax
        sumavgObj.vMax = matlabU.vMax
        #sumavgObj.uAvg = matlabU.uAvg
        #sumavgObj.vAvg = matlabU.vAvg
        #sumavgObj.uVar = matlabU.uVar
        #sumavgObj.vVar = matlabU.vVar

        return sumavgObj

    def get_sum(self) -> SumAvgInfo:
        """
           Do the sum of radials totals over the file list
        """

        is25Hr, isMonthly, isAnnual = self.get_config_bools()
        infoObj = self.stcLtaInfoObj

        # need to know which files to run over
        self.get_file_list()

        for inFile in self.fileList:

            rtvTotObj = RtvTotals()
            if not Path(inFile.input_matfile).is_file():
                msg = f"ERROR::sumAvg: could not load file {inFile.input_matfile}"
                _log.error(msg)
                continue

            matLabObj = read_total_file(inFile.input_matfile)['data']
            matlabU = None
            if isAnnual:
                matlabU = matLabObj.S
            else:
                matlabU = matLabObj.U
                rtvTotObj.u_xvel = matlabU.u
                rtvTotObj.v_yvel = matlabU.v
                rtvTotObj.hdop = matlabU.hdop

            self.nLoadedFiles = self.nLoadedFiles + 1

            # Filter by HDOP
            if (is25Hr or isMonthly):
                mask = rtvTotObj.hdop >= infoObj.stcInfo.max_error
                if np.any(mask):
                    rtvTotObj.u_xvel[mask] = np.nan
                    rtvTotObj.v_yvel[mask] = np.nan

            if len(self.sumavgObj.nGood) == 0 and not isAnnual:
                self.sumavgObj = self.initalize_sumavg(self.sumavgObj,
                                                       matlabU)
            # Compute sums
            if isAnnual:
                if len(self.sumavgObj.nGood) == 0:
                    self.sumavgObj = self.initalize_sumavg(self.sumavgObj,
                                                           matlabU)
                    self.sumavgObj = self.initalize_sumavg_annual(self.sumavgObj,
                                                                  matlabU)
                else:
                    self.sumavgObj.nGood = np.nansum(np.stack((self.sumavgObj.nGood,
                                                               matlabU.nGood)), axis=0)
                    self.sumavgObj.uSum  = np.nansum(np.stack((self.sumavgObj.uSum,
                                                               matlabU.uSum)), axis=0)
                    self.sumavgObj.vSum  = np.nansum(np.stack((self.sumavgObj.vSum,
                                                               matlabU.vSum)), axis=0)
                    self.sumavgObj.u2Sum = np.nansum(np.stack((self.sumavgObj.u2Sum,
                                                               matlabU.u2sum)), axis=0)
                    self.sumavgObj.v2Sum = np.nansum(np.stack((self.sumavgObj.v2Sum,
                                                               matlabU.v2sum)), axis=0)
                    self.sumavgObj.uMin  = np.nanmin(np.stack((self.sumavgObj.uMin,
                                                               matlabU.uMin)), axis=0)
                    self.sumavgObj.vMin  = np.nanmin(np.stack((self.sumavgObj.vMin,
                                                               matlabU.vMin)), axis=0)
                    self.sumavgObj.uMax  = np.nanmax(np.stack((self.sumavgObj.uMax,
                                                               matlabU.uMax)), axis=0)
                    self.sumavgObj.vMax  = np.nanmax(np.stack((self.sumavgObj.vMax,
                                                               matlabU.vMax)), axis=0)
            else:
                self.sumavgObj.nGood = self.sumavgObj.nGood + (1 - np.isnan(rtvTotObj.u_xvel))
                self.sumavgObj.uSum  = np.nansum(np.stack((self.sumavgObj.uSum,
                                                           rtvTotObj.u_xvel)), axis=0)
                self.sumavgObj.vSum  = np.nansum(np.stack((self.sumavgObj.vSum,
                                                           rtvTotObj.v_yvel)), axis=0)
                self.sumavgObj.u2Sum = np.nansum(np.stack((self.sumavgObj.u2Sum,
                                                           rtvTotObj.u_xvel**2)), axis=0)
                self.sumavgObj.v2Sum = np.nansum(np.stack((self.sumavgObj.v2Sum,
                                                           rtvTotObj.v_yvel**2)), axis=0)
                self.sumavgObj.uMin  = np.nanmin(np.stack((self.sumavgObj.uMin,
                                                           rtvTotObj.u_xvel)), axis=0)
                self.sumavgObj.vMin  = np.nanmin(np.stack((self.sumavgObj.vMin,
                                                           rtvTotObj.v_yvel)), axis=0)
                self.sumavgObj.uMax  = np.nanmax(np.stack((self.sumavgObj.uMax,
                                                           rtvTotObj.u_xvel)), axis=0)
                self.sumavgObj.vMax  = np.nanmax(np.stack((self.sumavgObj.vMax,
                                                           rtvTotObj.v_yvel)), axis=0)
        self.completedSum = True

        return self.sumavgObj

    def nanany(self, x):
        """ ignore NaN """
        return np.any(x, where=np.logical_not(np.isnan(x)))

    def get_avg(self) -> SumAvgInfo:
        """
           Compute the average after the sum is done
        """

        if not self.completedSum:
            _log.error("ERROR: Cannot do the average until 'get_sum' has been completed")
            return None

        is25Hr, isMonthly, isAnnual = self.get_config_bools()
        infoObj = self.stcLtaInfoObj
        avgsumObj = self.sumavgObj
        mask = None
        if is25Hr:
            # Mask points below minimum temporal coverage
            if self.nLoadedFiles < infoObj.stcInfo.min_temporal_coverage:
                return avgsumObj

            mask = avgsumObj.nGood < infoObj.stcInfo.min_temporal_coverage

        if isMonthly:
            # Mask points below minimum temporal coverage
            mask = avgsumObj.nGood < infoObj.ltaInfo.min_month_temporal_coverage*self.HOURS_IN_DAY

        if isAnnual:
            # Mask points below minimum temporal coverage
            mask = avgsumObj.nGood < infoObj.ltaInfo.min_year_temporal_coverage*self.HOURS_IN_DAY

        if np.any(mask):
            avgsumObj.nGood[mask] = np.nan
            avgsumObj.uSum[mask] = np.nan
            avgsumObj.vSum[mask] = np.nan
            avgsumObj.u2Sum[mask] = np.nan
            avgsumObj.v2Sum[mask] = np.nan
            avgsumObj.uMin[mask] = np.nan
            avgsumObj.vMin[mask] = np.nan
            avgsumObj.uMax[mask] = np.nan
            avgsumObj.vMax[mask] = np.nan

        if not self.nanany(avgsumObj.nGood):
            return avgsumObj

        # Compute stats
        A = avgsumObj
        A.uAvg = A.uSum/A.nGood
        A.vAvg = A.vSum/A.nGood
        A.uVar = ( 1./(A.nGood - 1) ) * (A.u2Sum - ((1./A.nGood) * (A.uSum**2)))
        A.vVar = ( 1./(A.nGood - 1) ) * (A.v2Sum - ((1./A.nGood) * (A.vSum**2)))

        avgsumObj = A

        return avgsumObj

    def qc_mask(self):
        """
        LTAQCMASK Apply quality control masks to long-term average products

        QC_mask masks spatial areas as a function of time as needed.
        
        Filter out currents in the Straits of Florida
        Do for all time until analysis show a good period, either in the past or starting from some
        future date that we can keep.

        """

        fl_lat = [25, 26.75]
        fl_lon = [-80.75, -78.75]
        A = self.sumavgObj
        #mask = A.lat > 25 & A.lat < 26.75 & A.lon > -80.75 & A.lon < -78.75;
        mask = np.logical_and(np.logical_and(A.lat > fl_lat[0],
                                             A.lat < fl_lat[1]),
                              np.logical_and(A.lon > fl_lon[0],
                                             A.lon < fl_lon[1]))
        if np.any(mask):
            self.sumavgObj.nGood[mask] = np.nan
            self.sumavgObj.uMin[mask]  = np.nan
            self.sumavgObj.vMin[mask]  = np.nan
            self.sumavgObj.uMax[mask]  = np.nan
            self.sumavgObj.vMax[mask]  = np.nan
            self.sumavgObj.uSum[mask]  = np.nan
            self.sumavgObj.vSum[mask]  = np.nan
            self.sumavgObj.u2sum[mask] = np.nan
            self.sumavgObj.v2sum[mask] = np.nan
            self.sumavgObj.uAvg[mask]  = np.nan
            self.sumavgObj.vAvg[mask]  = np.nan
            self.sumavgObj.uVar[mask]  = np.nan
            self.sumavgObj.vVar[mask]  = np.nan

        return self.sumavgObj

    def get_sum_and_avg(self):
        """
        Do both the sum and average
        """
        sumObj = self.get_sum()
        avgObj = self.get_avg()

        is25Hr, isMonthly, isAnnual = self.get_config_bools()
        if isMonthly or isAnnual:
            self.qc_mask()

        return avgObj
