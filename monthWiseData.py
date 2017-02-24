import re
import hug
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import io
import sys
from time import time
from datetime import datetime
from lxml import html
from datetime import datetime
import pytz


@hug.get('/market-data',examples='date=01/02/2017&state=Telangana&commodity=Carrot')
def start_scrape(date: hug.types.text, state: hug.types.text, commodity: hug.types.text):
	t = time()
	data = None
	try:
		log_file = open('log.txt', 'a')
		current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
		print(current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'), file = log_file)
		print (date, state, commodity, file = log_file)
		month = datetime.strptime(date, '%d/%m/%Y').strftime('%B')
		year = datetime.strptime(date, '%d/%m/%Y').year

		scraper = MonthCropWiseScraper()
		data = scraper.scrape(str(year), month, state, commodity,date, log_file)
		
	except Exception as e:	
		print (str(e), file = log_file)
	finally:
		print ("Time taken:" + str(round(time()-t, 3)) + "s\n", file = log_file)
		log_file.close()
		return data

class MonthCropWiseScraper(object):
	def __init__(self):
		self.url = "http://agmarknet.nic.in/agnew/NationalBEnglish/DatewiseCommodityReport.aspx"
		self.driver = webdriver.PhantomJS()
		self.driver.set_window_size(1120, 550)



	def scrape(self, year, month, state, commodity, date, log_file):
		self.driver.get(self.url)

		try:
			rows = []
			data = {}
			# Select state selection dropdown
			select = Select(self.driver.find_element_by_id('cboYear'))
			select.select_by_visible_text(year)

			select = Select(self.driver.find_element_by_id('cboMonth'))
			select.select_by_visible_text(month)

			wait = WebDriverWait(self.driver, 10)
			wait.until(lambda driver: driver.find_element_by_id('cboState').is_displayed() == True)

			select = Select(self.driver.find_element_by_id('cboState'))
			select.select_by_visible_text(state)

			wait = WebDriverWait(self.driver, 10)
			wait.until(lambda driver: driver.find_element_by_id('cboCommodity').is_displayed() == True)

			select = Select(self.driver.find_element_by_id('cboCommodity'))
			select.select_by_visible_text(commodity)

			wait = WebDriverWait(self.driver, 10)
			wait.until(lambda driver: driver.find_element_by_id('btnSubmit').is_displayed() == True)

			self.driver.find_element_by_id('btnSubmit').click()

			# s = BeautifulSoup(self.driver.page_source,"lxml")

			# s = s.find_all('tbody')[2]
			# cols = [a.find(text=True) for a in s.find('tr').find_all('th')]
			# table_data = [a.find(text=True) for a in s.find_all('td')]
			def check_value(value):
				if value is not None and value != 'NR':
					return True
				return False

			
			tree = html.fromstring(self.driver.page_source)
			cols = tree.xpath('//th/text()')
			table_data = [element.text for element in tree.xpath('//*[(@id = "gridRecords")]//td')]	
			
			current_market = ""
			obj = (table_data[pos:pos + 7] for pos in range(0, len(table_data), 7))		

			for market, arrival_date, quantity, variety, minimum, maximum, modal in obj:
				if check_value(variety) and check_value(minimum) and check_value(maximum) \
				and check_value(modal) and check_value(arrival_date):
					temp = {}
					if market is not None:
						current_market = market
					if arrival_date == date:					
						temp[cols[0]] = current_market
						temp[cols[2]] = quantity
						temp[cols[3]] = variety
						temp[cols[4]] = minimum
						temp[cols[5]] = maximum
						temp[cols[6]] = modal
						rows.append(temp)
			data['success'] = True
			data['message'] = "successfully got"
			return data
		except Exception as e:
			data['success'] = False
			data['message'] = str(e)
			print (str(e), file = log_file)
		finally:
			data['result'] = {'marketData': rows}
			return data

