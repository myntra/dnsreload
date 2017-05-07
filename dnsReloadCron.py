#!/usr/bin/python

import os
import urllib2
import commands
import json
import time
import logging
from os.path import exists
import jinja2
import requests
import httplib
import array
import configs
import sh
import time
import filecmp
import sys
from subprocess import Popen, PIPE

LOGFILE = configs.LOGFILE
TEMPLATE_FILE = configs.TEMPLATE_FILE
ZONE_FILE = configs.ZONE_FILE
TMP_ZONE_FILE = configs.TMP_ZONE_FILE
BACKUP_ZONE_FILE = configs.BACKUP_ZONE_FILE


LIVE_RECORDS_FILE = configs.LIVE_RECORDS_FILE
EDIT_RECORDS_FILE =  configs.EDIT_RECORDS_FILE
ADD_RECORDS_FILE = configs.ADD_RECORDS_FILE
SOA_FILE = configs.SOA_FILE
TEMPLATE_ZONE_FILE  = configs.TEMPLATE_ZONE_FILE
TEST_ZONE_FILE  = configs.TEST_ZONE_FILE

SERIAL_FILE = configs.SERIAL_FILE
OLD_SERIAL_SOA_FILE = configs.OLD_SERIAL_SOA_FILE
OLD_SERIAL_TMP_ZONE_FILE = configs.OLD_SERIAL_TMP_ZONE_FILE

SERIAL = ""

#Logging
def logme(lcategory,logstring):
    logging.basicConfig(format='%(levelname)s: %(asctime)s: %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',filename=LOGFILE,level=logging.DEBUG)
    if lcategory == "debug":
        logging.debug(logstring)
    elif lcategory == "info":
        logging.info(logstring)
    elif lcategory == "warning":
        logging.warning(logstring)
    elif lcategory == "error":
        logging.error(logstring)

#Generates the record template
def generate_template(record_json):
    '''
    This method generates the record configuration from the
    supplied template file
    '''

    template_vars = {}
    template_loader = jinja2.FileSystemLoader(searchpath='/')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(TEMPLATE_FILE)
    template_vars['name'] = record_json['name']
    template_vars['type'] = record_json['type']
    template_vars['value'] = record_json['value']
    template_vars['ttl'] = record_json['ttl']
   
    output = template.render(template_vars)
    return output

#Generates the zone template
def generate_zone_template(paramter):
    '''
    This method generates the zone configuration from the
    supplied template file
    '''

    template_vars = {}
    template_loader = jinja2.FileSystemLoader(searchpath='/')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(TEMPLATE_ZONE_FILE)
   
    template_vars['RECORD'] = paramter.get('entry','')
    template_vars['SERIAL'] = paramter.get('serial','1000')
   
    output = template.render(template_vars)
    return output

#Check the records to be added and add the templates to ADD_RECORDS_FILE
def addRecords(records):    
    
    status = True
    Output_addRecord = []

    if exists(ADD_RECORDS_FILE):
        os.system("rm -f "+ADD_RECORDS_FILE)

    for record in records:
        recordOutput = {}

        recordOutput['id'] = record['id']
        recordOutput['prev_status'] =  record['status']

        record_tmpl = generate_template(record)
        paramter = {}
        paramter['entry'] = record_tmpl
        zone_template =  generate_zone_template(paramter)

        f = open(TEST_ZONE_FILE,'w')
        f.write(zone_template)
        f.close()
        
        # Replace the Original record if the zone file is correct according to the DNS
        p = Popen(['named-checkzone','testDNS',TEST_ZONE_FILE], stdin=PIPE, stdout=PIPE, stderr=PIPE) 
        output, err = p.communicate() 
        rc = p.returncode 
  
        if rc == 0:
            add_file = open(ADD_RECORDS_FILE,'a')
            add_file.write(record_tmpl)
            
            recordOutput['status'] = 'SUCCESS'
            logme('info',' addRecords: successful addition of the record: '+record_tmpl)
        else:
            recordOutput['status'] = 'FAILED'
            logme('error',' addRecords: error in addition of record: '+record_tmpl+' Err: '+str(err))

        Output_addRecord.append(recordOutput)

    return Output_addRecord

#Generates the live records templates and store them in LIVE_RECORDS_FILE
def liveRecords(records):
    Output_liveRecord = []
    records_template = ""
    if exists(LIVE_RECORDS_FILE):
        os.system("rm -f "+LIVE_RECORDS_FILE)

    for record in records:
        record_tmpl = generate_template(record)
        records_template += record_tmpl

    f = open(LIVE_RECORDS_FILE,'w')
    f.write(records_template)
        

