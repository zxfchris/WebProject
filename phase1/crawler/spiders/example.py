from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.spiders import CrawlSpider
from crawler.items import LinkItem
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy import log
import parameter
import re
from loginform import fill_login_form

class ExampleSpider(CrawlSpider):
    #handle_httpstatus_list = [404]
    name = 'example.com'
    start_urls = parameter.login_urls
    startCrawlingURL = parameter.start_urls
    allowed_dommains= parameter.domain
    login_user = parameter.username
    login_pass = parameter.password
    originUrl = dict()
    #cookie= Cookie.SimpleCookie()
    #rules = (Rule(LinkExtractor(deny=('logout\.php', ))),)
    # 'log' and 'pwd' are names of the username and password fields
    # depends on each website, you'll have to change those fields properly
    # one may use loginform lib https://github.com/scrapy/loginform to make it easier
    # when handling multiple credentials from multiple sites.
    def start_requests(self):
        print '----------------------------------'
        print self.startCrawlingURL[0]
        print '----------------------------------'
        if parameter.login==True:
            return [Request(url=self.start_urls[0],method='get', dont_filter=True,callback=self.login)]
        else:
            return [Request(url=self.startCrawlingURL[0],method='get', dont_filter=True,callback=self.parse)]
    def login(self,response):
            
            args, url, method = fill_login_form(response.url, response.body, self.login_user, self.login_pass)
            print args,url,method
            #print args
            argsdict={}
            for i in args:
                argsdict[i[0]]=i[1]
            #print argsdict
            return FormRequest(url,formdata=args, dont_filter=True,callback=self.after_login)

    def after_login(self, response):
        # check login succeed before going on
        #print response.body
        if "No match"  in response.body:
            self.log("Login fail", level=log.ERROR)
            return []


        # continue scraping with authenticated session...
        else:
            self.log("Login succeed!", level=log.DEBUG)
            #print response.body
            return Request(url=response.url)
            
            #return Request(url="https://app1.com/cart/review.php",
            #               callback=self.parse)


    def parseJavascript(self, response):
        print 'crawler parseJavascript:', response.url
        # print response.body
        lines = response.body.split('\n')

        for line in lines:
            if line.find('open') > -1 and (line.find('?') > -1):
                ####found possible injection point
                # print 'line: ', line

                # print self.originUrl[response.url]

                content = line[line.find('(')+1:line.find(')')]
                content = content.replace('\"+', '')
                content = content.replace('+\"', '')
                content = content.replace('\"', '')
                # print content
                strs = content.split(',')
                # print strs
                method = ''
                params = []
                action = ''
                for str in strs:
                    # print str
                    if str.lower() == 'get':
                        method = 'get'
                    elif str.lower() == 'post':
                        method = 'post'
                    elif str.find('?'):
                        if self.originUrl[response.url][-1] == '/':
                            action = self.originUrl[response.url] + str.strip()[:str.strip().find('?')]
                        else:
                            action = self.originUrl[response.url] + '/' + str.strip()[:str.strip().find('?')]
                        parastr = str[str.find('?')+1:]
                        params = parastr.split('&')
                        print params
                if method == 'get':
                    formsfile = open('formslist', 'a')
                    formsfile.write("<form action='" + action + "' method='get'> ")
                    for param in params:
                        name, value = param.split('=')
                        formsfile.write("<input type='hidden' name='"+name+"' value='"+value+"'/>")
                    formsfile.write("</form>")
                    formsfile.write('\n')
                    linksfile = open('linkslist', 'a')
                    linksfile.write(self.originUrl[response.url])
                    linksfile.write('\n')
                    formsfile.close()
                    linksfile.close()

    def parse(self, response):
        """ Scrape useful stuff from page, and spawn new requests
        """

        hxs = HtmlXPathSelector(response)
        links = hxs.xpath('//a/@href').extract()
        self.extract_forms(hxs, response)
        js_links = hxs.xpath('//script/@src').extract()

        # print '!!!!!!!links!!!!!!'
        # print links

        for link in js_links:
            pattern = re.compile(r'javascript:void(0)')
            match = re.match(pattern, link)
            print match
            if match:
                continue

            print "src ur1: "+link
            link = link.split('?')
            params = []
            if len(link) > 1:
                param_url = link[1]
                params = param_url.split('&')

            link = link[0]
            js_url = link

            if link.find("logout") > -1:
                continue
            if link.find("http") > -1:
                if link.find(parameter.domain[0]) <= -1:
                    continue

            elif len(link) > 0 and link[0] == '#':
                if (len(link) > 1 and link[1] == '/') or len(link) == 1:
                    js_url = response.url + link[1:]
                else:
                    if response.url[-1:] != '/':
                        js_url = response.url + '/' + link[1:]
                    else:
                        js_url = response.url + link[1:]

            else:
                if (len(link) > 0 and link[0] != '/') or len(link) == 0:
                    direct = response.url.split('/')
                    path = ''
                    for i in range(len(direct) - 1):
                        path = path + direct[i] + '/'
                    if path.find(parameter.domain[0]) > -1:
                        js_url = path + link
                    else:
                        js_url = response.url + '/' + link
                else:
                    js_url = parameter.domain[0] + link

            if len(params)>0:
                formsfile = open('formslist', 'a')
                formsfile.write("<form action='" + js_url + "' method='get'> ")
                for param in params:
                    value = ''
                    kvpair = param.split('=')
                    if len(kvpair) > 1:
                        value = kvpair[1]
                    name = kvpair[0]
                    formsfile.write("<input type='hidden' name='"+name+"' value='"+value+"'/>")
                formsfile.write("</form>")
                formsfile.write('\n')
                linksfile = open('linkslist', 'a')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()
            self.originUrl[js_url] = response.url
            yield Request(url=js_url, callback=self.parseJavascript)

        for link in links:
            print link
            if link.find('status.php?op=del&status_id=')>-1:
                ip=link.split('status.php?op=del&status_id=')[1]
                delform="<form action='status.php'> <input name='op' type='hidden' value='del'/><input name='status_id' type='hidden' value='"+id+"'/></form>"
                formsfile=open('formslist','a')
                linksfile=open('linkslist','a')
                formsfile.write(form)
                formsfile.write('\n')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()
                continue
            elif link.find('resolution.php?op=del&resolution_id=')>-1:
                ip=link.split('resolution.php?op=del&resolution_id=')[1]
                delform="<form action='resolution.php'> <input name='op' type='hidden' value='del'/><input name='resolution_id' type='hidden' value='"+id+"'/></form>"
                formsfile=open('formslist','a')
                linksfile=open('linkslist','a')
                formsfile.write(form)
                formsfile.write('\n')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()
                continue
            elif link.find('severity.php?op=del&severity_id=')>-1:
                ip=link.split('severity.php?op=del&severity_id=')[1]
                delform="<form action='severity.php'> <input name='op' type='hidden' value='del'/><input name='severity_id' type='hidden' value='"+id+"'/></form>"
                formsfile=open('formslist','a')
                linksfile=open('linkslist','a')
                formsfile.write(form)
                formsfile.write('\n')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()
                continue
            elif link.find('os.php?op=del&os_id=')>-1:
                ip=link.split('os.php?op=del&os_id=')[1]
                delform="<form action='os.php'> <input name='op' type='hidden' value='del'/><input name='os_id' type='hidden' value='"+id+"'/></form>"
                formsfile=open('formslist','a')
                linksfile=open('linkslist','a')
                formsfile.write(form)
                formsfile.write('\n')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()
                continue
            #print "THIS IS A LINK" + link
            #only process external/full link
