#!/usr/bin/env python
# Chris - cvaras@itsec.cl
# -*- coding: utf-8 -*-

import subprocess
import stuffs
import os
import re
from random import randint

WafLogsPath = '/opt/waf/nginx/var/log/'
DownloadLogPath = '/home/www-data/waf2py_community/applications/Waf2Py/static/logs/'

@auth.requires_login()
def ExcludeLocal():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.vars['id_rand'])
        c = a.CheckRule(request.vars['ruleid'])
        d = a.CheckName(request.vars['attack_name'])
        f = a.CheckPath(request.vars['path'])
    except:
        b = 'NO'

    if b == 'YES' and c == 'YES' and d == 'YES' and f == 'YES':
        data = db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.type == 1) & (db.exclusions.rules_id == request.vars['ruleid']) & (db.exclusions.local_path == request.vars['path'])).select(db.exclusions.rules_id, db.exclusions.local_path)
        modsec_conf = db(db.production.id_rand == request.vars['id_rand']).select(db.production.app_name, db.production.modsec_conf_data)
        if not data:
            #random custom_id
            custom_id = randint(0, 99999999)
            #add rule id to exclusions in db
            db.exclusions.insert(rules_id=request.vars['ruleid'], id_rand=request.vars['id_rand'], custom_id=custom_id, local_path=request.vars['path'], type=1, attack_name=request.vars['attack_name'], user=session['auth']['user']['username'])

            #get updated rules id
            rulesid = db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.type == 1)).select(db.exclusions.rules_id, db.exclusions.local_path, db.exclusions.custom_id)

            #Recreate the rules
            rules = '#ExclusionLocal\n'
            for i in rulesid:
                rules = rules + "SecRule REQUEST_URI \"@beginswith "+i['local_path']+"\" \"id:"+str(i['custom_id'])+",phase:1,pass,nolog, ctl:ruleRemoveById="+i['rules_id']+"\"\n"
            rules_list = rules
            #replace old rules with new ones
            replace = re.sub(r'^(##\w+Local\w+##\n).*(##\w+Local\w+##)', r'\1%s\2' %(rules_list.decode("utf-8")), modsec_conf[0]['modsec_conf_data'], flags=re.S | re.M)
            db(db.production.id_rand == request.vars['id_rand']).update(modsec_conf_data=replace)#'\n'.join(r))
            db.commit()
            UpdateFiles = stuffs.CreateFiles()
            try:
                UpdateFiles.CreateModsecConf('prod', modsec_conf[0]['app_name'], replace)
                a = stuffs.Nginx()
                b = a.Reload()
                #NewLogApp(db2, auth.user.username, "Mode: prod " +  data[0]['app_name'])
            except Exception as e:
                #NewLogError(db2, auth.user.username, "Mode: " + str(e))
                session.flash = e
            response.flash = 'Rule has been excluded locally'
            r = 'Rule has been excluded locally'
        else:
            response.flash = 'Rule ID or Path already excluded'
            r = 'Rule ID already excluded'

    else:
        response.flash = 'Error in data supplied'
        r = 'Error in data supplied'
    #print b,c,d,f
    return response.json(r)

@auth.requires_login()
def ExcludeGlobal():
    #import changeconfig
    a = stuffs.Filtro()
    try:

        b = a.CheckStr(request.vars['id_rand'])
        c = a.CheckRule(request.vars['ruleid'])
        d = a.CheckName(request.vars['attack_name'])
    except:
        b = 'NO'
    if b == 'YES' and c == 'YES' and d == 'YES':

        data = db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.type == 0) & (db.exclusions.rules_id == request.vars['ruleid'])).select(db.exclusions.rules_id)
        modsec_conf = db(db.production.id_rand == request.vars['id_rand']).select(db.production.app_name, db.production.modsec_conf_data)
        if not data:
            #add rule id to exclusions in db
            db.exclusions.insert(rules_id=request.vars['ruleid'], id_rand=request.vars['id_rand'], type=0, attack_name=request.vars['attack_name'], user=session['auth']['user']['username'])

            #get updated rules id
            rulesid = db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.type == 0)).select(db.exclusions.rules_id)
            #change = changeconfig.Change()
            rules = '#ExclusionGLobally\n'
            for i in rulesid:
                rules = rules + "SecRuleRemoveById " + str(i['rules_id']) + '\n'
            rules_list = rules

            replace = re.sub(r'^(##\w+Global\w+##\n).*(##\w+Global\w+##)', r'\1%s\2' %(rules_list.decode("utf-8")), modsec_conf[0]['modsec_conf_data'], flags=re.S | re.M)
            db(db.production.id_rand == request.vars['id_rand']).update(modsec_conf_data=replace)#'\n'.join(r))
            db.commit()
            UpdateFiles = stuffs.CreateFiles()
            try:
                UpdateFiles.CreateModsecConf('prod', modsec_conf[0]['app_name'], replace)
                a = stuffs.Nginx()
                b = a.Reload()
                #NewLogApp(db2, auth.user.username, "Mode: prod " +  data[0]['app_name'])
            except Exception as e:
                #NewLogError(db2, auth.user.username, "Mode: " + str(e))
                session.flash = e
            response.flash = 'Rule has been excluded globally'
            r = 'Rule has been excluded globally'
        else:
            response.flash = 'Rule ID already excluded'
            r = 'Rule ID already excluded'

    else:
        response.flash = 'Error in data supplied'
        r = 'Error in data supplied'

    return response.json(r)


