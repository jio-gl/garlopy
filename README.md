# garlopy
A Scrapely clone (learn HTML scrapping from examples) using  BeautifulSoup

# Example

```
from garlopy import GarlopyScraper
import unittest


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
        

    def test_basic(self):
        # make sure the shuffled sequence does not lose any elements
        html1 = '''
        <html>
        <p>Hector</p>
        </html>
        '''
        html2 = '''
        <html>
        <p>Jorge</p>
        </html>
        '''
        data1 = {'name':'Hector'}
        data2 = {'name':['Jorge']}

        self._test_scraper(html1, data1, html2, data2)

```