#            cookie.load(response.headers['Set-Cookie'])
            if link.find("logout") >-1 :
                continue
            if link.find("http") > -1:
                if link.find(parameter.domain[0])>-1:
                    #print link
                    yield Request(url=link)
                else:
                    continue

            elif len(link)>0 and link[0]=='#':
                direct=response.url.split('/')
                if  (len(link)>1 and link[1]=='/') or len(link)==1:
                    #print response.url+link[1:]
                    yield Request(url=response.url+link[1:])
                else:
                    if response.url[-1:]!='/':
                        #print response.url+'/'+link[1:]
                        yield Request(url=response.url+'/'+link[1:])
                    else:
                        #print response.url+link[1:]
                        yield Request(url=response.url+link[1:])

            else:
                if (len(link)>0 and link[0]!='/') or len(link)==0:
                    direct=response.url.split('/')
                    path=''
                    for i in range(len(direct)-1):
                        path=path+direct[i]+'/'
                    #print path+link
                    yield Request(url=path+link)
                else:
                    #print parameter.domain[0]+link
                    yield Request(url=parameter.domain[0]+link)
        item = LinkItem()
        #if len(hxs.xpath('//title/text()').extract())>0:
        item["title"] = hxs.xpath('//title/text()').extract()[0]
        item["url"] = response.url
        yield self.collect_item(item)

        item = LinkItem()
        if len(hxs.xpath('//title/text()').extract())>0:
            item["title"] = hxs.xpath('//title/text()').extract()[0]
        else:
            item["title"] = hxs.xpath('//title/text()').extract()
        item["url"] = response.url
        yield self.collect_item(item)

    def collect_item(self, item):
        return item

    def extract_forms(self,hxs,response):
        forms = hxs.xpath('//form').extract()
        formsfile=open('formslist','a')
        linksfile=open('linkslist','a')
        for form in forms:
            form = form.encode('utf-8').strip()
            linksfile.write(str(response)[5:-1])
            linksfile.write('\n')
            formsfile.write(form)
            formsfile.write('\n')
        formsfile.close()
        linksfile.close()
