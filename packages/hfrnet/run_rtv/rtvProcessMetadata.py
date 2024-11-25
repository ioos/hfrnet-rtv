"""rtvProcessMetadata"""

import logging
from hfrnet.utils_funcs.lib_rtv import Metadata
from hfrnet.utils_funcs import constsHFR

_log = logging.getLogger()

def rtvProcessMetadata(processObj, configObj):
    """
    #   Amends process and method specific metadata
    #
    #    metaDataObj = rtvProcessMetadata(processObj, configObj) updates the
    #    title, summary, keywords, processingLevel and references with process
    #    or method specific metadata.
    #
    #    Metadata defined here is primarily defined by standards used in NetCDF
    #    export routines.
    #
    #
    #    HF-Radar Network
    #    Scripps Institution of Oceanography
    #    Coastal Observing Research and Development Center
    """

    metaDataObj = Metadata()
    name = processObj.name.casefold()

    # Obtain process dependent metadata
    if name == 'rtv':
        metaDataObj = getRtvMetadata(processObj, configObj, metaDataObj)

    elif name == 'stc':
        metaDataObj = getStcMetadata(processObj, configObj, metaDataObj)

    elif name == 'lta':
        metaDataObj = getLtaMetadata(processObj, configObj, metaDataObj)

    else:
        msg = f'Process{processObj.name} not recognized for defining metadata'
        _log.error(msg)
        raise ValueError(msg)

    return metaDataObj

    #% RTV specific metadata
def getRtvMetadata(processObj, configObj, metaDataObj):
    """ rtv metadata """

    domain = (configObj.domain).casefold()

    # Title (REQUIRED)
    if domain == "glna":
        metaDataObj.title = (f"Near-Real Time Surface Water Velocity, "
                             f"{metaDataObj.domain_description}, "
                             f"{configObj.resolution} Resolution")
    else:
        metaDataObj.title = ('Near-Real Time Surface Ocean Velocity, '
                             f"{metaDataObj.domain_description}, "
                             f"{configObj.resolution} Resolution")

    # Summary (REQUIRED)
    if domain == "glna":
        metaDataObj.summary = ('Surface velocities estimated from HF-Radar are '
                            f"representative of the upper {metaDataObj.depth_bottom: 0.1f} "
                               'meters of the lake.  The main objective of near-real'
                               'time processing is to produce the best product from'
                               'available data at the time of processing. '
                               'Radial velocity measurements are obtained from '
                               'individual radar sites through the U.S. HF-Radar Network.'
                               'Hourly radial data are processed by '
                               f"{processObj.methoddesc.lower()}"
                               f" on a {configObj.resolution} resolution grid "
                               f"of the {metaDataObj.domain_description} "
                               'to produce near real-time surface current maps.')
    else:
        metaDataObj.summary = ('Surface ocean velocities estimated from HF-Radar are '
                               'representative of the upper '
                               f"{metaDataObj.depth_bottom:0.1f} meters"
                               ' of the ocean.  The main objective of near-real '
                               'time processing is to produce the best product '
                               'from available data at the time of processing. '
                               'Radial velocity measurements are obtained from '
                               'individual radar sites through the U.S. HF-Radar '
                               'Network. Hourly radial data are processed by '
                               f"{processObj.methoddesc.lower()}"
                               f" on a {configObj.resolution} resolution grid "
                               f"of the {metaDataObj.domain_description}"
                               ' to produce near real-time surface current maps.')

    # Keywords (REQUIRED)
    #case & repeat for each product below (rtv, sta, lta)
    metaDataObj.keywords_vocabulary = \
        'Global Change Master Directory (GCMD) Keywords, Version 14.1'
    if domain == "glna":
        metaDataObj.keywords = ('Earth Science, Terrestrial Hydrosphere, '
            'Surface Water, Surface Water Features, Lakes/Reservoirs')
    else:
        metaDataObj.keywords = ('Earth Science, Oceans, Coastal Processes, '
            'Marine Environment Monitoring, Ocean Circulation, Ocean Currents, '
            'Surface Currents, Wind-Driven Circulation, Tides, Tidal Currents')

    metaDataObj = appendLocationKeywords(configObj, metaDataObj)

    # Processing Level (REQUIRED)
    metaDataObj.processing_level = ('Near real-time dataset with automated data '
                                      'acquisition and processing quality control')

    # References (OPTIONAL)
    metaDataObj.references = ('Terrill, E. et al., 2006. Data Management and Real-time '
        'Distribution in the HF-Radar National Network. Proceedings of the MTS/IEEE Oceans '
        '2006 Conference, Boston MA, September 2006.')

    return metaDataObj

    #% STC specific metadata
