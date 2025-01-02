#!/usr/bin/env python
""" HFRnet Unit1:run_config Interface

@Description:
    *** Update to add description about unit ***
    Responsible for interfacing with unit 1

@History:
    - Letitia Soulliard, July, 26 2021, Created
    - brian.helgans, Sep 23, 2021, Reworked
    *** Update to add your history ***
"""
# *** Update to today ***
__updated__ = "2024-07-23"

from pathlib import Path
import aim
from datetime import datetime
#hfrnet modules
from hfrnet.utils_funcs.utility import setup_log_filename
from hfrnet.db_tools.db_tables import read_domain, read_resolution, read_methods
from hfrnet.utils_funcs.lib_rtv import (ConfigureVals, Metadata, RtvInfo, 
                                        FileLocations, RtvProcess, RtvTotals,
                                        SetupError, DatabaseError)
from hfrnet.utils_funcs.lib_sumavg import StcLtaInfo
from hfrnet.utils_funcs.utility import generate_time_spans
import hfrnet.run_rtv.processRtv as processRtv
from hfrnet.db_tools.db_manager import db_manager, set_db_info

import logging
_log = logging.getLogger()


class Interface(aim.Interface):
    """ Defines the interface to run unit1.

    (This class is inheriting some of its functionality from aim.Interface.)

    This comment section is called a "docstring". It's an important feature of
    python.
    The first line brief.
    You may write as much of a detailed description as you like in these lines
    here.

    *** Update docstring to be descriptive and useful ****

    """

    # initialization of the Interface class expects "template"
    # for validating the incoming configuration file
    # *** Update with your needed configuration ****
    template = {
        'processing': {
                'domain': str,
                'resolution': str,
                'batch_processing': str,
        },
        'time': {
                'start_date': str,
                'end_date': str,
        },
        'production': {
                'site': str,
                'environment': str,
                'version': str,
        },
        'directory': {
            'algorithm_dir': str,
            'working': str,
            'input': str,
            'log': str,
            'output': str,
            'radial_remote_dir': str,
            'radial_local_dir': str,
            'interm_local_dir': str,
        },
        'databases': {
            'run_env': str,
            'user': str,
            'host': str,
            'port': str,
            'password': str,
            'ssl_ca': str,
            'ssl_verify_identity': str,
            'ssl_verify_cert': str,
            'auth_plugin_map': {},
            'config_dbname': str,
            'radial_dbname': str,
        },
    }
    
    mconfigureVals = ConfigureVals("", "")
    mrtvInfo = RtvInfo()
    mstcLtaInfo = StcLtaInfo()
    mstcInfo = mstcLtaInfo.stcInfo 
    mltaInfo = mstcLtaInfo.ltaInfo 
    mnetcdf_metadata = Metadata()
    fileLocObj = FileLocations()
    siteInfoObj = []
    rtvProcessObj = RtvProcess()
    compTotObj = RtvTotals()
    
    def setup(self):
        """ Generate a configuration for the science code.
        This method exists to transform the incoming configuration
        into the configuration understood by the science executable.

        NOTE: The idea is for operations to provide a simple config
            (self.config) then this code handles any additional logic while we
            generate the "real" configuration file.

        *** Update docstring to be descriptive and useful ****
        """
        self.mconfigureVals.domain = self.config['processing.domain']
        self.mconfigureVals.resolution = self.config['processing.resolution']

        # ------ Check the working dir
        working_dir = Path(self.config['directory.working'])
        if not working_dir.is_dir():
            _log.fatal(f" ---- FATAL ERROR: The directory {working_dir} does not "
                       f"exist")
            raise SetupError(f"The directory {working_dir} does not exist")
        # ------ Check the log dir
        log_dir = Path(self.config['directory.log'])
        log_dir.mkdir(parents=True, exist_ok=True)

        self.mconfigureVals.product_version = self.config['production.version']

        setup_log_filename(self, f"hfrnet_{self.mconfigureVals.domain}"
                           f"_{self.mconfigureVals.resolution}")
        
        _log.info("-------------------------------------- ")
        _log.info(f"Star processing HFRnet for domain::"
                  f"{self.mconfigureVals.domain} "
                  f"and Resolution::{self.mconfigureVals.resolution} ")
        _log.info(log_dir)
        _log.info(working_dir)
        # set the runtime to the start time
        self.mconfigureVals.runTime = datetime.strptime(self.config['time.start_date'],
                                          '%Y%m%d%H%M%S%f')
        # This is used when reporcessing a patch of time in the past
        self.mconfigureVals.reprocess = False
        if self.config['processing.batch_processing'].casefold() == 'true':
            self.mconfigureVals.times = generate_time_spans(self.config['time.start_date'],
                                                            self.config['time.end_date'])
            self.mconfigureVals.reprocess = True



    def process(self):
        """ This executes the algorithm's executable (for this unit).

        *** Update docstring to be descriptive and useful ****
        python -m hfrnet.run_config /data/smcd12/ASSISTT_DATA/HFRnet/test2/config_hfr_run_config.yml
        """
               
        # ------ setup the rtvproc connection

        set_db_info(self.config, self.mconfigureVals)
        # get the analysis parametrers for domain, res, rtv,stc,lta
        with db_manager(self.mconfigureVals.dbObject) as db_class:
    
            # Check for valid domain
            try:
                read_domain(db_class, self.mconfigureVals)
            except DatabaseError:
                _log.info(f"No domain {self.mconfigureVals.domain} decsription were found or "
                          f"database connection failed")
                return
            
            # ---------------------------------
            # Check for valid resolution
            try:
                read_resolution(db_class, self.mconfigureVals)
            except DatabaseError:
                _log.info(f"No domain {self.mconfigureVals.resolution}  were found "
                          f"or database connection failed")
                return
            # ---------------------------------
            # Check for valid resolution
            process_list = []
            read_methods(db_class, self.mconfigureVals, self.mrtvInfo,
                         self.mstcInfo, self.mltaInfo,process_list)
        
        self.set_file_locations(self.fileLocObj)
        
        processStatus = processRtv.processRtv(self.mconfigureVals,
                                              self.siteInfoObj,
                                              self.fileLocObj,
                                              process_list,
                                              self.mrtvInfo,
                                              self.mstcLtaInfo,
                                              self.compTotObj)

        self.output_info['status'] = "good"

    def reformat(self):
        """ we sometimes want to reformat the output after processing runs.

        *** Update docstring to be descriptive and useful ****
        """

    def output(self):
        """ Inform OPS of any remaining files it should know about.
        Add any files that need to be pulled out of the container and saved
        into the output_info hand off object.  Create a FileToken object for
        each file and give each file a useful label value.

        *** Update docstring to be descriptive and useful ****
        """
    
    def set_file_locations(self, fileLocObj):
        """
            Set all the directory locations
        """
        
        fileLocObj.mdir = Path(self.config['directory.input'])
        
        algo_dir = Path(self.config['directory.algorithm_dir'])
        fileLocObj.landfile = algo_dir / 'ancillary_data/land_data'
        fileLocObj.gridfile = algo_dir / 'ancillary_data/grid_data'
        
        # --- output dirs to save the nc, asc, intermediate files
        fileLocObj.domaindir = Path(self.config['directory.output'])
        fileLocObj.input_dir = Path(self.config['directory.input'])
        fileLocObj.output_dir = Path(self.config['directory.output'])
        
        fileLocObj.domaindir.mkdir(parents=True, exist_ok=True)
        
        fileLocObj.radial_remote_dir = Path(self.config['directory.radial_remote_dir'])
        fileLocObj.radial_local_dir = Path(self.config['directory.radial_local_dir'])
        if self.config['directory.interm_local_dir']:
            fileLocObj.interm_local_dir = Path(self.config['directory.interm_local_dir'])
        else:
            fileLocObj.interm_local_dir = None
