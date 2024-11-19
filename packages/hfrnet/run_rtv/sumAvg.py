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
import hfrnet.utils_funcs.constsHFR as constsHFR

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

       Output: for the get_sum, get_avg, and get_sum_and_avg functions

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

    def __init__(self, mode, configObj, rtvProcessObj, fileLocObj,
                 time, stc_lta_infoObj):
        """
           Create all the different variables needed to run
        """
        self.mode = mode.lower()
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
        self.avg_mode_25hr, self.avg_mode_monthly, self.avg_mode_annual = self.get_mode_bools()

        if self.mode.casefold() not in constsHFR.MODES:
            raise ValueError(f"Must have mode be one of: {constsHFR.MODES}")


    def get_file_list(self):
        """
           Get the proper list of files based on time
        """
        if self.avg_mode_25hr:
            self.fileList = self.get_25Hr_list(self.time)
        elif self.avg_mode_monthly:
            self.fileList = self.get_monthly_list(self.time)
        elif self.avg_mode_annual:
            self.fileList = self.get_annual_list(self.time)
        else:
            raise ValueError(f"Must have 'config' be one of: {constsHFR.MODES}")

    def get_files(self, fileList):
        """
            Get path to the file for each time
        """
        fileList2 = []
        for time in fileList:
            fileLocTemp = None
            if self.mode == constsHFR.MODES[0]:#25-hour
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

    def get_mode_bools(self) -> (bool, bool, bool):
        """
           Want bools for each config condition
        """
        avg_mode_25hr = False
        avg_mode_monthly = False
        avg_mode_annual = False
        if self.mode == constsHFR.MODES[0]:
            avg_mode_25hr = True
        elif self.mode == constsHFR.MODES[1]:
            avg_mode_monthly = True
        elif self.mode == constsHFR.MODES[2]:
            avg_mode_annual = True
        else:
            raise ValueError(f"Must have 'config' be one of: {constsHFR.MODES}")

        return (avg_mode_25hr, avg_mode_monthly, avg_mode_annual)

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

    def initalize_sumavg_annual(self, sumavgObj, inFileTotObj):
        """
           Annual should initalize to the first month's
        """
        sumavgObj.grid = inFileTotObj.grid
        sumavgObj.lat = inFileTotObj.lat
        sumavgObj.lon = inFileTotObj.lon
        sumavgObj.nGood = inFileTotObj.nGood.astype(np.float32)
        sumavgObj.uSum = inFileTotObj.uSum
        sumavgObj.vSum = inFileTotObj.vSum
        sumavgObj.u2Sum = inFileTotObj.u2sum
        sumavgObj.v2Sum = inFileTotObj.v2sum
        sumavgObj.uMin = inFileTotObj.uMin
        sumavgObj.vMin = inFileTotObj.vMin
        sumavgObj.uMax = inFileTotObj.uMax
        sumavgObj.vMax = inFileTotObj.vMax
        #sumavgObj.uAvg = inFileTotObj.uAvg
        #sumavgObj.vAvg = inFileTotObj.vAvg
        #sumavgObj.uVar = inFileTotObj.uVar
        #sumavgObj.vVar = inFileTotObj.vVar

        return sumavgObj

    def get_sum(self) -> SumAvgInfo:
        """
           Do the sum of radials totals over the file list
        """

        infoObj = self.stcLtaInfoObj

        # need to know which files to run over
        self.get_file_list()

        for inFile in self.fileList:

            rtvTotObj = RtvTotals()
            if not Path(inFile.input_matfile).is_file():
                msg = f"ERROR::sumAvg: could not load file {inFile.input_matfile}"
                _log.error(msg)
                continue

            dataInObj = read_total_file(inFile.input_matfile)['data']
            inFileTotObj = None
            if self.avg_mode_annual:
                inFileTotObj = dataInObj.S
            else:
                inFileTotObj = dataInObj.U
                rtvTotObj.u_xvel = inFileTotObj.u
                rtvTotObj.v_yvel = inFileTotObj.v
                rtvTotObj.hdop = inFileTotObj.hdop

            self.nLoadedFiles = self.nLoadedFiles + 1

            # Filter by HDOP
            if (self.avg_mode_25hr or self.avg_mode_monthly):
                mask = rtvTotObj.hdop >= infoObj.stcInfo.max_error
                if np.any(mask):
                    rtvTotObj.u_xvel[mask] = np.nan
                    rtvTotObj.v_yvel[mask] = np.nan

            if len(self.sumavgObj.nGood) == 0 and not self.avg_mode_annual:
                self.sumavgObj = self.initalize_sumavg(self.sumavgObj,
                                                       inFileTotObj)
            # Compute sums
            if self.avg_mode_annual:
                if len(self.sumavgObj.nGood) == 0:
                    self.sumavgObj = self.initalize_sumavg(self.sumavgObj,
                                                           inFileTotObj)
                    self.sumavgObj = self.initalize_sumavg_annual(self.sumavgObj,
                                                                  inFileTotObj)
                else:
                    self.sumavgObj.nGood = np.nansum(np.stack((self.sumavgObj.nGood,
                                                               inFileTotObj.nGood)), axis=0)
                    self.sumavgObj.uSum  = np.nansum(np.stack((self.sumavgObj.uSum,
                                                               inFileTotObj.uSum)), axis=0)
                    self.sumavgObj.vSum  = np.nansum(np.stack((self.sumavgObj.vSum,
                                                               inFileTotObj.vSum)), axis=0)
                    self.sumavgObj.u2Sum = np.nansum(np.stack((self.sumavgObj.u2Sum,
                                                               inFileTotObj.u2sum)), axis=0)
                    self.sumavgObj.v2Sum = np.nansum(np.stack((self.sumavgObj.v2Sum,
                                                               inFileTotObj.v2sum)), axis=0)
                    self.sumavgObj.uMin  = np.nanmin(np.stack((self.sumavgObj.uMin,
                                                               inFileTotObj.uMin)), axis=0)
                    self.sumavgObj.vMin  = np.nanmin(np.stack((self.sumavgObj.vMin,
                                                               inFileTotObj.vMin)), axis=0)
                    self.sumavgObj.uMax  = np.nanmax(np.stack((self.sumavgObj.uMax,
                                                               inFileTotObj.uMax)), axis=0)
                    self.sumavgObj.vMax  = np.nanmax(np.stack((self.sumavgObj.vMax,
                                                               inFileTotObj.vMax)), axis=0)
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

        infoObj = self.stcLtaInfoObj
        avgsumObj = self.sumavgObj
        mask = None
        if self.avg_mode_25hr:
            # Mask points below minimum temporal coverage
            if self.nLoadedFiles < infoObj.stcInfo.min_temporal_coverage:
                return avgsumObj

            mask = avgsumObj.nGood < infoObj.stcInfo.min_temporal_coverage

        if self.avg_mode_monthly:
            # Mask points below minimum temporal coverage
            mask = avgsumObj.nGood < infoObj.ltaInfo.min_month_temporal_coverage*constsHFR.HOURS_IN_DAY

        if self.avg_mode_annual:
            # Mask points below minimum temporal coverage
            mask = avgsumObj.nGood < infoObj.ltaInfo.min_year_temporal_coverage*constsHFR.HOURS_IN_DAY 

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
        Do for all time until analysis show a good period, either in the past or
        starting from some future date that we can keep.
        """

        A = self.sumavgObj
        # florida region mask
        mask = np.logical_and(np.logical_and(A.lat > constsHFR.florida_lat[0],
                                             A.lat < constsHFR.florida_lat[1]),
                              np.logical_and(A.lon > constsHFR.florida_lon[0],
                                             A.lon < constsHFR.florida_lon[1]))
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

        if self.avg_mode_monthly or self.avg_mode_annual:
            self.qc_mask()

        return avgObj