def getStcMetadata(processObj, configObj, metaDataObj):
    """stc metadata"""

    domain = (configObj.domain).casefold()

    # Title (REQUIRED)
    if domain == "glna":
        metaDataObj.title = ('Near-Real Time Subtidal Surface Water Velocity, '
                             f"{metaDataObj.domain_description}, "
                             f"{configObj.resolution} Resolution")
    else:
        metaDataObj.title = ('Near-Real Time Subtidal Surface Ocean Velocity, '
                             f"{metaDataObj.domain_description}, "
                             f"{configObj.resolution} Resolution")

    # Summary (REQUIRED)
    if domain == "glna":
        metaDataObj.summary =('Surface velocities estimated from HF-Radar are '
                              f"representative of the upper {metaDataObj.depth_bottom:0.1f}"
                              ' meters of the lake.  The main objective of '
                              'near-real time processing is to produce the '
                              'best product from available data at the time of '
                              'processing.  Radial velocity measurements are '
                              'obtained from individual radar sites through the U.S. HF-Radar '
                              'Network. Hourly radial data are processed by '
                              f"{processObj.methoddesc.lower()}"
                              f" on a {configObj.resolution} resolution grid "
                              f"of the {metaDataObj.domain_description}"
                              ' to produce hourly near real-time surface '
                              'current maps. The subtidal current is '
                              'estimated by applying a 25 hour moving average '
                              'filter to the hourly surface current maps.')
    else:
        metaDataObj.summary = ('Surface ocean velocities estimated from HF-Radar are '
                               f"representative of the upper {metaDataObj.depth_bottom:0.1f}"
                               ' meters of the ocean.  The main objective of '
                               'near-real time processing is to produce the '
                               'best product from available data at the time '
                               'of processing.  Radial velocity '
                               'measurements are obtained from individual radar'
                               ' sites through the U.S. HF-Radar Network.'
                               'Hourly radial data are processed by '
                               f"{processObj.methoddesc.lower()}"
                               f" on a {configObj.resolution} resolution grid "
                               f"of the {metaDataObj.domain_description}"
                               ' to produce hourly near real-time surface '
                               'current maps. The subtidal current is '
                               'estimated by applying a 25 hour moving average '
                               'filter to the hourly surface current maps.')

    # Keywords (REQUIRED)
    metaDataObj.keywords_vocabulary = 'Global Change Master Directory (GCMD) Keywords, Version 14.1'

    if domain == "glna":
        metaDataObj.keywords = ['Earth Science, Terrestrial Hydrosphere, '
            'Surface Water, Surface Water Features, Lakes/Reservoirs']
    else:
        metaDataObj.keywords = ['Earth Science, Oceans, Sea Surface, Coastal Processes, '
            'Marine Environment Monitoring, Ocean Circulation, Ocean Currents, '
            'Wind-Driven Circulation']

    metaDataObj = appendLocationKeywords(configObj, metaDataObj)

    # Processing Level (REQUIRED)
    metaDataObj.processing_level = ('Near real-time dataset with automated data '
        'acquisition and processing quality control')

    # References (OPTIONAL)
    metaDataObj.references = ('Terrill, E. et al., 2006. Data Management and Real-time '
        'Distribution in the HF-Radar National Network. Proceedings of the MTS/IEEE Oceans '
        '2006 Conference, Boston MA, September 2006.')

    return metaDataObj

    #% LTA specific metadata
