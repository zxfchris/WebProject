from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.spiders import CrawlSpider, Rule
from crawlernologin.items import LinkItem
from scrapy.http import Request
import parameter

class Example1Spider(CrawlSpider):
    name = 'example.com1'
    start_urls = parameter.login_urls
    startCrawlingURL = parameter.start_urls
    allowed_dommains= parameter.domain
    login_user = parameter.username
    login_pass = parameter.password
    originUrl = dict()
    # 'log' and 'pwd' are names of the username and password fields
    # depends on each website, you'll have to change those fields properly
    # one may use loginform lib https://github.com/scrapy/loginform to make it easier
    # when handling multiple credentials from multiple sites.
    def start_requests(self):
        print '**********************************'
        print self.startCrawlingURL[0]
        print '**********************************'
	return [Request(url=self.startCrawlingURL[0],method='get', dont_filter=True,callback=self.parse)]

    def parseJavascript(self, response):
        print 'originUrl:'
        # print response.body
        lines = response.body.split('\n')

        for line in lines:
            if line.find('open') > -1 and (line.find('?') > -1):
                ####found possible injection point
                print 'line: ', line
                print self.originUrl[response.url]

                content = line[line.find('(')+1:line.find(')')]
                content = content.replace('\"+', '')
                content = content.replace('+\"', '')
                content = content.replace('\"', '')
                print content
                strs = content.split(',')
                print strs
                method = ''
                params = []
                action = ''
                for str in strs:
                    print str
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

        # print 'url:', response.url

    def parse(self, response):
        # print response.url
        # print response.body
        """ Scrape useful stuff from page, and spawn new requests
        """
        print 'in parse function'
        hxs = HtmlXPathSelector(response)
        # i = CrawlerItem()
        # find all the link in the <a href> tag

        links = hxs.xpath('//a/@href').extract()
        js_links = hxs.xpath('//script/@src').extract()
        self.extract_forms(hxs, response)

        for link in js_links:
            print link
            # pattern = re.compile(r'javascript:void(0)')
            # match = re.match(pattern, link)
            # print match
            # if match:
            #     continue

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
                if link.find(parameter.domain[0]) > -1:
                    # print link
                    yield Request(url=link)
                else:
                    continue

            elif len(link) > 0 and link[0] == '#':
                direct = response.url.split('/')
                if (len(link) > 1 and link[1] == '/') or len(link) == 1:
                    # print response.url+link[1:]
                    yield Request(url=response.url + link[1:], callback=self.parseJavascript)
                    js_url = response.url + link[1:]
                else:
                    if response.url[-1:] != '/':
                        # print response.url+'/'+link[1:]
                        js_url = response.url + '/' + link[1:]
                        yield Request(url=response.url + '/' + link[1:], callback=self.parseJavascript)
                    else:
                        # print response.url+link[1:]
                        js_url = response.url + link[1:]
                        yield Request(url=response.url + link[1:], callback=self.parseJavascript)

            else:
                if (len(link) > 0 and link[0] != '/') or len(link) == 0:
                    if response.url[-1:] != '/':
                        js_url = response.url + '/' + link
                        print 'js_url:', js_url
                        self.originUrl[js_url] = response.url
                        yield Request(url=js_url, callback=self.parseJavascript)
                    else:
                        js_url = response.url + link
                        print 'js_url:', js_url
                        yield Request(url=js_url, callback=self.parseJavascript)
                else:
                    print parameter.domain[0]+link
                    js_url = parameter.domain[0] + link
                    yield Request(url=parameter.domain[0] + link, callback=self.parseJavascript)

            if len(params)>0:
                formsfile = open('formslist', 'a')
                formsfile.write("<form action='" + js_url + "' method='get'> ")
                for param in params:
                    global input
                    name, value = param.split('=')
                    formsfile.write("<input type='text' name='"+name+"' value='"+value+"'/>")
                formsfile.write("</form>")
                formsfile.write('\n')
                linksfile = open('linkslist', 'a')
                linksfile.write(response.url)
                linksfile.write('\n')
                formsfile.close()
                linksfile.close()

        # Yield a new request for each link we found
        # #this may lead to infinite crawling...
        #print response.headers['Location']
        for link in links:

            print "THIS IS A LINK: " + link
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
                print 'linkelse'
                if (len(link)>0 and link[0]!='/') or len(link)==0:
                    direct=response.url.split('/')
                    path=''
                    for i in range(len(direct)-1):
                        path=path+direct[i]+'/'
                    print path+link
                    yield Request(url=path+link)
                else:
                    print 'printnewlink', parameter.domain[0]+link
                    yield Request(url=parameter.domain[0]+link)
        item = LinkItem()
        if len(hxs.xpath('//title/text()').extract())>0:
            item["title"] = hxs.xpath('//title/text()').extract()[0]
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
