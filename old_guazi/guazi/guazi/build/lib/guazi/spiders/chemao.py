# -*- coding: UTF-8 -*-
import json
import re
import time
import redis
import requests
import scrapy
import logging

from lxml import etree
from scrapy.conf import settings
from ..items import GuaziItem
from ..redis_bloom import BloomFilter

website = 'chemao'


class CarSpider(scrapy.Spider):
    name = website
    allowed_domains = ["chemao.com"]
    start_urls = ['https://www.chemao.com/bjs/s/00cf1so10',
                  'https://www.chemao.com/tjs/s/00cf1so10',
                  'https://www.chemao.com/shs/s/00cf1so10',
                  'https://www.chemao.com/zqs/s/00cf1so10',
                  'https://www.chemao.com/zz/s/00cf1so10',
                  'https://www.chemao.com/nj/s/00cf1so10',
                  'https://www.chemao.com/sz/s/00cf1so10',
                  'https://www.chemao.com/xa/s/00cf1so10',
                  'https://www.chemao.com/hz/s/00cf1so10',
                  'https://www.chemao.com/wh/s/00cf1so10',
                  'https://www.chemao.com/cs/s/00cf1so10',
                  'https://www.chemao.com/cd/s/00cf1so10',
                  'https://www.chemao.com/gz/s/00cf1so10',
                  'https://www.chemao.com/sc/s/00cf1so10',
                  'https://www.chemao.com/fz/s/00cf1so10',
                  'https://www.chemao.com/jzh/s/00cf1so10',
                  'https://www.chemao.com/qg/s/00cf1so10'
                  ]


    def __init__(self, **kwargs):
        self.bf = BloomFilter(key='b1f_' + website)
        super(CarSpider, self).__init__(**kwargs)
        settings.set('WEBSITE', website, priority='cmdline')
        self.counts = 0

    def parse(self, response):
        sorry_info = response.xpath('//p[@class="sorry"]').extract()
        if sorry_info:
            return
        for href in response.xpath('//div[@id="carPicList"]/div[@class="list"]'):
            urlbase = href.xpath("./div/a/@href").extract_first()
            url = response.urljoin(urlbase)
            yield scrapy.Request(url, callback=self.parse_car)

        # next page
        next_page = response.xpath('//a[@class="page-next"]/@href')
        if next_page:
            url_next = response.urljoin(next_page.extract_first())
            yield scrapy.Request(url_next, self.parse)

    def parse_car(self, response):

        grap_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_dict = {
            "projectName": "used-car-scrapy",
            "logProgram": website,
            "logProgramPath": "/home/scrapyd/eggs/guazi",
            "logPath": "/home/scrapyd/logs/guazi/{}/".format(website),
            "logTime": grap_time,
            "logMessage": "",
            "logServer": "192.168.1.248",
            "logObjectType": "UsedCarPaChong",
        }
        status = response.xpath('//div[@class="shelf-wram"] | //div[@class="car-status"]')
        if status:
            status = "sold"
        else:
            status = "sale"

        price = response.xpath('//em[text()="???"]/../text()').extract_first()
        datetime = response.xpath('//span[@class="Tahoma"]/text()').extract_first()

        # item loader
        item ={}
        if response.xpath('//*[@id="det_title"]/text()'):
            trade_id = response.xpath('//input[@id="trade_id"]/@value').extract_first()
            url = 'https://www.chemao.com/index.php?app=show&act=show_more&id=' + trade_id
            res = requests.get(url,headers ={'Referer': 'http://www.kx.cn',
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"},verify=False)
            html = etree.HTML(res.content.decode('gb2312'))

            body = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if body:
                item['body'] = body[0].strip()
            else:
                item['body'] = '-'

            bodystyle = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if bodystyle:
                if len(bodystyle[0].split(u'???')) > 1:
                    item['bodystyle'] = bodystyle[0].split(u'???')[1].strip()
                else:
                    item['bodystyle'] = '-'
            else:
                item['bodystyle'] = '-'

            gear = html.xpath('//td[text()="?????????"]/../td[2]/text()')
            if gear:
                item['gear'] = gear[0].strip()
            else:
                item['gear'] = '-'

            gearnumber = html.xpath('//td[contains(text(), "?????????")]/../td[2]/text()')
            if gearnumber:
                item['gearnumber'] = gearnumber[0].strip()
            else:
                item['gearnumber'] = '-'

            doors = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if doors:
                if len(doors[0].split(u'???')) > 1:
                    item['doors'] = doors[0].split(u'???')[0].strip()
                else:
                    item['doors'] = '-'
            else:
                item['doors'] = '-'

            seats = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if seats:
                if len(seats[0].split(u'???')) > 1:
                    item['seats'] = seats[0].split(u'???')[1][0]
                else:
                    item['seats'] = '-'
            else:
                item['seats'] = '-'

            size = html.xpath('//td[contains(text(), "?????????")]/../td[2]/text()')
            if size:
                temp = size[0].split('*')
                if len(temp) == 3:
                    item['length'] = temp[0]
                    item['width'] = temp[1]
                    item['height'] = temp[2]
                else:
                    item['length'] = '-'
                    item['width'] = '-'
                    item['height'] = '-'
            else:
                item['length'] = '-'
                item['width'] = '-'
                item['height'] = '-'

            fueltype = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if fueltype:
                item['fueltype'] = fueltype[0]
            else:
                item['fueltype'] = '-'

            fuelnumber = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if fuelnumber:
                item['fuelnumber'] = fuelnumber[0]
            else:
                item['fuelnumber'] = '-'

            maxnm = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if maxnm:
                item['maxnm'] = maxnm[0]
            else:
                item['maxnm'] = '-'

            maxpower = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if maxpower:
                item['maxpower'] = maxpower[0]
            else:
                item['maxpower'] = '-'

            maxps = html.xpath(u'//td[contains(text(), "????????????")]/../td[2]/text()')
            if maxps:
                item['maxps'] = maxps[0]
            else:
                item['maxps'] = '-'

            lwv = html.xpath(u'//td[contains(text(), "??????????????????")]/../td[2]/text()')
            if lwv:
                item['lwv'] = lwv[0]
            else:
                item['lwv'] = '-'

            lwvnumber = html.xpath(u'//td[contains(text(), "?????????")]/../td[2]/text()')
            if lwvnumber:
                item['lwvnumber'] = lwvnumber[0]
            else:
                item['lwvnumber'] = '-'

            compress = html.xpath('//td[contains(text(), "?????????")]/../td[2]/text()')
            if compress:
                item['compress'] = compress[0]
            else:
                item['compress'] = '-'

            driverway = html.xpath('//td[contains(text(), "????????????")]/../td[2]/text()')
            if driverway:
                item['driverway'] = driverway[0]
            else:
                item['driverway'] = '-'


        else:

            item['body'] = '-'

            item['bodystyle'] = '-'

            item['gear'] = '-'

            item['gearnumber'] = '-'

            item['doors'] = '-'

            item['seats'] = '-'

            item['length'] = '-'
            item['width'] = '-'
            item['height'] = '-'

            item['fueltype'] = '-'

            fuelnumber = response.xpath('//dt[contains(text(),"????????????")]/../dd/text()')
            if fuelnumber:
                item['fuelnumber'] = fuelnumber.extract_first()
            else:
                item['fuelnumber'] = '-'

            item['maxnm'] = '-'

            item['maxpower'] = '-'

            item['maxps'] = '-'

            item['lwv'] = '-'

            item['lwvnumber'] = '-'

            item['compress'] = '-'

            driverway = response.xpath(u'//dt[contains(text(), "????????????")]/../dd/text()')
            if driverway:
                item['driverway'] = driverway.extract_first()
            else:
                item['driverway'] = '-'
        try:
            self.counts += 1
            logging.log(msg="download   " + str(self.counts) + "  car_items", level=logging.INFO)
            car_item =GuaziItem()
            car_item["carid"] = re.findall(r'\d+', response.url)[0]
            car_item["car_source"] = "chemao"
            car_item["usage"] = response.xpath('//td[contains(text(), "??????????????????")]/../td[2]/text()').extract_first().strip()
            car_item["grab_time"] = grap_time
            car_item["update_time"] = None
            car_item["post_time"] = response.xpath('//li[contains(text(), "????????????")]/span[1]/text()').extract_first()
            car_item["sold_date"] = None
            car_item["pagetime"] =grap_time
            car_item["parsetime"] = grap_time
            car_item["shortdesc"] = response.xpath('//*[@id="det_title"]/text()').extract_first().strip()
            car_item["pagetitle"] = response.xpath("//title/text()").extract_first().strip("")
            car_item["url"] = response.url
            car_item["newcarid"] =None
            car_item["status"] = status
            car_item["brand"] = re.findall(r'??????(\S+)',response.xpath('//div[@class="show-breadcrumb w1190"]/ul/li[3]/a/@title').extract_first())[0]


            car_item["series"] =re.findall(r'??????(\S+)',response.xpath('//div[@class="show-breadcrumb w1190"]/ul/li[4]/a/@title').extract_first())[0]

            car_item["factoryname"] = None
            car_item["modelname"] = None
            car_item["brandid"] = None
            car_item["familyid"] = None
            car_item["seriesid"] = None
            try:
                car_item['makeyear'] = re.findall(r'\d{4}',response.xpath('//*[@id="det_title"]/text()').extract_first())[0]
            except:
                car_item['makeyear'] =None

            car_item["registeryear"] =re.findall(r'\d{4}',response.xpath('//div[contains(text(), "????????????")]/em/text()').extract_first())[0]
            car_item["produceyear"] = None
            car_item["body"] = item['body']
            car_item["bodystyle"] = item['bodystyle']

            car_item["level"] = response.xpath('//td[contains(text(), "????????????")]/../td[2]/text()').extract_first().strip()
            car_item["fueltype"] = item['fueltype']
            car_item["driverway"] = item['driverway']
            car_item["output"] = response.xpath('//td[contains(text(), "??????")]/../td[2]/text()').extract_first().strip()
            car_item["guideprice"] = None
            # ???????????????46.30???(??????)
            try:
                car_item["guidepricetax"] =re.findall(r'(\d+\.\d+.*)',response.xpath('//span[@class="p2"]/text()').extract_first())[0]
            except:
                car_item['guidepricetax'] =None
            car_item["doors"] =item['doors']
            car_item["emission"] = response.xpath('//div[contains(text(), "????????????")]/em/text()').extract_first()
            car_item["gear"] =item['gear']
            car_item["geartype"] = response.xpath('//td[contains(text(), "???????????????")]/../td[2]/text()').extract_first().strip()
            car_item["seats"] =item['seats']
            car_item["length"] = item['length']
            car_item["width"] =item['width']
            car_item["height"] = item['height']
            car_item["gearnumber"] = item['gearnumber']
            car_item["weight"] = None
            car_item["wheelbase"] =None
            car_item["generation"] =  response.xpath(
                '//div[@class="cd_m_pop_pzcs_slide"]/ul/li/dl/dd/span[contains(text(),"\u6b3e\u4ee3")]/following-sibling::span/text()').extract_first()
            car_item["fuelnumber"] =item['fuelnumber']
            car_item["lwv"] = item['lwv']
            car_item["lwvnumber"] =item['lwvnumber']
            car_item["maxnm"] = item['maxnm']
            car_item["maxpower"] = item['maxpower']
            car_item["maxps"] =item['maxps']
            car_item["frontgauge"] = None
            car_item["compress"] = item['compress']
            car_item["registerdate"] = response.xpath('//div[contains(text(), "????????????")]/em/text()').extract_first()
            car_item["years"] = None
            car_item["paytype"] = None
            car_item["price1"] = response.xpath('//em[text()="???"]/../../span/text()').extract_first()
            car_item["pricetag"] = None
            car_item["mileage"] = response.xpath('//div[contains(text(), "????????????")]/em/text()').extract_first()
            car_item["color"] = response.xpath(
                '//td[contains(text(), "??????")]/../td[2]/text()').extract_first().strip()
            car_item["city"] = re.findall(r'???(.*)???',response.xpath('//td[contains(text(), "?????????")]/../td[2]/text()').extract_first())[0].strip()
            car_item["prov"] = re.findall(r'(.*)???.*???',response.xpath('//td[contains(text(), "?????????")]/../td[2]/text()').extract_first())[0].strip()
            car_item["guarantee"] = '?????????????????????/??????????????????/??????????????????'
            car_item["totalcheck_desc"] = None
            car_item["totalgrade"] = None
            car_item["contact_type"] = None
            car_item["contact_name"] = None
            car_item["contact_phone"] = None
            car_item["contact_address"] =None
            car_item["contact_company"] = None
            car_item["contact_url"] = None
            car_item["change_date"] = None
            try:
                car_item["change_times"] =  re.findall(r'\d+',response.xpath('//td[contains(text(), "????????????")]/../td[2]/text()').extract_first())[0]
            except:
                car_item["change_times"] =None
            car_item["insurance1_date"] = response.xpath('//td[contains(text(), "?????????")]/../td[2]/text()').extract_first().strip()
            car_item["insurance2_date"] =response.xpath('//td[contains(text(), "???????????????")]/../td[2]/text()').extract_first().strip()
            car_item["hascheck"] = None
            car_item["repairinfo"] =None
            car_item["yearchecktime"] = response.xpath('//td[contains(text(), "???????????????")]/../td[2]/text()').extract_first().strip()
            car_item["carokcf"] = None
            car_item["carcard"] = None
            car_item["carinvoice"] = None
            car_item["accident_desc"] = None
            car_item["accident_score"] = None
            car_item["outer_desc"] = None
            car_item["outer_score"] = None
            car_item["inner_desc"] = None
            car_item["inner_score"] =None
            car_item["safe_desc"] = None
            car_item["safe_score"] = None
            car_item["road_desc"] = None
            car_item["road_score"] = None
            car_item["lastposttime"] = None
            car_item["newcartitle"] = None
            car_item["newcarurl"] = None
            car_item["img_url"] = response.xpath("//div[@id='slide-image-list']/img[1]/@src").extract_first()
            car_item["first_owner"] = response.xpath(
                '//td[contains(text(), "????????????")]/../td[2]/text()').extract_first()
            car_item["carno"] = response.xpath('//div[contains(text(), "?????????")]/em/text()').extract_first()
            car_item["carnotype"] = None
            car_item["carddate"] = None
            car_item["changecolor"] = None
            car_item["outcolor"] = None
            car_item["innercolor"] = None
            car_item["desc"] = '.'.join( response.xpath("//div[@class='info fl']/p/text()").extract())
            car_item["statusplus"] = response.url + "-None-sale-" + str(car_item["price1"]) + car_item['post_time'] + car_item['pagetitle']
            car_item['url'] = response.url
            car_item['grab_time'] = time.strftime('%Y-%m-%d %X', time.localtime())
            car_item['status'] = response.url + "-" + str(price) + "-" + str(status) + "-" + datetime
            car_item['pagetime'] = datetime
            # yield item
        except:
            log_dict["logType"] = 'ERROR'
            log_dict["logMessage"] = response.url
            logging.log(msg=json.dumps(log_dict, ensure_ascii =False), level=logging.INFO)
        else:
            log_dict["logType"] = 'INFO'
            log_dict["logMessage"] = "successful"
            log_dict["logObject"] = {
                "field": {
                    "carsource": website,
                    "grab_time": car_item["grab_time"],
                    "price1": car_item["price1"],
                    "mileage": car_item["mileage"],
                    "post_time": car_item["post_time"],
                    "sold_date":car_item["sold_date"],
                    "city":car_item["city"],
                    "registerdate":car_item["registerdate"]
                },
                "info": {
                    "dataBaseType": "mysql",
                    "dataBaseName": settings["MYSQLDB_DB"],
                    "tableName": website + '_online',
                    "saveStatus": ""
                }
            }
            returndf = self.bf.isContains(car_item["statusplus"])
            # 1???????????????0???????????????
            if returndf == 1:
                log_dict["logObject"]["info"]["saveStatus"] = "true"
            else:
                log_dict["logObject"]["info"]["saveStatus"] = "false"
            logging.log(msg=json.dumps(log_dict,ensure_ascii=False), level=logging.INFO)
            yield  car_item
