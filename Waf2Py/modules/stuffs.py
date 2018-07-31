#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import random
import subprocess
import time
import os
import socket
import re

class Stuffs:
    def __init__(self):
        pass

    def password(self):
        #Generate a random string, 40 chars
        self.chars = string.letters + string.digits
        self.pwdSize = 40

        self.result = ''.join((random.choice(self.chars)) for x in range(self.pwdSize))
        return self.result

class Filtro:
    def __init__(self):
        pass
    
    def CheckRule(self, clean):
        self.clean = clean
        #self.isalphanum = self.clean.isalnum()
        try:
            #if no numeric input will throw an error
            int(self.clean)
            if any(c in self.clean for c in "\"/'\;.,=%#$*()[]?¿¡@{}:!|&<>¨~°^ "):
                self.aproved = 'NO'
            elif len(self.clean) <= 10:
                self.aproved = 'YES'
            else:
                self.aproved = 'NO'
        except:
            self.aproved = 'NO'
        return self.aproved
    
    def CheckStr(self, clean):
        self.clean = clean
        self.isalphanum = self.clean.isalnum()
        if len(self.clean) == 40 and self.isalphanum == True:
            self.aproved = 'YES'

        else:
            self.aproved = 'NO'

        return self.aproved
    
    def CheckStr35(self, clean):
        self.clean = clean
        self.isalphanum = self.clean.isalnum()
        if self.isalphanum == True and (len(self.clean) == 35 or len(self.clean) == 36):
            self.aproved = 'YES'

        else:
            self.aproved = 'NO'

        return self.aproved

    def CheckStrIP(self, ip):
        self.clean_ip = ip
        try:
            socket.inet_aton(self.clean_ip)
            self.aproved = 'YES'
            if any(c in self.clean_ip for c in "\"/';,%#$*=()[]{}?¿¡!@|&<>¨~°^ "):
                self.aproved = 'NO'
        except Exception as e:
            self.aproved = 'NO'

        return self.aproved
    
    def CheckPorts(self, ports):
        self.ports = ports
        if any(c in self.ports for c in "\"/';,%#$*=()[]{}:?¿¡!|&<>¨~°^ ."):
            self.aproved = 'NO'
        if re.search('[a-zA-Z]', self.ports):
            self.aproved = 'NO'
        if len(self.ports) < 2:
            self.aproved = 'NO'
        else:
            self.aproved = 'YES'
            
        
        return self.aproved
    
    def CheckName(self, name):
        self.name = name
        if any(c in self.name for c in "\"\\';,%$*=[]{}?¿¡!|<>¨~°^"):
            self.aproved = 'NO'
        else:
            self.aproved = 'YES'
            
        return self.aproved
    
    def CheckPath(self, path):
        self.path = path
        if any(c in self.path for c in "\"\\';,%$*[]{}:|<>¨~°^ "):
            self.aproved = 'NO'
        else:
            self.aproved = 'YES'
            
        return self.aproved