#Check the records to be edited and add the templates to EDIT_RECORDS_FILE
def editRecords(records):

    if exists(EDIT_RECORDS_FILE):
        os.system("rm -f "+EDIT_RECORDS_FILE)
    
    Output_editRecord = []
    for record in records:
        new_value = json.loads(record['new_value'])
        recordOutput = {}
        
        recordOutput['id'] = record['id']
        recordOutput['prev_status'] =  record['status']

        record_tmpl = generate_template(new_value)
        prev_record = generate_template(record)
        parameter = {}
        parameter['entry'] = record_tmpl
        zone_template =  generate_zone_template(parameter)

        f = open(TEST_ZONE_FILE,'w')
        f.write(zone_template)
        f.close()

        p = Popen(['named-checkzone','testDNS',TEST_ZONE_FILE], stdin=PIPE, stdout=PIPE, stderr=PIPE) 
        output, err = p.communicate() 
        rc = p.returncode 
        
        if rc == 0:
            edit_file = open(EDIT_RECORDS_FILE,'a')
            edit_file.write(record_tmpl)
            logme('info',' editRecords: successful updation  of the record: '+prev_record)
            recordOutput['status'] = 'SUCCESS'
        else:
            logme('error',' editRecords: unsuccessful updation  of the record: '+prev_record+' Err: '+str(err))
            recordOutput['status'] = 'FAILED'
        
        Output_editRecord.append(recordOutput)

    return Output_editRecord

#Put the latest serial to the SOA_FILE
def change_serial():
    global SERIAL
    parameter = {}
    parameter['serial'] = str(int(round(time.time())))
    SERIAL = parameter['serial'] #Global variable
    soa_template =  generate_zone_template(parameter)
    f = open(TEST_ZONE_FILE,'w')
    f.write(soa_template)
    f.close()

    #Generating the SOA with Stored serial
    if exists(SERIAL_FILE):
        f = open(SERIAL_FILE,'r')
        serial_from_file = f.read()
        f.close()
        parameter = {}
        parameter['serial'] = serial_from_file
        old_serial_soa_template = generate_zone_template(parameter)
        f2 = open(OLD_SERIAL_SOA_FILE,'w')
        f2.write(old_serial_soa_template)
        f2.close()

    p = Popen(['named-checkzone','testDNS',TEST_ZONE_FILE], stdin=PIPE, stdout=PIPE, stderr=PIPE) 
    output, err = p.communicate() 
    rc = p.returncode 
    
    if rc == 0:
        if exists(SOA_FILE):
            os.system("rm -f " + SOA_FILE)
        f = open(SOA_FILE,'w')
        f.write(soa_template)
        f.close()
        
        #First time initializing file SERIAL_FILE
        if exists(SERIAL_FILE) != True:
            logme('info','No serial_FILE') 
            f1 =open(SERIAL_FILE,'w')
            f1.write(SERIAL)
            f1.close()
        
        #First time initializing file OLD_SERIAL_SOA_FILE
        if exists(OLD_SERIAL_SOA_FILE) != True:
            logme('info','No OLD_SERIAL_SOA_FILE') 
            f2 =open(OLD_SERIAL_SOA_FILE,'w')
            f2.write(soa_template)
            f2.close()

        logme('info',' change_serial: successful updation of the Serial')
    else:
        logme('error',' change_serial: unsuccessful updation  of the Serial.  Err: '+str(err))

#API call to the server to get all the records
def get_records():
    
    try:
        get_url = configs.GETURL
        payload = {"zone_name":configs.ZONE}
        payload =json.dumps(payload)
        req = urllib2.Request(get_url, payload, headers = {'API_KEY': configs.APIKEY, 'Content-Type': 'application/json'})
        response = json.load(urllib2.urlopen(req))
        add_records = response['add_records']
        edit_records = response['edit_records']
        live_records = response['live_records']
        if exists(TMP_ZONE_FILE):
            os.system("rm -f "+TMP_ZONE_FILE)
        
        #Removing all the conf files
        conf_files = [SOA_FILE, LIVE_RECORDS_FILE, EDIT_RECORDS_FILE, ADD_RECORDS_FILE, OLD_SERIAL_SOA_FILE, OLD_SERIAL_TMP_ZONE_FILE]
        for file in conf_files:
            if exists(file):
                os.system("rm -f "+file)

        successful_pull = pullingLatestZone()

        
        if successful_pull:
            if exists(TMP_ZONE_FILE):
                os.system("rm -f  "+TMP_ZONE_FILE)
        
            output ={}
            liveRecords(live_records)
            output['add_records'] = addRecords(add_records)
            output['edit_records'] = editRecords(edit_records)
            change_serial()
            generate_zone_cfg()
            
            changingZoneFile()
            post_zone_change(output)
        else:
            logme('error','Error in pulling the latest changes')
    
    except urllib2.HTTPError, e:
        logme('error',' get_records: HTTPError = ' + str(e.message))
    except urllib2.URLError, e:
        logme('error',' get_records: URLError = ' + str(e.reason))
    except httplib.HTTPException, e:
        logme('error',' get_records: HTTPException')
    except Exception:
        import traceback
        logme('error',' get_records: generic exception: ' + traceback.format_exc())
 
 #Generates the Bind Format Zone file from the conf files
