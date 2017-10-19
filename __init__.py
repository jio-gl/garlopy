#!/bin/python                                                                                                                               
# -*- coding: utf-8 -*-

# standard imports
import re
import urllib2
import random
import unittest

from collections import Counter

# project-native imports
from BeautifulSoup import BeautifulSoup


class GarlopyException(Exception):
    pass

class GarlopyNoneDOMException(GarlopyException):
    pass

class GarlopyNodeNotFoundException(GarlopyException):
    pass

class GarlopyAmbiguousScrapeException(GarlopyException):
    pass

class GarlopyMultibranchLimitException(GarlopyException):
    pass

class GarlopyNoContentsException(GarlopyException):
    pass


class GarlopyXPath(object):
    
    def __init__(self, xpath, replacements, is_multistring=False, multistring_index=None):
        self.xpath = xpath
        self.replacements = replacements
        self.is_multistring = is_multistring
        self.multistring_index = multistring_index 
        
    def preprocess_html(self, html_str):        
        for original,new in self.replacements:
            if 'view view-sfj-event-heroimages view-id-sfj_event_heroimages ' in original:
                pass
            for finding in re.findall(original,html_str):
                html_str = html_str.replace(finding,new)            
        return html_str
    
    def __repr__(self):
        return str(self.xpath) #+ ' ' + str(self.replacements)


class GarlopyScraper(object):

    _xpath_dic = {}
    _default_encoding = 'utf-8'
    __MULTIBRANCH_LIMIT = 10
    __NUMERIC_LEN_REMOVAL_MINIMUM = 1
    
    def __init__(self, encoding=None, multibranch=False):

        if encoding:
            self._default_encoding = encoding
            
        self.multibranch = multibranch 
            

    def train(self, url, data):
        
        response = urllib2.urlopen(url)
        html = response.read()
        
        # DEBUG:
        #html = '''
        #    <html> <a id="node-1234">Juan Pedro</a></html>
        #'''
        #data = {'name' : 'Juan Pedro'}
        
        
        self.train_html(html, data)


    def scrape_html(self,html):

        results = {}
        
        # remove comments
        comments = re.findall('<!--.*-->',html)
        for comm in comments:
            html = html.replace(comm,'')
        
        for k, val in self._xpath_dic.iteritems():
            
            for gxpath in val:

                try:
                    processed_html = gxpath.preprocess_html( html )
                    soup = BeautifulSoup(processed_html.encode(self._default_encoding))
                    xpath = gxpath.xpath.encode( 'ascii' )   
                    if 'sfj-page-title' in xpath:
                        pass         
                    print len(xpath.split('/')),len(xpath),xpath
                    self.garlopy_xpath = gxpath
                    found = self._rec_find(soup, xpath)
                    if not k in results:
                        results[k] = []
                    results[k].append( found ) 
                    if len( list(set(found)) ) == 1:
                        results[k] = list(set(found)) #found[0]
                        print 'FOUND!!! WITH ' + xpath 
                        break
                except GarlopyNoneDOMException, e:
                    continue
                except GarlopyNodeNotFoundException, e:      
                    continue
                except GarlopyMultibranchLimitException, e:
                    continue
            
            if not k in results:
                open('scrape.html','w').write(html)
                raise GarlopyException('cannot scrape "%s" with the following xpaths: %s replacements -> %s ' % (k,str([x.xpath for x in val ]),str([x.replacements for x in val ]) ) )
            
            if k in results and not isinstance(results[k][0], basestring):
                res = []
                for l in results[k]:
                    res += l  
                results[k] = res
            #    raise GarlopyAmbiguousScrapeException('ambiguous scrape "%s" with the following xpaths: %s replacements -> %s : ambiguity -> %s' % (k,str([x.xpath for x in val ]),str([x.replacements for x in val ]) , str(results[k])) )
            
        return results
        

    def scrape(self, url):

        response = urllib2.urlopen(url)
        html = response.read()

        return self.scrape_html(html)
     

    def train_html(self, html, data):
        
        soup = BeautifulSoup(html.encode(self._default_encoding))
        
        for k,val in data.iteritems():

            xpaths = self._train_s_one(soup, k, val)
            
            if not xpaths:
                open('out.html','w').write(html)                
                raise GarlopyException('cannot found XPath for: ' + str(val))  
                          
            else:
                self._xpath_dic[k] = xpaths
        
        print self._xpath_dic
        
        #for k,v in self._xpath_dic.iteritems():
        #        print k,v
                
    
    def _sanitize_identifier(self,tid):
        
        if 'primary-links' in tid:
            pass
        
        final = tid
        
        hexas = []
        all_hexa_apps = re.findall('[0-9a-f]*[a-f]+[0-9]+[a-f]+[0-9]+[0-9a-f]*',final)        
        for app in all_hexa_apps:
            if len(app) > 4:
                tid = tid.replace(app,'[0-9a-f]*[a-f]+[0-9]+[a-f]+[0-9]+[0-9a-f]*')
                final = final.replace(app,'')
                
        # numbers < 99
        c_num = 0
        all_num_apps = re.findall('[0-9]+',final)        
        for app in all_num_apps:
            if len(app) > self.__NUMERIC_LEN_REMOVAL_MINIMUM:
                tid = tid.replace(app,'###NUMERIC-%s-GARLOPY###' % ('X'*c_num))
                c_num += 1
                final = final.replace(app,'')
