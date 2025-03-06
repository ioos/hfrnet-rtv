"""db_manager"""

from hfrnet.utils_funcs.lib_rtv import DatabaseConfig
import pymysql
import logging
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
        try:
            if self.dbConfig.run_env == 'rhw':
                # -- connect on local rhw linux
                self.conn_handel = pymysql.connect(
                    host=self.dbConfig.host,
                    user=self.dbConfig.user,
                    database=self.dbConfig.db_name)
            else:
                #--- connect on AWS
                self.conn_handel = pymysql.connect(
                user = self.dbConfig.user,
                database = self.dbConfig.db_name,
                host = self.dbConfig.host,
                port = self.dbConfig.port,
                password = self.dbConfig.password,
                ssl_ca = self.dbConfig.ssl_ca,
                ssl_verify_identity = self.dbConfig.ssl_verify_identity,
                ssl_verify_cert = self.dbConfig.ssl_verify_cert,
                auth_plugin_map = self.dbConfig.auth_plugin_map)
        
        except Exception as err:
            msg = (f" ---- FATAL ERROR:Unexpected {err=}, {type(err)=}"
                   f", Can't connect to the database: user={self.dbConfig.user}, "
                   f"database={self.dbConfig.db_name} , "
                   f"exist")
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
    configObj.dbObject.ssl_verify_identity = config['databases.ssl_verify_identity']
    configObj.dbObject.ssl_verify_cert = config['databases.ssl_verify_cert']
    configObj.dbObject.auth_plugin_map = config['databases.auth_plugin_map']
    configObj.dbObject.run_env = config['databases.run_env']
    #---- set the environment parameters
    configObj.config_dbname = config['databases.config_dbname']
    configObj.radial_dbname = config['databases.radial_dbname']

