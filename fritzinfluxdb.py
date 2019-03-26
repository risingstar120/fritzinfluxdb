#!/usr/bin/env python

import os
import sys
import signal
import configparser
import fritzconnection
import influxdb
import time
from datetime import datetime
import argparse
import logging

running = True
default_config = os.path.join(os.path.dirname(__file__), 'default.ini')
default_loglevel = logging.INFO


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_file", default=default_config,
                        help="define config file (default: " + default_config + ")")
    parser.add_argument("-d", "--debug", help="switch on debug mode", action="store_true")
    args = parser.parse_args()
    return args


def shutdown(signal, frame):
    global running
    running = False

# sometimes integers are returned as string
# try to sanatize this a bit
def sanatize_fb_return_data(results):

    return_results = {}
    for instance in results:
        # turn None => 0
        if results[instance] == None:
            return_results.update({instance: 0})
        else:
            # try to parse as int
            try:
                return_results.update({instance: int(results[instance])})
            # keep it a string if this fails
            except ValueError:
                return_results.update({instance: results[instance]})

    return return_results

def query_points(fc, services):
    result = {}

    for service, content in services.items():

        for action in content['actions']:

            if 'value_instances' in content:

                this_result = fc.call_action(service, action)

                for instance in content['value_instances']:

                    rewrite_name = None

                    if ':' in instance:
                        instance, rewrite_name = instance.split(':')
                        instance = instance.strip()
                        rewrite_name = rewrite_name.strip()

                    # only keep desired result key
                    if instance in this_result:
                        result.update({ rewrite_name if rewrite_name != None else instance : this_result[instance]})
            else:
                result.update(fc.call_action(service, action))

    return sanatize_fb_return_data(result)


def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def check_db_status(db_handler, db_name):
    try:
        dblist = db_handler.get_list_database()
        db_found = False
        for db in dblist:
            if db['name'] == db_name:
                db_found = True
        if not db_found:
            logging.info('Database <%s> not found, trying to create it' % db_name)
            db_handler.create_database(db_name)
        else:
            logging.debug('Influx Database <%s> exists' % db_name)
        return True
    except Exception as e:
        logging.error('Problem creating database: %s', e)
        return False


def get_services(config, section_name_start):
    this_sections = [s for s in config.sections() if s.startswith(section_name_start)]
    this_services = {}
    for s in this_sections:
        this_services.update({config.get(s, 'service'): {'actions': config.get(s, 'actions').split("\n")}})
        if config.has_option(s, 'value_instances'):
            this_services[config.get(s, 'service')].update(
                {'value_instances': config.get(s, 'value_instances').split("\n")})

    return this_services


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # parse command line arguments
    args = parse_args()

    # set logging
    log_level = logging.DEBUG if args.debug == True else default_loglevel
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # check if config file exists
    if not os.path.isfile(args.config_file):
        logging.error("config file \"%s\" not found" % args.config_file)
        exit(1)

    # read config from ini file
    config = read_config(args.config_file)

    logging.info("Done parsing config file")

    # set up influxdb handler
    influxdb_client = influxdb.InfluxDBClient(
        config.get('influxdb', 'host'),
        config.getint('influxdb', 'port'),
        config.get('influxdb', 'username'),
        config.get('influxdb', 'password'),
        config.get('influxdb', 'database'),
    )

    # check influx db status
    check_db_status(influxdb_client, config.get('influxdb', 'database'))

    logging.info("Connection to InfluxDB established and database present")

    # create unauthenticated FB client handler
    fritz_client_unauth = fritzconnection.FritzConnection(
        address=config.get('fritzbox', 'host'),
        port=config.get('fritzbox', 'port'),
    )

    # test connection
    if fritz_client_unauth.modelname is None:
        logging.error("Failed to connect to %s" % config.get('fritzbox', 'host'))
        exit(1)

    # create authenticated FB client handler
    fritz_client_auth = fritzconnection.FritzConnection(
        address=config.get('fritzbox', 'host'),
        port=config.get('fritzbox', 'port'),
        user=config.get('fritzbox', 'username'),
        password=config.get('fritzbox', 'password')
    )

    # test connection
    if fritz_client_auth.modelname is None:
        logging.error("Failed to connect to %s" % config.get('fritzbox', 'host'))
        exit(1)

    logging.info("Successfully connected to FritzBox")

    # read services from config file
    unauth_services = get_services(config, "service")
    auth_services = get_services(config, "auth_service")

    while running:
        points = query_points(fritz_client_unauth, unauth_services)
        points.update(query_points(fritz_client_auth, auth_services))
        data = {
            "measurement": config.get('influxdb', 'measurement_name'),
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": points
        }
        try:
            logging.debug("writing data to InfluxDB")
            influxdb_client.write_points([data], time_precision="ms")
        except Exception:
            logging.error("Failed to write to InfluxDB %s" % config.get('influxdb', 'host'))

        # just sleep for 10 seconds
        time.sleep(10)


if __name__ == "__main__":
    main()