class Nginx:
    def __init__(self):
        pass

    def SyntaxCheck(self):
        self.process = subprocess.Popen(['sudo', '/opt/waf/nginx/sbin/nginx', '-t'], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.out, self.err = self.process.communicate()

        if 'test failed' in self.err:
            self.response = 'Bad Syntax: ' + str(self.err)
        else:
            self.response = 'OK'
        return self.response

    #Reload Nginx
    def Reload(self):
        import time
        import subprocess

        self.process = subprocess.Popen(['sudo', '/opt/waf/nginx/sbin/nginx', '-t'], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        self.out, self.err = self.process.communicate()
        if 'syntax is ok' in self.err:
            self.check = 'Syntax OK'
        else:
            self.check = 'Bad Syntax: ' + str(self.err)

        if self.check == 'Syntax OK':
            print 'estado: ', self.check
            #sometimes a single reload doesn't work as spected... we make 2 reload to solve this random issue.
            subprocess.Popen(['sudo', '/opt/waf/nginx/sbin/nginx', '-s', 'reload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
            subprocess.Popen(['sudo', '/opt/waf/nginx/sbin/nginx', '-s', 'reload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #Check if nginx is still running
            self.check1 = subprocess.Popen(['sudo','/bin/netstat', '-tulpen'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.out1 = self.check1.communicate()
            #print self.out1
            for i in self.out1:
                if 'nginx' in i:
                    self.response = 'Reload Succesfull'
                    cmd = 'printf 0 > /home/www-data/waf2py_community/applications/Waf2Py/status/reload'
                    subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    break

                else:
                    self.response = 'Failed, nginx is not running'
                    cmd = 'printf 1 > /home/www-data/waf2py_community/applications/Waf2Py/status/reload'
                    subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)



        else:
            self.response = 'Error in configuration: ' + self.check
            cmd = 'printf 1 > /home/www-data/waf2py_community/applications/Waf2Py/status/reload'
            subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return self.response

    def Start(self):
        self.start = subprocess.Popen(['sudo', '/opt/waf/nginx/sbin/nginx'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.ok,self.nok = self.start.communicate()
        #wait 4 sec
        time.sleep(4)
        #Check if nginx is still running
        self.check2 = subprocess.Popen(['sudo', '/bin/netstat', '-tulpen'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.out2 = self.check2.communicate()
        p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(['grep', 'nginx'], stdin=p1.stdout, stdout=subprocess.PIPE)
        running = p2.communicate()[0]

        for i in self.out2:
            if 'nginx' in i:
                self.response2 = 'Nginx is Running and listening'
            elif 'master process' in running:
                self.response2 = 'Running but not listening'
            else:
                self.response2 = 'Failed, nginx is not running'

        return (self.response2, self.ok)

    def Stop(self):
        subprocess.Popen(['sudo','/opt/waf/nginx/sbin/nginx', '-s', 'stop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #Wait 4 seconds until nginx is stoped
        time.sleep(4)
        self.check3 = subprocess.Popen(['sudo','/bin/netstat', '-tulpen'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.out3 = self.check3.communicate()
        for i in self.out3:
            if 'nginx' in i:
                self.response3 = 'I could not stop Nginx'
                break
            else:
                self.response3 = 'Nginx Stopped'

        return self.response3


class CreateFiles:
    def __init__(self):
        pass

    def CreateNginxFiles(self, NginxAvailable, AppName, Data):
        #Data = query1[0]['nginx_data_conf']

        try:

            # Create Nginx block Server
            a = open(NginxAvailable + str(AppName) + '_nginx' + '.conf', 'w+')
            a.write(Data)
            a.close()
            self.message = 'OK'
        except Exception as e:
            self.message = 'Error: ' + e

        return self.message

    def CreateNginxSymlink(self, NginxAvailable, AppName, TmpOrProd):

        if TmpOrProd == 'tmp':
            dst = '/opt/waf/nginx/etc/tmp/sites-enabled/'
        elif TmpOrProd == 'prod':
            dst = '/opt/waf/nginx/etc/sites-enabled/'

        try:

            # Create symlink from sites available to site enabled

            os.system('ln -sf ' + NginxAvailable + str(AppName) + '_nginx' + '.conf ' + dst  )
            self.message = 'OK'

        except Exception as e:
            self.message = 'Error: ' + e

        return self.message

    def CreateModsecConf(self, TmpOrProd, appname, data):
        #temporal will be deleted in next release...
        if TmpOrProd == 'tmp':
            try:
                # Create Modsecurity conf
                a = open('/opt/waf/nginx/etc/tmp/modsecurity_conf/' + str(appname) + '_modsec' + '.conf', 'w+')
                a.write(data)
                a.close()
                self.message = 'Ok'

            except Exception as e:
                self.message = 'Error: ' + e

        elif TmpOrProd == 'prod':
            try:
                # Create Modsecurity conf
                a = open('/opt/waf/nginx/etc/modsecurity_conf/' + str(appname) + '_modsec' + '.conf', 'w+')
                a.write(data)
                a.close()
                self.message = 'Ok'

            except Exception as e:
                self.message = 'Error: ' + e

        return self.message

    def CreateModsecFiles(self, PathRules, AppName, PathModConf, Data):
        # create app folder in modsecurity tmp directory
        try:

            os.mkdir(PathRules + str(AppName))
            os.mkdir(PathRules + str(AppName) + '/enabled_rules')
            os.mkdir(PathRules + str(AppName) + '/base_rules')

            # Copy core set rules to modsec tmp
            os.system('cp /opt/waf/nginx/etc/crs/owasp-modsecurity-crs/rules/* ' + PathRules + str(AppName) + '/base_rules/')

            # Copy setup.conf of ruleset to modsec tmp
            os.system('cp /opt/waf/nginx/etc/crs/owasp-modsecurity-crs/crs-setup.conf ' + PathRules + str(AppName)+'/')

            # Create Modsecurity app conf
            a = open(PathModConf + str(AppName) + '_modsec' + '.conf', 'w+')
            a.write(Data)
            a.close()

            self.message = 'OK'

        except Exception as e:
            self.message = 'Error: ' + str(e)

        return self.message

    def CreateSymlinksRules(self, PathRules, AppName):

        # Create symlinks from base_rules to enabled rules
        try:
            os.system('ls ' + PathRules + str(AppName) + '/base_rules/ | while read i; do ln -sf '
                      + PathRules + str(AppName) + '/base_rules/$i ' + PathRules + str(AppName)
                      + '/enabled_rules/;done')
            self.message = 'OK'

        except Exception as e:
            self.message = 'Error: ' + e

        return self.message

    def CreateBackend(self, TmpOrProd, AppName, IpPool, vhost_id, max_fails, fail_timeout, plbsid_id, proto):
        #custom_id = random.randint(0, 999999)

        if TmpOrProd == 'prod':
            try:
                # Create backend conf

                f = open('/opt/waf/nginx/etc/backend/%s.conf' %(AppName), 'a')
                f.writelines('upstream backend_%s_%s%s {\n' %(vhost_id, str(plbsid_id), proto))
                for ip in IpPool:
                    if ip != "":
                        
                        f.writelines('    server %s max_fails=%s fail_timeout=%s;' %(ip, str(max_fails), str(fail_timeout)))
                        f.writelines('\n')

                    else:
                        pass
                f.writelines('}\n')
                f.close()
                self.message = 'Backend Saved'
            except Exception as e:
                self.message = 'Error: ' + str(e)
        else:
            self.message = 'Invalid characters found'
        return self.message

class Maintenance:
    
    def __init__(self):
        pass
    
    def LogRotationFile(self, app_name):
        self.app_name = app_name
        logs_files = "/opt/waf/nginx/var/log/"+self.app_name+"/*.log {\n\
        create 0644 www-data www-data\n\
        daily\n\
        rotate 10\n\
        missingok\n\
        notifempty\n\
        compress\n\
        sharedscripts\n\
        postrotate\n\
        /bin/kill -USR1 `cat /opt/waf/nginx/var/run/nginx.pid 2>/dev/null` 2>/dev/null || true\n\
        endscript\n\
        chown -R www-data.www-data /opt/waf/nginx/var/log/"+self.app_name+"/ || true\n\
        }"
        
        #Create rotation logs for every app.
        f = open('/home/www-data/waf2py_community/applications/Waf2Py/logrotation.d/%s.conf' %(self.app_name),'w') 
        f.write(logs_files)
        f.close()
        os.system('sudo chown root.root /home/www-data/waf2py_community/applications/Waf2Py/logrotation.d/*')
        return 'ok'