#                final = final.replace(app,'')
        for i_num in range(c_num):
            tid = tid.replace('###NUMERIC-%s-GARLOPY###' % ('X'*i_num),'[0-9]+')
                
        return tid, final

    def _train_s_one(self, soup, k, val):

        fs = soup.findAll( text=re.compile(re.escape(unicode(val)))) #.encode(self._default_encoding)) )

        if len(fs) == 0:
            return None
        
        # TODO: support multipe things...
        #fs = fs[:1]

        replacements = []        
        xpaths = []
        for f in fs:
            
            f_string = f.string
    
            xpath = []
            is_multistring = False
            multistring_index = None
    
            while f.parent.name != 'html':
    
                #print f.parent.name
    
                try:
                    tid = f.parent['id']
                except:
                    tid = None
    
                try:
                    tclass = f.parent['class']
                except:
                    tclass = None
    
                elem = f.parent.name
                if elem in ['html','body','head']:
                    tid = None
                    tclass = None
                    
                if tid:
                    old_tid = tid
                    tid,new_tid = self._sanitize_identifier(tid)
                    if tid != old_tid:
                        replacements += [('id="%s"'%tid,'id="%s"'%new_tid), ("id='%s'"%tid,"id='%s'"%new_tid)]
                    elem += '#' + new_tid
                if tclass:
                    old_tclass = tclass
                    tclass,new_tclass = self._sanitize_identifier(tclass)
                    if tclass != old_tclass:
                        replacements += [('class="%s"'%tclass,'class="%s"'%new_tclass), ("class='%s'"%tclass,"class='%s'"%new_tclass)]
                    elem += '.' + new_tclass
                
                print dir(f.parent)
                print '-'*80
                print str(f.parent)
                print '-'*80
                print str(f.parent.strings)
                
                if xpath == []:
                    #parent_soup = BeautifulSoup(str(f.parent))
                    par_conts = f.parent.contents
                    if len(par_conts) > 1:
                        is_multistring = True
                        multistring_index = [i for i in range(len(f.parent.contents)) if val in str(f.parent.contents[i]) ][0] 
                    
                xpath.append( elem )
                f = f.parent
    
            try:
                    tid = f.parent['id']
            except:
                    tid = None
    
            try:
                    tclass = f.parent['class']
            except:
                    tclass = None
    
            elem = f.parent.name

            if elem in ['html','body','head']:
                tid = None
                tclass = None

            if tid:
                old_tid = tid
                tid,new_tid = self._sanitize_identifier(tid)
                if tid != old_tid:
                    replacements += [('id="%s"'%tid,'id="%s"'%new_tid), ("id='%s'"%tid,"id='%s'"%new_tid)]
                elem += '#' + tid
            if tclass:
                old_tclass = tclass
                tclass,new_tclass = self._sanitize_identifier(tclass)
                if tclass != old_tclass:
                    replacements += [('class="%s"'%tclass,'class="%s"'%new_tclass), ("class='%s'"%tclass,"class='%s'"%new_tclass)]
                elem += '.' + tclass

            xpath.append( elem )
    
            xpath.reverse()
            
            xpath = '/%s' % '/'.join( xpath )
            
            #return xpath
            
            gxpath = GarlopyXPath(xpath,replacements,is_multistring,multistring_index)
            xpaths.append( (f_string, gxpath) )

        len_xpath = [(len(val)-len(f_string), -len(gxpath.xpath.split('/')),gxpath) for f_string, gxpath in xpaths ]
        # TODO: continue introducing GarlopyXPath Instead of plain xpath
        len_xpath.sort(reverse=True)
        
        return  [ xpath_tuple[2] for xpath_tuple in  len_xpath ] # len_xpath[0][2] 


    def _rec_find( self, elem, path ):
    
        # TODO: learn on training if the string is on a multiple content tag
        #       when here appears len(path) == 0
    
        #print str(elem)[:-2]
        print '='*80
        
        print 'PATH: ' + path
        print 'ELEM: ' + str(elem)
        
        #print 'CONTENTS ELEM:' + str(elem.contents)
        #print dir(elem)
        print '-'*80
        
        if path.startswith('div.view view-sfj-event-heroimages view-id-sfj_event_heroimages'):
            pass
            
        if elem == None:
            raise GarlopyNoneDOMException('None elem in recursive traversal of DOM with _rec_find().')
            
        # OJO: If a tag contains more than one thing, then it’s not clear
        # what .string should refer to, so .string is defined to be None
        if elem.string:
            return elem.string
    
        #if len(path) == 0 and len(elem.stripped_strings) > 0:
        # ble    
    
        if len(path) == 0:
            conts = elem.contents
            if len( elem.contents ) == 1 or not self.garlopy_xpath.is_multistring:      
                return str(elem.contents[0])
            elif len( elem.contents ) > 1 and self.garlopy_xpath.is_multistring:
                return str(elem.contents[self.garlopy_xpath.multistring_index])
            else:
                raise GarlopyNoContentsException('no contents on elem -> %s' % str(elem) )
         
        if path[0] == '/':
            path = path[1:] # remove '/'
        name = path.split('/')[0]
    
        #print name
    
        has_numeral = '#' in name
        generic_sep = '@'
        name = name.replace('#',generic_sep).replace('.',generic_sep)
        tag_id,tag_class = None,None
        if len(name.split(generic_sep)) > 1:
            if not has_numeral:
                tag_class = name.split(generic_sep)[-1]
            else:
                tag_id = name.split(generic_sep)[-1]
                
        if len(name.split(generic_sep)) > 2:
            tag_id = name.split(generic_sep)[1]
        name = name.split(generic_sep)[0]
    
        path = '/'.join( path.split('/')[1:] )
    
        if name in ['html','body','head']:
            tag_id = None
            tag_class = None
    
        tag_attrs = {}
        if tag_id:
            tag_attrs['id'] = tag_id
        if tag_class:
            tag_attrs['class'] = tag_class

        # single DOM branch
        #elem = elem.find(name, attrs=tag_attrs)
        #return self._rec_find( elem, path )

        # multiple DOM branches ...        
        elems = elem.findAll(name, attrs=tag_attrs)

        if len(elems) > self.__MULTIBRANCH_LIMIT:
            raise GarlopyMultibranchLimitException('Too many branches with _rec_find(), limit is %d' % self.__MULTIBRANCH_LIMIT)
    
        if 'class' in tag_attrs and tag_attrs['class'] == 'sfj-page-title':
            pass
    
        ret = []
        if not self.multibranch and len(elems) > 1:
            len_elems = [(len(str(elem)),elem) for elem in elems]
            len_elems.sort()
            len_elems.reverse()
            elems = [len_elems[0][1]]
        for elem in elems:
            try:
                found = self._rec_find( elem, path )
                if not isinstance(found, basestring) :
                    ret += found#[(len(found),found)]
                else:
                    ret += [found]
            except GarlopyNoneDOMException, e:                
                pass
            except GarlopyNodeNotFoundException, e:                
                pass
        ret.sort()
        ret.reverse()
        if len(ret) == 0:
            raise GarlopyNodeNotFoundException()
        return ret #ret[0][1]

            
