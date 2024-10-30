"""
Program name:        hfrnet_rtv.py
Date:                10/30/2024
History:             Original
Author:              Tianzhu Qiao
Email:               tianzhu.qiao@noaa.gov
Description:         When run inside of a Docker container, this script
                     will execute the program interface and generate
                     ouput for the hfrnet algorithm.
Input:               config.yaml - A YAML file containing all
                     required variables and paths.
Files needed:        Requires the configuration file.
Output:              After a successful execution of the container, output
                     data will be available in the output directory,
                     and logs should be available in the logging
                     directory. Please read the README document for more
                     information.
Modules/subroutines: t4_utils.future.parse_config
Calling sequence:    python hfrnet_rtv.py <config_yaml>
"""

import sys
import traceback
import logging
import argparse
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Union, Tuple

from t4_utils.future.ccap.parse_config import parse_config

def get_logger(cfg: dict) -> Tuple[logging.getLogger, Path]:
    """
    Creates a logging object.
    """

    create = datetime.now(timezone.utc)
    create = datetime.strftime(create, '%Y%m%d%H%M%S0')
    start = cfg['coverage']['start']

    logfile = f'hfrnet_wrapper_s{start}0_eEND_c{create}.log'
    logpath = cfg['io']['logdir']
    logpath = Path(logpath) / logfile

    level = logging.getLevelName(cfg['logging_level'])
    formatter = logging.Formatter('%(name)s - %(asctime)s - '
                                  '%(levelname)s - %(message)s')
    logger = logging.getLogger('hfrnet')
    logger.setLevel(level)

    log_handler = logging.FileHandler(logpath)
    log_handler.setLevel(level)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    return logger, logpath

def create_directories(cfg: dict) -> None:
    """
    Create a working directory.
    """

    working_dir = Path(cfg['ref']['work_dir'])
    working_dir.mkdir(exist_ok=True, parents=True)

def aim_config(cfg: dict) -> dict:
    """
    From the config file, create the
    dictionary that AIM needs in the
    handoff.
    """
    aim_cfg = {
        "algorithm": {
            "rtv": {
                "domain": cfg['site']['domain'],
                "resolution": cfg['site']['resolution'],
            },
        },
        "date": {
          "start": cfg['coverage']['start'] ,
          "end": cfg['coverage']['end'],
        },
        'directory': {
            "ancillary": cfg['ref']['ancillary'],
            "input": cfg['ref']['input'],
            "output": cfg['io']['outdir'],
            "working": cfg['ref']['work_dir'],
        },
        "production": cfg['production']
    }

    return aim_cfg

def run_aim(cfg: dict, interface_cfg: dict, logger: logging.getLogger) -> None:
    """
    Run the AIM interface
    """
    sys.path.append(cfg['ref']['packages'])

    try:
        import hfrnet
        import aim
    except Exception as err:
        logger.error(err, exc_info=True)
        traceback.print_exc()
        sys.exit(1)
    try:
        aim_cfg = aim.Handoff(interface_cfg)
    except Exception as err:
        traceback.print_exc()
        logger.error(err, exc_info=True)
        sys.exit(1)
    logger.info('Completed succesfully: aim.Handoff(interface_config)')
    try:
        pkg_interface = hfrnet.interface.Interface(aim_cfg)
    except Exception as err:
        traceback.print_exc()
        logger.error(err, exc_info=True)
        sys.exit(1)
    logger.info('Completed succesfully: hfrnet.interface.Interface(aim_cfg)')

    try:
        pkg_interface.run_methods()
    except Exception as err:
        traceback.print_exc()
        logger.info('pkg_interface.run_methods() returned an error:')
        logger.error(err, exc_info=True)
        sys.exit(1)
    logger.info('Completed succesfully: pkg_interface.run_methods()')

def move_output(cfg: dict, logpath: Path) -> None:
    """
    Move the logs and output files in their
    respective directories.

    The wrapper logfile end time is also corrected based on the output
    files.
    """
    work_dir = Path(cfg['ref']['work_dir'])

    # Move algorithm output to io directories
    for f in work_dir.glob('*.log'):
        shutil.move(f, cfg['io']['logdir'])

    output_files = []
    output_files.extend(work_dir.glob('*.nc'))
    for f in output_files:
        shutil.move(f, cfg['io']['outdir'])

    # Rename Docker wrapper log
    fname = Path(output_files[-1])
    search = re.search(r'_e(\d*)_', fname.stem)
    etime = search.group(1)

    newlog = logpath.name.replace('END', str(etime))
    newpath = f'{logpath.parent}/{newlog}'
    shutil.move(logpath, newpath)

def main(config_path: Union[str, Path], logger: logging.getLogger=None) -> None:
    """
    Main function that performs the following:
        1) Calls parse_config to read in the application yaml
        2) Creates a logging object by calling get_logger
        3) Creates the runtime directory
        4) Creates the AIM Handoff config
        5) Executes the aim
        5) Move the log files and output
    """

    cfg = parse_config(config_path)['algorithm']

    if logger is None:
        logger, logpath = get_logger(cfg)

    logger.info('Creating working directory')
    create_directories(cfg)

    logger.info('Creating AIM config')
    aim_cfg = aim_config(cfg)

    start = datetime.now(timezone.utc)
    logger.info('Start Time: %s', start)
    logger.info('Interface Config:\n%s', str(aim_cfg))

    run_aim(cfg, aim_cfg, logger)

    end = datetime.now(timezone.utc)
    run = end - start
    logger.info('End Time: %s', end)
    logger.info('Total Run Time: %f sec', run.total_seconds())

    #move_output(cfg, logpath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('application_yaml_path')
    args = parser.parse_args()
    main(args.application_yaml_path)
