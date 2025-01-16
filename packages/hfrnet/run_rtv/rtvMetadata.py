"""rtvMetadata"""

import logging
_log = logging.getLogger()

def rtvMetadata(ncid, configObj):
    """
    RTVMETADATA Returns project, sensor, and institutional metadata

       c = rtvMetadata( c ) populates the pre-declared c.metadata map
       object with metadata for RTV processing that is specific to the
       processing instutition and nominal grid resolution as well as other
       optional information.

       Metadata defined here is primarily defined by standards used in NetCDF
       export routines.

       See also CONFIGURERTV, FILENAMES, RTVPROCESSMETADATA, RTVSAVENETCDF,
       LTASAVENETCDF, STCSAVENETCDF

       HF-Radar Network
       Scripps Institution of Oceanography
       Coastal Observing Research and Development Center
    """

    #% Program & Project Information
    # These terms are defined by the NetCDF ACDD metadata convention

    # Program (OPTIONAL)
    #    The overarching program(s) of which the dataset is a part
    ncid.program = 'Integrated Ocean Observing System (IOOS)'

    #% Institution & Contact

    # Organization acronym (REQUIRED)
    ncid.institution_acronym = 'SIO'

    # Organization descriptive name (REQUIRED)
    ncid.institution = ('Coastal Observing Research and Development Center, '
                        'Scripps Institution of Oceanography')

    # Organization contact name (REQUIRED)
    ncid.creator_name = 'HFRNet Administrators'

    # Organization contact email (REQUIRED)
    ncid.creator_email = 'hfrnet.administrators@sio.ucsd.edu'

    # Organization contact type; 'person', 'group', 'institution', or 'position' (REQUIRED)
    ncid.creator_type = 'group'

    # Organization URL (REQUIRED)
    ncid.creator_url = 'http://cordc.ucsd.edu/projects/mapping/'

    # Naming Authority (REQUIRED)
    ncid.naming_authority = 'edu.ucsd.cordc'

    #% Source & Instrument Definition

    if configObj.domain == "glna":
        ncid.source = 'surface water velocity field from hf-radar'
    else:
        ncid.source = 'surface ocean velocity field from hf-radar'

    ncid.instrument_vocabulary = 'Global Change Master Directory (GCMD) Keywords, Version 8.6'

    ncid.instrument = ('Earth Remote Sensing Instruments, Active Remote Sensing, '
                       'Profilers/Sounders, Radar Sounders, Doppler RADAR')