def generate_zone_cfg():
    try:
        files = [SOA_FILE, LIVE_RECORDS_FILE, EDIT_RECORDS_FILE, ADD_RECORDS_FILE]
        f = open(TMP_ZONE_FILE, "w")

        for file in files: 
            if exists(file) and os.path.isfile(file):
                fptr  = open(file,'r')
                data = fptr.read()
                fptr.close()
                f.write(data)
        f.write('\n')
        f.close()

        files1 = [OLD_SERIAL_SOA_FILE, LIVE_RECORDS_FILE, EDIT_RECORDS_FILE, ADD_RECORDS_FILE]
        f1 = open(OLD_SERIAL_TMP_ZONE_FILE, "w")

        for file in files1: 
            if exists(file) and os.path.isfile(file):
                fptr  = open(file,'r')
                data = fptr.read()
                fptr.close()
                f1.write(data)
        f1.write('\n')
        f1.close()

       
    except Exception,e:
        logme('error',' generate_zone_cfg: Error in generating configuration'+str(e))
    
#It pushes the record status based on the record acceptance by BIND Syntax
def post_zone_change(output):
    payload = json.dumps(output)
    post_url = configs.POSTURL

    try:
        postreq = urllib2.Request(post_url, payload,headers={'API_KEY': configs.APIKEY,'Content-Type': 'application/json'})
        postcall = urllib2.urlopen(postreq)
        response = postcall.read()
        postcall.close()

    except urllib2.HTTPError, e:
        logme('error',' post_zone_change: HTTPError = ' + str(e.message))
    except urllib2.URLError, e:
        logme('error',' post_zone_change: URLError = ' + str(e.reason))
    except httplib.HTTPException, e:
        logme('error',' post_zone_change: HTTPException')
    except Exception:
        import traceback
        logme('error',' post_zone_change: generic exception: ' + traceback.format_exc())


#Git module to pull the zone file from git repo
def pullingLatestZone():
    p = Popen([configs.GIT_MODULE,'-pullFlag','True'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    for line in iter(p.stderr.readline, ''):
        logme('info',line)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0 :
        logme('info','Got latest pull from Git repo')
        return True
    else:
        logme('error','Unsuccessful pull from Git repo'+str(err))
        return False

#Changes the zone file if there are any changes in the records
def changingZoneFile():
    try:
        if exists(TMP_ZONE_FILE):
            if exists(OLD_SERIAL_TMP_ZONE_FILE):
                flag_same = filecmp.cmp(OLD_SERIAL_TMP_ZONE_FILE, ZONE_FILE)
                if flag_same != True:
                    # Backup ZONE file
                    if not exists(BACKUP_ZONE_FILE):
                        os.system("cp "+ZONE_FILE+ " "+BACKUP_ZONE_FILE)
                    else:
                        os.system("rm -f "+BACKUP_ZONE_FILE)
                        os.system("cp "+ZONE_FILE+ " "+BACKUP_ZONE_FILE)

                    #Updating the SERIAL FILE
                    f = open(SERIAL_FILE,'w')
                    f.write(SERIAL)
                    f.close()
                    os.system("cp " +TMP_ZONE_FILE+" "+ZONE_FILE)
                    os.system("rm -f "+TMP_ZONE_FILE)

                    gitPush()
                else:
                    logme('info','NO changes in the ZONE FILE')
            else:
                logme('error','OLD_SERIAL_TMP_ZONE_FILE not found for comparison '+str(err))
           
    except Exception, e:
        logme('error',' ChangingZoneFile '+str(e))

#Pushes all the changes to the zone file to GITHUB
def gitPush():
    p = Popen([configs.GIT_MODULE], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    for line in iter(p.stderr.readline, ''):
        logme('error',line)    
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0 :
        logme('info','Successful Git Push')
    else:
        logme('error','Unsuccessful Git Push'+str(err))
  
if __name__ == '__main__':
    logme('info','Service is Running....')
    get_records()