class TestGarlopy(unittest.TestCase):

    def setUp(self):
        self.seq = range(10)
        self.s = GarlopyScraper()
        
    def _test_scraper(self,html1,data1,html2,data2):
        
        s = self.s

        s.train_html(html1, data1)
        
        result = s.scrape_html(html2)
        #print result
        data2_scraped = result # result[0]
        
        print data2
        print data2_scraped
        print '+'*80
        #print Counter(data2_scraped['name'])
    
        if 'name' in data2_scraped:
            data2_scraped['name'] = [e.strip() for e in data2_scraped['name'] ]
        if 'venue_name' in data2_scraped:
            data2_scraped['venue_name'] = data2_scraped['venue_name']!=None and [e.strip() for e in data2_scraped['venue_name'] ] or None
        if 'date' in data2_scraped:
            data2_scraped['date'] = [e.strip() for e in data2_scraped['date'] ]

        print '*'*80
        print data2
        print '-'*80
        print data2_scraped
        print '*'*80

        self.assertEqual(data2, data2_scraped)
        

#    def test_basic(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <p>Hector</p>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <p>Jorge</p>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_basic2(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div id="myname">Hector</div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div id="myname">Jorge</div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_basic3(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div class="myclasss">Hector</div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div class="myclasss">Jorge</div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#            
#    def test_basic4(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div class="myclasss" id="myname">Hector</div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div class="myclasss" id="myname">Jorge</div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#            
#    def test_medium(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div><p>Hector</p></div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div><p>Jorge</p></div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_medium2(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div id="myname"><div>Hector</div></div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div id="myname"><div>Jorge</div></div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_medium3(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div class="myclasss"><div>Hector</div></div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div class="myclasss"><div>Jorge</div></div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#            
#    def test_medium4(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#        <div class="myclasss" id="myname"><div>Hector</div></div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#        <div class="myclasss" id="myname"><div>Jorge</div></div>
#        </html>
#        '''
#        data1 = {'name':'Hector'}
#        data2 = {'name':['Jorge']}
#
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_urls1(self):
#
#        url1 = 'http://www.sfsymphony.org/Buy-Tickets/2013-2014/MTT-and-Emanuel-Ax-Beethoven.aspx'
#        data1 = {
#                        'name': 'MTT and Emanuel Ax: Beethoven',
#                        'venue_name': 'Davies Symphony Hall',
#                        'date': 'Thu, Sep 26, 2013 at 8:00pm', #[u'Thu, Sep 26, 2013 at 8:00pm', u'Fri, Sep 27, 2013 at 8:00pm', u'Sat, Sep 28, 2013 at 8:00pm']
#                        # price : MANY PRICES (12), MULTIPLE CLICKS TO ACCESS
#                    }
#        
#        url2 = 'http://www.sfsymphony.org/Buy-Tickets/2013-2014/MTT-conducts-Mahler%E2%80%99s-Ninth-Symphony.aspx'
#        data2 = {
#                        'name': ['MTT conducts Mahler&rsquo;s Ninth Symphony'],
#                        'venue_name': ['Davies Symphony Hall'],
#                        'date': [u'Wed, Sep 18, 2013 at 8:00pm',u'Thu, Sep 19, 2013 at 8:00pm',u'Sat, Sep 21, 2013 at 8:00pm',u'Fri, Sep 20, 2013 at 8:00pm'],
#                        #'description':'By 1909, when Mahler penned his Ninth Symphony, he had tragically lost his four-year-old daughter and learned of the heart ailment that would contribute to his own death two years later. The last symphony he completed, the Ninth is one of the composer’s greatest symphonic and life achievements, a work that secured Mahler’s musical immortality. It was with this music that Michael Tilson Thomas began his storied SFS career in 1974.',
#                }
#        
#        response = urllib2.urlopen(url1)
#        html1 = response.read()
#        response = urllib2.urlopen(url2)
#        html2 = response.read()
#        
#        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_urls2(self):
#
#        url1 = 'http://www.yoshis.com/jazzclub/artist/show/4531'
#        data1 = {
#                        'name': u'Omaha Diner w/ Charlie Hunter, Skerik, Bobby Previt & Steven Bernstein',
#                        'venue_name': "Yoshi's Oakland",
#                        'date': 'November 06, 2014',
#                        #'price': '$25',
#                }
#        url2 = 'http://www.yoshis.com/jazzclub/artist/show/4496'
#        data2 = {
#                        'name': [u'America'],
#                        'venue_name': ["Yoshi's Oakland"],
#                        'date': ['Nov 03-Nov  4, 2014'],
#                        #'price': u'8pm $21 adv, $25 door',
#                }
#                
#        response = urllib2.urlopen(url1)
#        html1 = response.read()
#        response = urllib2.urlopen(url2)
#        html2 = response.read()
#        
#        self._test_scraper(html1, data1, html2, data2)


    def test_urls3(self):

        url1 = 'http://www.sfjazz.org/events/2014-15/jan2/maceo-parker'
        data1 = {
                        #'name': u'Maceo Parker',
                        #'venue_name': "at SFJAZZ Center, Miner Auditorium",
                        #'date': 'Friday, January 2, 7:30pm',
                        'price': '$25',
                }
        url2 = 'http://www.sfjazz.org/events/2014-15/oct31/diego-el-cigala'
        data2 = {
                        #'name': [u'Diego El Cigala'],
                        #'venue_name': ["at SFJAZZ Center, Miner Auditorium"],
                        #'date': ['Friday, October 31, 7:30pm'],
                        'price': [u'$30'],
                }
        response = urllib2.urlopen(url1)
        html1 = response.read()
        response = urllib2.urlopen(url2)
        html2 = response.read()
        
        self._test_scraper(html1, data1, html2, data2)
