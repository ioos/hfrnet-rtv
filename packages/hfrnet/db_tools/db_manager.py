"""db_manager"""


import os
import boto3
import ssl
import urllib.request
import pymysql

from hfrnet.utils_funcs.lib_rtv import DatabaseConfig
import logging

CERTIFICATE_URL = 'https://truststore.pki.rds.amazonaws.com/us-east-1/us-east-1-bundle.pem'
CERTIFICATE_PATH = '/tmp/us-east-1-bundle.pem'    

_log = logging.getLogger()

class db_manager:
    """manages the database connection and queries"""

    def __init__(self, dbObject, dbname='rtvproc'):
        self.dbConfig = dbObject
        self.dbConfig.db_name=dbname
        self.conn_handel = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self):
        _log.info(f"-- Running in {self.dbConfig.run_env }")
        try:
            if self.dbConfig.run_env == 'rhw':
                # -- connect on local rhw linux
                self.conn_handel = pymysql.connect(
                    host=self.dbConfig.host,
                    user=self.dbConfig.user,
                    database=self.dbConfig.db_name)
            else:
                #--- connect on AWS
                _log.info(f"---------------------------------------------")
                _log.info(f" ::self.dbConfig.run_env::{self.dbConfig.run_env}")
                _log.info(f"--------self.dbConfig.password ::{self.dbConfig.password} ")
                _log.info(f"-------- pymysql.connect ")

                self.conn_handel = pymysql.connect(host = self.dbConfig.host,
                                                user = self.dbConfig.user,
                                                password = self.dbConfig.password,
                                                database = self.dbConfig.db_name,
                                                port =self.dbConfig.port,
                                                ssl = self.dbConfig.ssl_context)
        
                _log.info(f"---------------------------- connected")
                _log.info(f"---------------------------------------------")
        except Exception as err:
            msg = (f" ---- FATAL ERROR:Unexpected {err} ::::, {type(err)}::::"
                f", Can't connect to the database: user={self.dbConfig.user}, "
                f"database={self.dbConfig.db_name}")
            _log.fatal(msg)
    #----------------------------------------------------------
    def get_query(self, query):
        _log.info(" -------->>>>>>>>>>>>>>------------------ ")
        _log.info(query)
        datasetdict = {}
        with self.conn_handel.cursor() as cursor:
            cursor.execute(query)
            # Fetch the first row
            rows = cursor.fetchall()
            self.create_dict(rows, cursor.description, datasetdict)
            
            _log.info(" ------------------ ")
            for key, value in datasetdict.items():
                msg = f"{key}:::{value}"
                _log.info(msg)
            _log.info(" -------->>>>>>>>>>>>>>------------------ ")

        return datasetdict
    #----------------------------------------------------------
    def write_query(self, query):
        _log.info(" -------->>>>>>>>>>>>>>------------------ ")
        _log.info(query)
        
        with self.conn_handel.cursor() as cursor:
            nNpdated_rows = cursor.execute(query)
            if nNpdated_rows>0:
                _log.info(f" Database table is updated")
                self.conn_handel.commit()

        return

    # ----------------------------------------------------------
    def check_dict(self, my_dict, key, add, value):
        # Check if the key exists in the dictionary
        if key in my_dict:
            # Append the string to the existing value
            # value = my_dict[key]
            key += f"{add}"
            my_dict[key] = value
        else:
            # Add the key with the new string as its value
            my_dict[key] = value
    #----------------------------------------------------------

    def create_dict(self, data_rows, headers, datasetdict):
        # List of tuples
        for i in range(len(headers)):
            col_head = headers[i][0]
            list1 = []
            for row in data_rows:
                list1.append(row[i])

            #-- to check the repeated dict key, then append "_2"
            self.check_dict(datasetdict, col_head, "_2", list1)

    #----------------------------------------------------------

    def close(self):
        self.conn_handel.close()
    #----------------------------------------------------------
