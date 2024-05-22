""" This module installs Uptycs onto GCP Compute Engines 
    v0.2
"""

import googleapiclient.discovery
import json
import logging
from google.cloud import storage
import datetime 
import glob
import os

class LogHandler:
    """ Class to handle logging to local file and console at the same time 
        The method copy_to_bucket() can be used to copy the file to 
        a storage bucket at the end of all processing.
    """ 
    def __init__(self, log_name_string='install_uptycs', level=20):
        # Create a logger
        self.logger = logging.getLogger(log_name_string)
        self.logger.setLevel(level)

        # Create a log filename that includes the current datetime down to the second
        now = datetime.datetime.today().replace(microsecond=0)
        self.log_filename = log_name_string + '-' + str(now).replace(' ', '_').replace(':', '_') + '.log'

        # Create a formatter to define the log format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Create a file handler to write logs to a file
        file_handler = logging.FileHandler(self.log_filename)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Create a stream handler to log to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # You can set the desired log level for console output
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def copy_to_bucket(self, bucket_name):
        # copy the log file to a storage bucket, under folder 'logs'
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob('logs/' + self.log_filename)
        blob.upload_from_filename(self.log_filename)

    def remove_old_local_logs(self):
        """ Delete all old local log files (keep the current one).
            We keep all the log files in a cloud storage bucket. 
            A future feature might keep n files only in the storage bucket.
        """
        log_file_list = glob.glob('*.log')
        for f in log_file_list: 
            if f != self.log_filename:
                os.remove(f)
        

def file_to_json(filename: str):
    """ Opens a file and returns the json content as a dict """
    with open(filename) as f:
        return json.load(f)


def main():
    # read the configuration into a dict from the file: config.json  
    config = file_to_json('config.json') 

    # create a logger 
    log = LogHandler(log_name_string='install_uptycs', level=logging.INFO)

    msg = 'Starting installation of Uptycs agents for GCP projects: ' + json.dumps(config['project_list'])
    log.info(msg)

    msg = 'Zones read from config.json: ' + json.dumps(config['zone_list'])
    log.info(msg) 

    msg = 'Using storage bucket (for agent files and logs): ' + config['storage_bucket']
    log.info(msg) 
    
    compute = googleapiclient.discovery.build('compute', 'v1')
    for p in config['project_list']: 
        for z in config['zone_list']:
            result = compute.instances().list(project=p, zone=z).execute()
            if result.get('items'): 
                for vm in result.get('items'):
                    print('project: %s, zone: %s' % (p, z))
                    print(vm['name'])
                    print(vm['id'])
                    print(vm['status'])
                    print(vm['disks'][0]['licenses'])
                    #print(vm)
                    print(' ')

    # copy the log file to the storage bucket
    log.copy_to_bucket(config['storage_bucket'])

    # remove log files on local storage that are older than the current one 
    log.remove_old_local_logs()

if __name__ == "__main__":
    main()