#
#
#    def test_dynamic_id_erasure(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html> <a id="node-1234">Juan Pedro</a></html>
#        '''
#        html2 = '''
#        <html> <a id="node-3456">Carlos Alberto</a></html>
#        '''
#        data1 = {'name':'Juan Pedro'}
#        data2 = {'name':['Carlos Alberto']}
#
#        self._test_scraper(html1, data1, html2, data2)

    
#    def test_multibranch_scraping(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#<div class="sfj-pagehero-content">
#<div class="sfj-pagehero-title sfj-pagehero-title-switch-none"><h1>Diego El Cigala</h1></div>
#<div class="sfj-pagehero-title sfj-pagehero-title-switch-do-not-none"><h1></h1><p>&nbsp;<br />Diego El Cigala</p>
#</div>
#<div class="sfj-pagehero-subtitle"><h2></h2></div>
#<div class="sfj-pagehero-subtitle"><h3><span class="date-display-single">Friday, October 31, 7:30pm</span><br />at SFJAZ
#Z Center, Miner Auditorium</h3></div>
#<div class="sfj-pagehero-body"></div>
#</div>        
#        </html>
#        '''
#        html2 = '''
#        <html>
#<div class="sfj-pagehero-content">
#<div class="sfj-pagehero-title sfj-pagehero-title-switch-none"><h1>Diego El Cigala</h1></div>
#<div class="sfj-pagehero-title sfj-pagehero-title-switch-do-not-none"><h1></h1><p>&nbsp;<br />Diego El Cigala</p>
#</div>
#<div class="sfj-pagehero-subtitle"><h2></h2></div>
#<div class="sfj-pagehero-subtitle"><h3><span class="date-display-single">Monday, September 10, 7:30pm</span><br />at SFJAZ
#Z Center, Miner Auditorium</h3></div>
#<div class="sfj-pagehero-body"></div>
#</div>        
#        </html>
#        '''
#        data1 = {'name':'Friday, October 31, 7:30pm'}
#        data2 = {'name':['Monday, September 10, 7:30pm']}
#
#        self._test_scraper(html1, data1, html2, data2)




