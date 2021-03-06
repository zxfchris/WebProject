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
        # print 'datalength'
        # print len(data)
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
                            # print '!!!!!formLength'
                            # print len(ssciForm.formdata["parameter"])
                            parameters = ssciForm.formdata["parameter"]
                            for name in parameters.keys():
                                # print 'name1:', name
                                # print 'value:', parameters[name]
                                valid_parameters = dict(ssciForm.fill_entries(payload=evalData[item], paramkey=name))
                                # print 'parameters!!!'
                                # print valid_parameters
                                try:
                                    newParam = ''
                                    r = client.get(action, params=urlencode(valid_parameters))

                                    if r != None:
                                        if r.status_code == 200:
                                            # print r.content
                                            # print r.url
                                            injectSuccess = False
                                            if item == 'LFI1':
                                                if "root:/bin/bash" in r.content \
                                                        or 'root:/bin/sh' in r.content:
                                                    print "injection success1!"
                                                    injectSuccess = True
                                            elif item == 'LFI2' or item == 'LFI3' or item == 'LFI4':
                                                if "PHP Version" in r.content \
                                                        and 'HTTP Headers Information' in r.content:
                                                    print "injection success2!"
                                                    print 'LFI, show phpinfo'
                                                    injectSuccess = True
                                                    # print r.content
                                            elif item == 'RFI1' or item == 'RFI2' or item == 'RFI3':
                                                print 'RFI, show phpinfo'
                                                if "PHP Version" in r.content\
                                                        and 'HTTP Headers Information' in r.content:
                                                    print "injection success3!"
                                                    print 'RFI, show phpinfo'
                                                    injectSuccess = True
                                            elif item == 'PHP1' or item == 'PHP2':
                                                print 'PHP, show phpinfo'
                                                if "PHP Version" in r.content\
                                                        and 'HTTP Headers Information' in r.content:
                                                    print "injection success4!"
                                                    print 'PHP, show phpinfo'
                                                    injectSuccess = True
                                            elif item == 'PHP3' or item == 'PHP4':
                                                print 'PHP, show special string'
                                                # if "afadsfaefasdfafezdfa" in r.content \
                                                #         and "echo" not in r.content:
                                                        # and "echo \"afadsfaefasdfafezdfa\"" not in r.content\
                                                        # and "echo%20%22afadsfaefasdfafezdfa%22" not in r.content:
                                                start = r.content.find('afadsfaefasdfafezdfa')
                                                if start > -1:
                                                    if "echo" not in r.content[start - 20:start]:
                                                        print "injection success5!"
                                                        print 'PHP, show special string'
                                                        injectSuccess = True
                                            elif item == 'PHP5' or item == 'PHP6':
                                                print 'PHP, injection command'
                                                if "root:/bin/bash" in r.content \
                                                        or 'root:/bin/sh' in r.content:
                                                    print "injection success6!"
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
                                except:
                                    ''

                # elif formDetails["method"].lower() == "post":# form is a post form, check for CSRF
                #     ssciForm = Form(url,formDetails)
                #     #we send a request with randomly filled in token
                #     valid_parameters = dict(ssciForm.fill_entries())
                #
                #     try:
                #         newParam = ''
                #         r = client.post(action, params=urlencode(valid_parameters))
                #
                #         if r != None:
                #             if r.status_code == 200:
                #                 # print r.content
                #                 # print r.url
                #                 injectSuccess = False
                #                 if item == 'LFI1':
                #                     if "root:x:0:0:root:/root:/bin/bash" in r.content:
                #                         print "injection success1!"
                #                         injectSuccess = True
                #                 elif item == 'LFI2' or item == 'LFI3' or item == 'LFI4':
                #                     if "PHP Version" in r.content \
                #                             and 'HTTP Headers Information' in r.content:
                #                         print "injection success2!"
                #                         print 'LFI, show phpinfo'
                #                         injectSuccess = True
                #                         # print r.content
                #                 elif item == 'RFI1' or item == 'RFI2' or item == 'RFI3':
                #                     print 'RFI, show phpinfo'
                #                     if "PHP Version" in r.content\
                #                             and 'HTTP Headers Information' in r.content:
                #                         print "injection success3!"
                #                         print 'RFI, show phpinfo'
                #                         injectSuccess = True
                #                 elif item == 'PHP1' or item == 'PHP2':
                #                     print 'PHP, show phpinfo'
                #                     if "PHP Version" in r.content\
                #                             and 'HTTP Headers Information' in r.content:
                #                         print "injection success4!"
                #                         print 'PHP, show phpinfo'
                #                         injectSuccess = True
                #                 elif item == 'PHP3' or item == 'PHP4':
                #                     print 'PHP, show special string'
                #                     if "afadsfaefasdfafezdfa" in r.content \
                #                             and "echo \"afadsfaefasdfafezdfa\"" not in r.content:
                #                             #                                                      \
                #                             # and "echo%20%22afadsfaefasdfafezdfa%22" not in r.content:
                #                         print "injection success5!"
                #                         print 'PHP, show special string'
                #                         injectSuccess = True
                #                 elif item == 'PHP5' or item == 'PHP6':
                #                     print 'PHP, injection command'
                #                     if "root:x:0:0:root:/root:/bin/bash" in r.content:
                #                         print "injection success6!"
                #                         injectSuccess = True
                #                 #formDetails["url"] = url
                #                 if injectSuccess == True:
                #                     confirmForm = copy.deepcopy(formDetails)
                #                     confirmForm["parameter"] = copy.deepcopy(valid_parameters)
                #                     # formDetails["parameter"] = valid_parameters
                #                     if len(valid_parameters) != 0:
                #                         jsonform.append(confirmForm)
                #                 #pprint("post form "+ssciForm.formdata["action"] +  " is vulnerable to CSRF")
                #             else:
                #                 print "status code", r.status_code
                #
                #         continue
                #     except :
                        ''
                        #pprint('response is null')
with open("../output/phase3_output.json",'w') as outfile:
    json.dump(jsonform,outfile, indent=2)