def getLtaMetadata(processObj, configObj, metaDataObj):
    """lta metadata"""

    # Ensure subprocess is defined
    if not processObj.subprocess_name:
        _log.error('LTA subprocess is not defined')

    domain = (configObj.domain).casefold()

    # Summary (REQUIRED)
    if domain == "glna":
        metaDataObj.summary = ('Surface velocities estimated from HF-Radar are '
            'representative of the upper '
            f"{metaDataObj.depth_bottom:0.1f meters} of the lake.  The "
            'main objective of near-real time processing is to produce the best product '
            'from available data at the time of processing.  Radial velocity measurements '
            'are obtained from individual radar sites through the U.S. HF-Radar Network. '
            f"Hourly radial data are processed by {processObj.methoddesc.lower()}"
            f' on a {configObj.resolution} resolution grid of the '
            f"{metaDataObj.domain_description} to produce hourly near real-time surface "
            'current maps.')
    else:
        metaDataObj.summary = ('Surface ocean velocities estimated from HF-Radar are '
            'representative of the upper '
            f"{metaDataObj.depth_bottom:0.1f} meters of the ocean.  The "
            'main objective of near-real time processing is to produce the best product '
            'from available data at the time of processing.  Radial velocity measurements '
            'are obtained from individual radar sites through the U.S. HF-Radar Network. '
            f"Hourly radial data are processed by {processObj.methoddesc.lower()}"
            f' on a {configObj.resolution} resolution grid of the '
            f"metaDataObj.domain_description ' to produce hourly near real-time surface "
            'current maps.')

    # Subprocess specific fields
    subprocess_name = (processObj.subprocess_name).casefold()
    if subprocess_name == constsHFR.CONFIGS_DICT['month']:

        # Title (REQUIRED)
        if domain == "glna":
            metaDataObj.title = ('Near-Real Time Month Average Surface Water Velocity, '
                f"{metaDataObj.domain_description}, {configObj.resolution} Resolution'")
        else:
            metaDataObj.title = ('Near-Real Time Month Average Surface Ocean Velocity, '
                f"{metaDataObj.domain_description}, {configObj.resolution} Resolution")

        # Summary (REQUIRED)
        metaDataObj.summary = (f"{metaDataObj.summary}"
            ' The month average is computed from all available hourly near real-time '
            'surface current maps for the given month.')

    elif subprocess_name == constsHFR.CONFIGS_DICT['year']:

        # Title (REQUIRED)
        if domain == "glna":
            metaDataObj.title = ('Near-Real Time Year Average Surface Water Velocity, '
                f"{metaDataObj.domain_description}, {configObj.resolution} Resolution")
        else:
            metaDataObj.title = ('Near-Real Time Year Average Surface Ocean Velocity, '
                f"{metaDataObj.domain_description}, {configObj.resolution} Resolution")

        # Summary (REQUIRED)
        metaDataObj.summary = (f"{metaDataObj.summary}"
            ' The year average is computed from all available hourly near real-time '
            'surface current maps for the given year.')

    else:
        msg = f"LTA subprocess name {processObj.subprocess_name} is undefined"
        _log.error(msg)

    # Keywords (REQUIRED)
    metaDataObj.keywords_vocabulary = 'Global Change Master Directory (GCMD) Keywords, Version 14.1'
    if domain == "glna":
        metaDataObj.keywords = ('Earth Science, Terrestrial Hydrosphere, '
            'Surface Water, Surface Water Features, Lakes/Reservoirs')
    else:
        metaDataObj.keywords = ('Earth Science, Oceans, Sea Surface, Coastal Processes, '
            'Marine Environment Monitoring, Ocean Circulation, Ocean Currents, '
            'Wind-Driven Circulation')

    metaDataObj = appendLocationKeywords(configObj, metaDataObj)

    # Processing Level (REQUIRED)
    metaDataObj.processing_level = ('Near real-time dataset with automated data '
        'acquisition and processing quality control')

    # References (OPTIONAL)
    metaDataObj.references = ('Terrill, E. et al., 2006. Data Management and Real-time '
        'Distribution in the HF-Radar National Network. Proceedings of the MTS/IEEE Oceans '
        '2006 Conference, Boston MA, September 2006.')

    return metaDataObj


# Append location keywords based on domain
def appendLocationKeywords(configObj, metaDataObj):
    """keywords for each domain"""

    domain = (configObj.domain).casefold()
    locationKeywords = ''
    if domain =='akns':
        locationKeywords = ', Arctic Ocean, Beaufort Sea'

    elif domain == 'gak':
        locationKeywords = ', Pacific Ocean, North Pacific Ocean, Gulf of Alaska'

    elif domain == 'prvi':
        locationKeywords = [', Atlantic Ocean, North Atlantic Ocean, Caribbean Sea, '
             'Puerto Rico, Virgin Islands']

    elif domain == 'usegc':
        locationKeywords = ', Atlantic Ocean, North Atlantic Ocean, Gulf of Mexico'

    elif domain == 'ushi':
        locationKeywords = ', Pacific Ocean, Central Pacific Ocean, Hawaiian Islands'

    elif domain == 'uswc':
        locationKeywords = ', Pacific Ocean, North Pacific Ocean'

    elif domain == 'glna':
        locationKeywords = ', North America, United States of America, Great Lakes'

    else:
        msg =  f"Domain {configObj.domain} not recognized in appending location keywords"
        _log.error(msg)
        raise ValueError(msg)

    metaDataObj.keywords = f"{metaDataObj.keywords}{locationKeywords}"

    return metaDataObj