#------------------ new stuff here \/
    def table_exists(self, table_name):
        self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = self.cursor.fetchone()
        return result is not None
    #----------------------------------------------------------
    def create_lock_process_table(self, table_name):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS lock_process (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exe_time DATETIME,
            domain VARCHAR(255),
            resolution VARCHAR(255)
        )
        """
        self.write_query(create_table_query)
    #----------------------------------------------------------

# ----------------------------------------------------------
def set_db_info( config, configObj):
    """
    Set DB info to be used later...?
    """
    configObj.dbObject.user = config['databases.user']
    configObj.dbObject.host = config['databases.host']
    configObj.dbObject.port = config['databases.port']
    configObj.dbObject.password = config['databases.password']
    configObj.dbObject.ssl_ca = config['databases.ssl_ca']
    configObj.dbObject.region = config['databases.region']
    configObj.dbObject.run_env = config['databases.run_env']

    #-------------------------------------------
    # --- set the ceritication parameters
    download_rds_certificate()
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(configObj.dbObject.ssl_ca)
    context.verify_identity = True
    context.verify_cert = True
    context.auth_plugin_map = {'mysql_clear_password': None}
    configObj.dbObject.ssl_context = context

    #-------------------------------------------
    #---- set the environment parameters
    configObj.config_dbname = config['databases.config_dbname']
    configObj.radial_dbname = config['databases.radial_dbname']

    _log.info(f"---------------------------------------------")
    _log.info(f" set_db_info::Running Env is :: {configObj.dbObject.run_env}")
    if configObj.dbObject.run_env == 'ao':
        # Initialize a session using Amazon RDS
        
        _log.info(f" ::configObj.dbObject.run_env::{configObj.dbObject.run_env}")
        session = boto3.Session()
        client = session.client('rds')
        
        # Generate the authentication token
        REGION = configObj.dbObject.region
        token = client.generate_db_auth_token(DBHostname=configObj.dbObject.host,
                                            Port=configObj.dbObject.port,
                                            DBUsername=configObj.dbObject.user,
                                            Region=REGION)
    elif configObj.dbObject.run_env == 'aws':
        #--- connect on AWS

        _log.info(f"------ calling get_aws_pw")
        token = get_aws_cloud9_pw(configObj.dbObject.host, 
                            configObj.dbObject.port,
                            configObj.dbObject.user,
                            configObj.dbObject.region)

    #================================= 
    configObj.dbObject.password = token
    _log.info("Generating --> token = client.generate_db_auth_token")
    _log.info("======= token =================================")
    _log.info(f"{token}")
    _log.info("========================================")

# ----------------------------------------------------------
def get_aws_cloud9_pw( endpoint, port, user,region):
    """
    get the token when running on aws cloud9
    """

    # Generate the token to connect to the AWS database
    _log.info(f"------ in get_aws_pw")
    os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'
    
    _log.debug("Attempting to AWS keys ::AWS_ACCESS_KEY_ID::AWS_SECRET_ACCESS_KEY ::AWS_SESSION_TOKEN ")
    key_id = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    access_token = os.getenv('AWS_SESSION_TOKEN')
    _log.info(f"------ key_id::{key_id}")
    _log.info(f"------ key_id::{access_token}")
    _log.info(f"------ key_id::{secret_key}")

    # Initialize a session using Amazon RDS
    session = boto3.Session(aws_access_key_id=key_id, aws_secret_access_key=secret_key, aws_session_token=access_token, region_name=region)
    client = session.client('rds')

    # Generate the authentication token
    return client.generate_db_auth_token(DBHostname=endpoint, Port=port, DBUsername=user, Region=region)


def download_rds_certificate():
    """Downloads the RDS certificate. Falls back to env variable if download fails."""

    _log.info(f"------ in download_rds_certificate")   
    try:
        _log.debug("Attempting to download RDS certificate from AWS...")
        urllib.request.urlretrieve(CERTIFICATE_URL, CERTIFICATE_PATH)
        _log.debug("Certificate downloaded successfully.")
    except Exception as download_error: # TODO: coding standards require catching specific errors.
        _log.debug(f"Download failed: {download_error}")
        # Fallback to ENV variable if download fails
        if os.getenv('DEFAULT_RDS_CERTIFICATE'):
            _log.debug("Using RDS certificate from environment variable.")
            with open(CERTIFICATE_PATH, 'w') as cert_file:
                cert_file.write(os.environ['DEFAULT_RDS_CERTIFICATE'])
        else:
            raise RuntimeError("Failed to download certificate and no backup available in environment variable.")