#    def test_multistring_scraping(self):
#        # make sure the shuffled sequence does not lose any elements
#        html1 = '''
#        <html>
#<div class="sfj-pagehero-subtitle"><h3><span class="date-display-single">Friday, October 31, 7:30pm</span><br />at SFJAZZ Center, Miner Auditorium</h3></div>
#        </html>
#        '''
#        html2 = '''
#        <html>
#<div class="sfj-pagehero-subtitle"><h3><span class="date-display-single">Friday, October 31, 7:30pm</span><br />at SFJAZZ Center, Super Auditorium</h3></div>
#        </html>
#        '''
#        data1 = {'name':'at SFJAZZ Center, Miner Auditorium'}
#        data2 = {'name':['at SFJAZZ Center, Super Auditorium']}
#
#        self._test_scraper(html1, data1, html2, data2)

            

if __name__ == '__main__':

    unittest.main()
     
     # TODO: multiples strings separated by <br/> for example :O
     # If there’s more than one thing inside a tag, you can still look at just the strings. Use the .strings generator:
     # http://www.crummy.com/software/BeautifulSoup/bs4/doc/#strings-and-stripped-strings
     
     # TODO: Hacer un 2-stage training, 1st stage generar los xpaths y la 2nd stage filtra que xpaths dan lo que quiero.
     
     # TODO: que stripee cosas espureas del borde del string, por ejemplo si entrenamos con "Super Center" y encuentrá "at Super Center"
     #       que recuerde un regex o string para borrar "at " del comienzo. 