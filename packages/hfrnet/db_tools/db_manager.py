
import pymysql
import logging
_log = logging.getLogger()

class db_manager:
    def __init__(self, confdb):
        self.name = confdb.name
        self.user = confdb.user
        self.host = confdb.host
        self.port = confdb.port
        self.region = confdb.host
        self.password = confdb.password
        self.sslrootcert = confdb.sslrootcert
        
        self.conn_handel = None
        self.connected = False

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self):
        if ~self.connected:
            try:
                self.conn_handel = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.name)
                self.connected = True
            except Exception as err:
                    _log.fatal(f" ---- FATAL ERROR:Unexpected {err=}, {type(err)=}"
                             f", Can't connect to the database: user={self.user}, "
                             f"database={self.name} , "
                             f"exist")
        # self.cursor = self.connection.cursor()
    #----------------------------------------------------------
    def get_query(self, query):
        if self.connected:
            _log.info(" -------->>>>>>>>>>>>>>------------------ ")
            _log.info(query)
            with self.conn_handel.cursor() as cursor:
                cursor.execute(query)
                # Fetch the first row
                rows = cursor.fetchall()
                datasetdict = {}
                self.create_dict(rows, cursor.description, datasetdict)
                # tablee = self.store_output(cursor)
                # rows = cursor.fetchall()
                
                _log.info(" ------------------ ")
                for key in datasetdict.keys():
                    _log.info(f"{key}:::{datasetdict[key]}")
                _log.info(" -------->>>>>>>>>>>>>>------------------ ")

        return datasetdict
    #----------------------------------------------------------
    def write_query(self, query,values):
        if self.connected:
            _log.info(" -------->>>>>>>>>>>>>>------------------ ")
            _log.info(query)
            with self.conn_handel.cursor() as cursor:
                cursor.execute(query)
                # Fetch the first row
                rows = cursor.fetchall()
                datasetdict = {}
                self.create_dict(rows, cursor.description, datasetdict)
                # tablee = self.store_output(cursor)
                # rows = cursor.fetchall()
                
                _log.info(" ------------------ ")
                for key in datasetdict.keys():
                    _log.info(f"{key}:::{datasetdict[key]}")
                _log.info(" -------->>>>>>>>>>>>>>------------------ ")
        
        return datasetdict
    
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
        # datasetdict = {}
        # List of tuples
        for i in range(len(headers)):
            col_head = headers[i][0]
            # print(col_head)
            list1 = []
            for row in data_rows:
                list1.append(row[i])
            # print(row[i])
            
            # print(list1)
            #-- to check the repeated dict key, then append "_2"
            self.check_dict(datasetdict, col_head, "_2", list1)
        # datasetdict[col_head]=list1
        
        # print(rows[0][i])
        # list1.append(row[i])
        # datasetdict[headers[i][0]]=list1
        
        # print('===================== datasetdict')
        # for row in datasetdict:
        #     print(row, datasetdict[row])
        
        return
    #----------------------------------------------------------

    def close(self):
        if self.connected:
            self.conn_handel.close()
            self.connected = False
    #----------------------------------------------------------

    def table_exists(self, table_name):
        self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = self.cursor.fetchone()
        return result is not None
    #----------------------------------------------------------

    def create_table(self, table_name):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255),
            file_arrival_time DATETIME,
            domain VARCHAR(255),
            resolution VARCHAR(255)
        )
        """
        self.run_query(create_table_query)
        # self.connection.commit()
    #----------------------------------------------------------
def set_db_info( config, configObj):
        """
           Set DB info to be used later...?
        """
        configObj.confdb.user = config['databases.config.user']
        configObj.confdb.name = config['databases.config.name']
        configObj.confdb.host = config['databases.config.host']
        configObj.confdb.port = config['databases.config.port']
        configObj.confdb.region = config['databases.config.region']
        configObj.confdb.password = config['databases.config.password']
        configObj.confdb.sslrootcert = config['databases.config.sslrootcert']

        configObj.raddb.user = config['databases.radial.user']
        configObj.raddb.name = config['databases.radial.name']
        configObj.raddb.host = config['databases.radial.host']
        configObj.raddb.port = config['databases.radial.port']
        configObj.raddb.region = config['databases.radial.region']
        configObj.raddb.password = config['databases.radial.password']
        configObj.raddb.sslrootcert = config['databases.radial.sslrootcert']