@auth.requires_login()
def GeneralDenyLogs():

    cmd = 'tac /opt/waf/nginx/var/log/error | head -400'
    out1 = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    msg = out1.communicate()[0]

    return dict(msg=msg, page="General Deny-Error Logs", icon="fa fa-search", title="Waf Logs")

@auth.requires_login()
def WafLogs():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
        query =  db(db.production.id_rand == request.args[0]).select(db.production.app_name)
        if not query:
            n = True
        else:
            n = False
    except:
        b = 'NO'
    if b == 'YES' and n == False:
        id_rand = request.args[0]
        subprocess.Popen(['sudo', 'chown', '-R', 'www-data.www-data', '/opt/waf/nginx/var/log/'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.Popen(['sudo', 'chmod', '755', '-R', '/opt/waf/nginx/var/log/'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        query =  db(db.production.id_rand == request.args[0]).select(db.production.app_name)
        #Access Logs
        cmd = 'tac /opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_access.log | head -300' 
        out1 = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg, err = out1.communicate()
        #print err
        access_list=[]
        for i in msg.splitlines():
            access_list.append(i)
            
        #Error Logs
        cmd2 = 'tac /opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_error.log | head -300' 
        out2 = subprocess.Popen(cmd2, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg2, err2 = out2.communicate()
        #print err2
        error_list=[]
        for e in msg2.splitlines():
            error_list.append(e)
        
        #Error Logs
        cmd3 = 'tac /opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_debug.log | head -300' 
        out3 = subprocess.Popen(cmd3, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg3, err3 = out3.communicate()
        #print err2
        debug_list=[]
        for f in msg3.splitlines():
            debug_list.append(f)
        
        #Download Logs
        logs_file = db(db.logs_file.id_rand == request.args[0]).select(db.logs_file.id_rand, db.logs_file.log_name,
                                                                   db.logs_file.size, db.logs_file.type,
                                                                   db.logs_file.date, db.logs_file.id_rand2)
        #Count Criticals, medium, notice, alert, error.
        summary = {}
        for severity in ['CRITICAL', 'WARNING', 'ALERT', 'NOTICE', 'ERROR']:
            cmd4 = 'grep -Eho "\[severity \\"'+severity+'\\"" /opt/waf/nginx/var/log/' + query[0]['app_name'] + '/' + query[0]['app_name'] + '_debug.log | wc -l'
            #print 'Cmd: ', cmd4
            out4 = subprocess.Popen(cmd4, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            msg4, err4 = out4.communicate()
            #print msg4
            summary[severity] = msg4

        #Count access logs
        cmd5 = '/usr/bin/wc -l < /opt/waf/nginx/var/log/' + query[0]['app_name'] + '/' + query[0]['app_name'] + '_access.log'
        out5 = subprocess.Popen(cmd5, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg5, err5 = out5.communicate()
        requests = msg5.replace("\n","")
        #print "request", len(requests)
        if len(requests) == 0:
            requests = 0
        #print "request",requests
        db2(db2.defend_log_summary.id_rand == request.args[0]).update(id_rand=request.args[0], app_name=query[0]['app_name'], critical=summary['CRITICAL'], warning=summary['WARNING'],
                               notice=summary['NOTICE'], error=summary['ERROR'], requests=requests)
        #alert = summary['ALERT'],
    else:
        response.flash = 'Error in data supplied'
        redirect(URL('default','Websites'))
        id_rand = '#'
     
    return dict(page=query[0]['app_name']+" Logs", title="", icon="", summary=summary,logs_file=logs_file, access_logs=access_list, error_logs=error_list, debug_logs=debug_list, id_rand=id_rand)

#not used yet, we still missing the view...
@auth.requires_login()
def AccessLogs():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
    except:
        b = 'NO'
    if b == 'YES':
        query =  db(db.production.id_rand == request.args[0]).select(db.production.app_name)
        # - %s' %(session['auth']['user']['first_name']) query[0]
        cmd = 'tac /opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_access.log | head -400'
        out1 = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg,err = out1.communicate()
        access_list = []
        #print err
        for i in msg:
            access_list.append(dict(access_log=i))

    else:
        access_list.append('Error in data suplied')
    return response.json({'access_logs':access_list})

@auth.requires_login()
def WafLogs_frame():
    import re

    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
    except:
        b = 'NO'
    logs_dict = {}
    logs_list = []

    if b == 'YES':
        query = db(db.production.id_rand == request.args[0]).select(db.production.app_name, db.production.id_rand)
        cmd="cd /opt/waf/nginx/var/log/%s/audit_logs/; ls -dt -1 $PWD/**/**/* | head -200" %(query[0]['app_name'])

        out1 = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg = out1.communicate()[0]
        for i in msg.splitlines():
            #print i
            p = subprocess.Popen(['cat', i],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logs_data, err_logs = p.communicate()
            
            if '[id "' in logs_data and '[file "/opt/waf/nginx/etc/' in logs_data and '[msg "' in logs_data:
                
                try:
                    uri_path = re.search('^([A-Z]\w+) ([\/[\w+].* )', logs_data,  re.MULTILINE).group(2)
                except Exception as e:
                    #print e
                    uri_path = "I couldn't detect the path :/"
                
                
                #get the block with the attack info
                attack_info = re.search(r'^--\w+-H--\n(.*)\n\n--\w+-Z--\n', logs_data, flags=re.S | re.M).group(0)
                
                #get date and the attacker ip
                first_block = re.search(r'^--\w+-A--\n(.*)\n--\w+-B--\n', logs_data, flags=re.S | re.M).group(0)
                date = re.search('\d+\/\w+\/\d+:\d\d:\d\d:\d\d', first_block).group(0)
                attacker_ip = re.search('\[\d{0,2}\/\w{0,3}\/\d{0,4}:\d\d:\d\d:\d\d.--\d*\] .+ \d+.\d+.\d+.\d+', first_block).group(0)
                attacker_ip = re.search('\d+\.\d+\.\d+\.\d+', first_block).group(0)
                
                #get headers
                try:
                    headers = re.search(r'^--\w+-B--\n(.*)\n--\w+-E--\n', logs_data, flags=re.S | re.M).group(0)
                except:
                    headers = re.search(r'^--\w+-B--\n(.*)\n--\w+-H--\n', logs_data, flags=re.S | re.M).group(0)
                
                #get body
                try:
                    body = re.search(r'^--\w+-E--\n(.*)\n--\w+-H--\n', logs_data, flags=re.S | re.M).group(0)
                except:
                    body='\n**Empty Body**'
                
                #sometimes severity is not set in the rules, in that case we do a try except
                try:
                    severity = re.search('"\] \[severity "\w+.*?"\]', attack_info).group(0)
                    severity = severity.replace('"] [severity "', '').replace('"]','')
                except:
                    severity = 'No severity set in rules'
            
                ruleid = re.search('"\] \[id "\d+.*?"\]', attack_info).group(0)
                ruleid = ruleid.replace('"] [id "','').replace('"]','')
                title = re.search('\[msg "\w+.*?"\]', attack_info).group(0)
                title = title.replace('[msg "','').replace('"]','')
                try:
                    #some rules does not have "data"
                    attack = re.search('\[data "\w+.*?"\]', attack_info).group(0)
                    attack = attack.replace('[data "','')
                    attack = attack[:-2]
                except:
                    attack = ''
             
                logs_list.append(dict(titulo=title, fecha=date, headers=headers, body=unicode(body, errors='ignore'), ataque=attack, modsec_info=attack_info,rule=ruleid, severidad=severity, attacker=attacker_ip, data='logs_data', path=uri_path,randid=query[0]['id_rand']))
                
            else:
                pass
    else:
        redirect(URL('WafLogs'))
    return response.json({'data': logs_list})

@auth.requires_login()
def AppLogs():

    query = db2().select(db2.log_app.ALL, orderby=~db2.log_app.id)

    return dict(query=query, page="Application Logs", title="", icon="")

@auth.requires_login()
def ErrorAppLogs():
    query = db2().select(db2.log_error.ALL, orderby=~db2.log_error.id)
    return dict(query=query, page="Error Application Logs", title="", icon="")

@auth.requires_login()
def ExcludedRules():

    a = stuffs.Filtro()
    b = a.CheckStr(request.args[0])
    rule_list = []
    if b == 'YES':
        query = db(db.exclusions.id_rand == request.args[0]).select(db.exclusions.attack_name,
                                                             db.exclusions.id_rand, db.exclusions.rules_id, db.exclusions.type,
                                                             db.exclusions.user, db.exclusions.local_path,
                                                            )
        if query:

            for row in query:
                #print row['attack_name']
                rule_list.append(dict(attack_name=row['attack_name'], rule_id=row['rules_id'], id_rand=row['id_rand'], tipo=row['type'], path=row['local_path'], user=row['user']))
        else:
            rule_list.append('There are no excluded rules')

    else:
        rule_list.append('Error in data supplied')

    return response.json({'rules': rule_list})

@auth.requires_login()
def DeleteRule():
    import changeconfig
    a = stuffs.Filtro()
    #print request.vars['type']
    try:
        b = a.CheckStr(request.vars['id_rand'])
        c = a.CheckRule(request.vars['ruleid'])
        d = int(request.vars['type'])
        
    except:
        b = 'NO'

    if b == 'YES' and c == 'YES' and request.vars['type'] == '0':
        #remove rule from exclusions table
        db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.rules_id == request.vars['ruleid']) & (db.exclusions.type == 0)).delete()
        modsec = db(db.production.id_rand == request.vars['id_rand']).select(db.production.modsec_conf_data, db.production.app_name,db.production.mode)
    
        #change configuration
        #Change return a dictionary with status message and the new list whith changed configuration ex: {'newconf_list': 'data', 'message':'success or error'}
        change = changeconfig.Change()
        alter = change.Text(modsec[0]['modsec_conf_data'], 'SecRuleRemoveById '+request.vars['ruleid'], '')
        db(db.production.id_rand == request.vars['id_rand']).update(modsec_conf_data='\n'.join(alter['new_list']))
        
        #get new modsec conf
        new_modsec = db(db.production.id_rand == request.vars['id_rand']).select(db.production.modsec_conf_data)
        UpdateFiles = stuffs.CreateFiles()
        try:
            UpdateFiles.CreateModsecConf('prod', modsec[0]['app_name'], new_modsec[0]['modsec_conf_data'])
            stuffs.Nginx().Reload()
            #NewLogApp(db2, auth.user.username, "Mode: prod " +  data[0]['app_name'])
        except Exception as e:
            #NewLogError(db2, auth.user.username, "Mode: " + str(e))
            session.flash = e
        response.flash = 'Rule deleted succesfully'
        r = 'Rule deleted succesfully'
            
    elif b == 'YES' and c == 'YES' and request.vars['type'] == '1':
        db((db.exclusions.id_rand == request.vars['id_rand']) & (db.exclusions.rules_id == request.vars['ruleid']) & (db.exclusions.type == 1)).delete()
        modsec = db(db.production.id_rand == request.vars['id_rand']).select(db.production.modsec_conf_data, db.production.app_name,db.production.mode)
    
        #change configuration
        #Change return a dictionary with status message and the new list whith changed configuration ex: {'newconf_list': 'data', 'message':'success or error'}
        change = changeconfig.Change()
        alter = change.Text(modsec[0]['modsec_conf_data'], 'ctl:ruleRemoveById='+request.vars['ruleid'], '')
        db(db.production.id_rand == request.vars['id_rand']).update(modsec_conf_data='\n'.join(alter['new_list']))
        #get new modsec conf
        new_modsec = db(db.production.id_rand == request.vars['id_rand']).select(db.production.modsec_conf_data)
        UpdateFiles = stuffs.CreateFiles()
        try:
            UpdateFiles.CreateModsecConf('prod', modsec[0]['app_name'], new_modsec[0]['modsec_conf_data'])
            stuffs.Nginx().Reload()
            #NewLogApp(db2, auth.user.username, "Mode: prod " +  data[0]['app_name'])
        except Exception as e:
            #NewLogError(db2, auth.user.username, "Mode: " + str(e))
            session.flash = e
        response.flash = 'Rule deleted succesfully'
        r = 'Rule deleted succesfully'
            
    else:
        r = 'Error in data supplied'
    
    return response.json(r)

@auth.requires_login()
def DownloadError():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
        
    except:
        b = 'NO'
        
    if b == 'YES':
        random = randint(0, 999999999)
        query = db(db.production.id_rand == request.args[0]).select(db.production.app_name, db.production.id_rand)
        #print query
        out1 = subprocess.Popen(['/usr/bin/zip', '-j','/home/www-data/waf2py_community/applications/Waf2Py/static/logs/error_logs_'+query[0]['app_name']+'_'+str(random)+'.zip', '/opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_error.log'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg,err = out1.communicate()
        r = A('Error_logs.zip', _href='/Waf2Py/static/logs/error_logs_'+query[0]['app_name']+'_'+str(random)+'.zip') 
    else:
        session.flash = 'Error in data supplied'
        r = ''
    return r


@auth.requires_login()
def DownloadLogZip():
    import random
    import string
    import time
    import os
    a = stuffs.Filtro()
    try:
        #print request.args[1]
        b = a.CheckStr(request.args[0])
        c = a.CheckStr35(request.args[1])
        #print b,c
    except:
        b = 'NO'
        c = 'NO'
    if b == 'YES' and c == 'YES':
        chars = string.letters + string.digits
        pwdSize = 10

        rand = ''.join((random.choice(chars)) for x in range(pwdSize))
        log_name = db((db.logs_file.id_rand == request.args[0]) & (db.logs_file.id_rand2 == request.args[1])).select(
            db.logs_file.log_name
          )
        app_name = db(db.production.id_rand == request.args[0]).select(
            db.production.app_name
          )
        cmd = '/bin/cp ' + WafLogsPath+app_name[0]['app_name']+'/'+log_name[0]['log_name'] + ' ' + DownloadLogPath+rand+log_name[0]['log_name']
        out1 = os.system(cmd)
        if out1 == 0:
            redirect(URL('static', 'logs/'+rand+log_name[0]['log_name']))
        else:
            session.flash = 'Error in data supplied'
            redirect(URL('default','Websites'))


    else:
        session.flash = 'Error in data supplied'
        redirect(URL('default','Websites'))

        

#not used yet, we still missing the view...
@auth.requires_login()
def DebugLogs():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
    except:
        b = 'NO'
    if b == 'YES':
        query =  db(db.production.id_rand == request.args[0]).select(db.production.app_name)
        # - %s' %(session['auth']['user']['first_name']) query[0]
        cmd = 'tac /opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_debug.log | head -400'
        out1 = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg,err = out1.communicate()
        access_list = []
        #print err
        for i in msg:
            access_list.append(dict(access_log=i))

    else:
        access_list.append('Error in data suplied')
    return response.json({'debug_logs':debug_list})

@auth.requires_login()
def DownloadDebug():
    a = stuffs.Filtro()
    try:
        b = a.CheckStr(request.args[0])
        
    except:
        b = 'NO'
        
    if b == 'YES':
        random = randint(0, 999999999)
        query = db(db.production.id_rand == request.args[0]).select(db.production.app_name, db.production.id_rand)
        print query
        out1 = subprocess.Popen(['/usr/bin/zip', '-j','/home/www-data/waf2py_community/applications/Waf2Py/static/logs/debug_logs_'+query[0]['app_name']+'_'+str(random)+'.zip', '/opt/waf/nginx/var/log/'+query[0]['app_name']+'/'+query[0]['app_name']+'_debug.log'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg,err = out1.communicate()
        r = A('Debug_logs.zip', _href='/Waf2Py/static/logs/debug_logs_'+query[0]['app_name']+'_'+str(random)+'.zip') 
    else:
        session.flash = 'Error in data supplied'
        r = ''
    return r
