# -*- coding: utf-8 -*-

'''
Miles Bernhard
Created 9/5
manages reading a configuration file, creating 'carts' based on file, adding items to cart via webdriving, and checking out with an AJAX request or manually
Last checked: 10/16/17
'''
import sys
import os
import time
import seleniumrequests
import random
from seleniumrequests import Chrome
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException


#gets the directory of the current file, converts to a list, removes "itself" from the list, and returns the current working directory as a string
def get_local_directory():
	file_directory=str(__file__).split('/') 
	del file_directory[-1:]
	return '/'.join(file_directory)

#updates the saved sitekey with the passed sitekey
def update_sitekey(sitekey):
	rfile=open(get_local_directory()+"/configuration_files/captcha_config.txt", "r") #opens config file for reading
	lines=rfile.readlines() #saves lines in file as array lines
	rfile.close() #closes file
	rfile=open(get_local_directory()+"/configuration_files/captcha_config.txt", "w") #opens file for writing
	for line in lines: #reads through lines for line containing sitekey, and replaces it with the argument sitekey
		if ("sitekey" in line.split('&')[0]):
			line="sitekey&"+sitekey+"\n"
		rfile.write(line)
	rfile.close() #closes file

#gets the youngest captcha token from file
def get_captcha():
	rfile=open(get_local_directory()+"/resources/captcha_tokens.txt","r") #opens list of captcha tokens
	lines=rfile.readlines() #saves tokens in an array
	rfile.close() #closes file
	rfile=open(get_local_directory()+"/resources/captcha_tokens.txt","w") #opens for reading
	token=""
	youngest=0.0
	#searches through for youngest captcha token
	for line in lines:
		if (float(line.split("|")[1].rstrip('\n'))>youngest):
			token=line.split("|")[0].rstrip('\n')
			youngest=float(line.split("|")[1].rstrip('\n'))
	#writes all the tokens except for youngest token
	for line in lines:
		if (token not in line.split("|")[0].rstrip('\n')):
			rfile.write(line.rstrip('\n')+"\n")
	rfile.close()
	return token

#selects random user agent, weighted based on popularity
#user agents sourced from https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
def random_user_agent():
	file=open(get_local_directory()+'/resources/useragents.txt') #opens list of agents
	raw_config = [line.rstrip('\n') for line in file] #removes linebreak character and appends into list
	weighted_agent_list=[] #list that will be populated proportionally by user agent
	for agent in raw_config:
		for _ in range(int(float(agent.split('%')[0])*10)):
			weighted_agent_list.append(agent.split('%')[1]) #appends user agent to the list repeatedly based on popularity
	file.close()
	return random.choice(weighted_agent_list) #picks random user agent from weighted list

#Load information from the configuration file in same directory
def load_config():
	file=open(get_local_directory()+'/configuration_files/main_config.txt')
	raw_config = file.read().split('\n')
	checkouts={} #dictionary of dictionarys, key is name of checkout and value is dictionary of checkout values
	items=[] #array of arrays of item information
	settings={} #dictionary of settings values
	config={} #dictionary that will contain all of the above
	for line in raw_config:
		if ('#'in line): #comment out instructions
			pass
		else:
			line_type=line.split("?")[0] #type of line (ie config,checkout, item)
			line_content=line.split("?")[1]
			if ('item' in line_type):
				items.append(line_content.split("&")) #if line starts with item, split content into array and append to item array
			elif ('checkout' in line_type):
				if not (line_type in checkouts.keys()): #if this checkout profile hasn't been added
					checkouts[line_type]={} #add this checkout profile to the dictionary of checkouts
				checkouts[line_type][line_content.split("&")[0]]=line_content.split("&")[1] #add this key and value to its respective checkout profile within the dictionairy of checkout profiles
			elif ('setting' in line_type):
				settings[line.split("?")[1].split("&")[0]]=line.split("?")[1].split("&")[1] # add key and value to settings dictionairy
	config["checkouts"]=checkouts
	config["items"]=items
	config["settings"]=settings
	file.close()
	return config

#class for one item
class Item:
	#pass in array (read from config file), set attributes of item
	def __init__(self,item,settings):
		self.category=item[0] #category of item, loaded from config. Used to load the page on which the item will appear
		self.keyword=item[1] #unique keyword to identify item. Loaded from config, should be a string of text that will only appear in that items title
		self.color=item[2] #color of item, some have more that one color (Red, black, ect)
		self.size=item[3] #string that is contained in the desired size. can be default, in which case the bot won't even try to select size. Used to select size
		self.in_cart=False #boolean of whether the item is in cart yet. Upoon initilization, will never be in cart. Used by the carting process to determine if there is anything ready to checkout
		self.link="" #specific link to the item. since these are random and not guessable, the link is scraped from the page (using category, keyword, color) and saved as an attribute for easier access later
		self.name="["+self.keyword+"-"+self.color+"-"+self.size+"]" #Name assigned for use during printing to console
		self.settings=settings #dictionairy of settings, such as timeout, refresh delay

	#runs monitor, if monitor returns true run add to cart, if add to cart returns true then returns true
	def cart(self,webdriver):
		if (self.monitor(webdriver)):
			if (self.add_to_cart(webdriver)):
				return True

	#runs find_link function, if it finds it returns true, otherwise sleeps for timeout and tries again
	def monitor(self,webdriver):
		print self.name+" Monitoring..."
		while True:
			if (self.find_link(webdriver)):
				return True
			else:
				time.sleep(int(self.settings["refresh_delay"]))

	#loads supreme page based on category, finds link to item, sets as attribute and returns true, if can't find returns false
	def find_link(self,webdriver):
		print self.name+" Searching for link..."
		webdriver.get("http://www.supremenewyork.com/shop/all/"+self.category)
		soup = BeautifulSoup(webdriver.page_source, "html.parser") #python module for reading html pages
		for element in soup.find_all("div",{"class":"inner-item"}): #for every item on page:
			if (self.keyword in element.text.lower()) and (self.color in element.text.lower()): #if item contains keyword
				self.link=element.find_all('a')[0].get('href') #grab the link from the item
				print self.name+" Found link..." 
				return True
		return False

	#adds item to cart on given webdriver
	def add_to_cart(self,webdriver):
		is_first=True #determines whether this is the first item being carted. Declares as true initially
		if (webdriver.find_element_by_id("cart").get_attribute("class")!="hidden"): #if the cart is not hidden, that means there is something already in the cart
			is_first=False
			item_count=int(filter(str.isdigit, str(webdriver.find_element_by_id("items-count").text))) #reads number of items in cart, to be used to confirm that carting was succesful
		print self.name+" Adding to cart..."
		webdriver.get('http://www.supremenewyork.com'+self.link) #go to items page
		try:
			if (("default") not in self.size):
				for option in webdriver.find_element_by_tag_name('select').find_elements_by_tag_name('option'): #get all options for sizes
					if self.size in option.text.lower(): #if size keyword is included in option, select it
						option.click()
						break #if found size, stop looking through sizes
		except NoSuchElementException: #if it can't find size selector (could be out of stock, could have no sizes)
			print self.name+" Failed to select size..." #will try to cart regardless of size selection
		try:
			webdriver.find_element_by_name("commit").click() #click the add to cart button
			while True:
				#if the item is first, and the cart appears, or if the item is not first and the amount of items in the cart goes up
				if (((webdriver.find_element_by_id("cart").get_attribute("class")!="hidden") and (is_first)) or ((is_first==False) and (int(filter(str.isdigit, str(webdriver.find_element_by_id("items-count").text)))>item_count))):
					#set attribute in cart to true
					self.in_cart=True
					print self.name+" Succesfully carted..."
					return True
		except NoSuchElementException, ValueError:
			#if it failed to cart
			try:
				print self.name+" "+webdriver.find_element_by_xpath('//*[@id="add-remove-buttons"]/b').text #try to print what the add to cart button says (normally 'out of stock')
			except NoSuchElementException:
				print self.name+" "+NoSuchElementException #otherwise print error
			self.in_cart=False
			return False
				

class Task:
	#takes arguments and creates class attributes for easier and prettier access
	def __init__(self,name,incart,checkout,settings):
		self.cart=[] #array of item objects to cart and checkout
		self.settings=settings #dictionairy of user settings
		for item in incart:
			self.cart.append(Item(item,self.settings)) #convert array of arrays to array of item objects
		self.checkout=checkout #dictionairy of checkout values (such as name, address, ect)
		self.name=name #name of task to be used during printing to console

	#creates a selenium webdriver
	def create_webdriver(self):
		#https://stackoverflow.com/questions/29916054/change-user-agent-for-selenium-driver
		opts = Options()
		self.useragent=random_user_agent() #calls for a random useragent
		opts.add_argument("user-agent="+self.useragent) #adds random user agent to options
		self.webdriver = Chrome(executable_path=get_local_directory()+'/resources/chromedriver',chrome_options=opts) #creates new webdriver with premade options
		self.webdriver.set_page_load_timeout(int(self.settings["timeout"])) #set timeout of pageload from config

		#attempts to cart every item in cart. Returns true if any of the items cart
	def cart_items(self):
		self.create_webdriver()
		return_bool=False
		for item in self.cart:
			if (item.in_cart==False):
				item.cart(self.webdriver)
			if (item.in_cart==True):
				return_bool=True
		return return_bool

	#loads checkout page, fills form, clicks checkout, waits for user to complete captcha
	def manual_checkout(self):
		self.webdriver.get('https://www.supremenewyork.com/checkout') #load the checkout page
		self.fill_form()
		self.webdriver.find_element_by_name("commit").click()
		if (self.wait_for_manual_captcha()):
			return self.confirmation()

	#fills all elements of form and check required check boxes
	def fill_form(self):
		#TODO: IF SITEKEY CHANGED, CLEAR OLD TOKENS (not high priority)
		update_sitekey(self.webdriver.find_element_by_xpath('//*[@id="cart-cc"]/fieldset/div[3]').get_attribute("data-sitekey")) #updates the captcha sitekey saved on file (in case it changed).
		self.webdriver.find_element_by_name("order[billing_name]").send_keys(self.checkout["name"])
		self.webdriver.find_element_by_name("order[email]").send_keys(self.checkout["email"])
		self.webdriver.find_element_by_name("order[tel]").send_keys(self.checkout["phone"])
		self.webdriver.find_element_by_name("order[billing_address]").send_keys(self.checkout["address"])
		self.webdriver.find_element_by_name("order[billing_zip]").send_keys(self.checkout["zipcode"])
		self.webdriver.find_element_by_name("order[billing_city]").send_keys(self.checkout["city"])
		self.webdriver.find_element_by_name("order[billing_state]").send_keys(self.checkout["state"])
		self.webdriver.find_element_by_name("order[billing_country]").send_keys(self.checkout["country"])
		checkout_field=self.webdriver.find_element_by_name("credit_card[nlb]")
		for character in list(self.checkout["card_number"]): #weird error occurs when you send all at once,was shuffling characters
			time.sleep(.01)
			checkout_field.send_keys(character)
		self.webdriver.find_element_by_name("credit_card[month]").send_keys(self.checkout["card_month"])
		self.webdriver.find_element_by_name("credit_card[year]").send_keys(self.checkout["card_year"])
		self.webdriver.find_element_by_name("credit_card[rvv]").send_keys(self.checkout["cvv"])
		self.webdriver.find_element_by_xpath("//*[@id='cart-cc']/fieldset/p[2]/label/div/ins").click()

	#loads checkout page, fills form(supreme supplies necessary cookies during form filling, so even though I never submit I need to fill the form)
	def ajax_checkout(self):
		self.webdriver.get('https://www.supremenewyork.com/checkout')
		if ("y" in self.settings["fill_form"]):
			try:
				self.fill_form()
			except NoSuchElementException:
				pass
		csrf_token = self.webdriver.find_element_by_name('csrf-token').get_attribute("content")
		#headers required to make AJAX request, found using chrome devtools
		headers = {
			'Accept': '*/*',
			'X-CSRF-Token': csrf_token,
			'X-Requested-With': 'XMLHttpRequest',
			'Referer': 'https://www.supremenewyork.com/checkout',
			'Accept-Language': 'en-US,en;q=0.8',
			'User-Agent': self.useragent,
			'Connection': 'keep-alive',
			#'Host':'wwww.supremenewyork.com',
			'Origin': 'https://www.supremenewyork.com',
			'Accept-Encoding': 'gzip, deflate, br',
			'Content-Length':'1006',
			'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
		}
		#payload required to make AJAX request, found using chrome devtools
		payload = {
				'utf8': '✓',
				'authenticity_token': csrf_token,
				'order[billing_name]': self.checkout['name'],
				'order[email]': self.checkout['email'],
				'order[tel]': self.checkout['phone'],
				'order[billing_address]': self.checkout['address'],
				'order[billing_address_2]': '',
				'order[billing_zip]': self.checkout['zipcode'],
				'order[billing_city]': self.checkout['city'],
				'order[billing_state]': self.checkout['state'],
				'order[billing_country]': self.checkout['country'],
				'same_as_billing_address': '1',
				'asec': 'Rmasn',
				'store_credit_id': '',
				'credit_card[nlb]': self.checkout["card_number"],
				'credit_card[month]': self.checkout["card_month"],
				'credit_card[year]': self.checkout["card_year"],
				'credit_card[rvv]': self.checkout["cvv"],
				'order[terms]': '0',
				'order[terms]': '1',
				'credit_card[vval]': self.checkout["cvv"],
				'g-recaptcha-response': get_captcha()
			}
		#make request, print response
		response = self.webdriver.request('POST','https://www.supremenewyork.com/checkout.json', data=payload, headers=headers)
		print "["+self.name+"] RESPONSE: "+response.text

		#looks to see if captchas solved yet
	def wait_for_manual_captcha(self):
		while (True):
			#trys to click checkout, if captcha is visible it will throw WebDriverException
			try:
				self.webdriver.find_element_by_name("commit").click()
				return True
			except WebDriverException:
				print "["+self.name+"] Fill captcha manually..."
				time.sleep(3)

	#finds result of checkout on confirmation page
	def confirmation(self):
		while True:
			try:
				if ('selected' in self.webdriver.find_element_by_xpath('//*[@id="tabs"]/div[3]').get_attribute('class')): #if the confirmation tab is selected
					print "["+self.name+"] Response: "+self.webdriver.find_element_by_id('content').text.split("CONFIRMATION")[1] #print the desired information from checkout page
					return True
			except (NoSuchElementException, StaleElementReferenceException): #thrown if tab is not selected
				print "["+self.name+"] Waiting for confirmation..."
				time.sleep(1)

#main thread that loads config, optimizes carts, adds to cart, and checks out
def main():
	config=load_config() #loads the entire config file as dictionairy
	print "[Supreme Bot] Loaded configuration, optimizing carts..."
	carts=[[]] #array of arrays of items
	#the following loop reads throught array of items, checks to see if an identical item is alread in the current cart, and if not adds it to the cart and deletes it. Supreme only allows one of each item per cart, so this groups them into the minimal amount of carts to minimize shipping costs
	uncarted=config["items"] #makes new array of uncarted items
	#loops through all uncarted items, creates minimum amount of carts (Supreme only allows one identical item per checkout)
	for item in uncarted:
			incart=False
			for cart in carts:
				dup=False
				for cart_item in cart:
					print cart_item[0],item[0],cart_item[1],item[1]
					if ((cart_item[0] in item[0]) and (cart_item[1] in item[1])): 
						dup=True
				if not dup:
					cart.append(item)
					incart=True
					break
			if not incart:
				carts.append([item])
	tasks={} #dictionairy of tasks, key is name and value is Task object
	if ("y" in config["settings"]["optimize_carts"]):
		print "[Supreme Bot] "+str(len(carts))+" carts created..."
		for cart in carts:
			print "[Supreme Bot] Cart: "+str(cart) #print carts for the user to see
		if len(carts)>len(config["checkouts"]):
			print "[Supreme Bot] Error: "+str(len(carts))+" carts and "+str(len(config["checkouts"].items()))+" checkout profiles!" #if you don't have enough checkout profiles for each cart, quit
			print "[Supreme Bot] Edit your configuration file and try again."
			sys.exit()
		for i in range(len(carts)):
			tasks["task"+str(i+1)]=Task("task"+str(i+1), carts[i],config["checkouts"][config["checkouts"].keys()[i]],config["settings"]) #creates new task object for each cart with a unique name, checkout profile, and cart and the same settings
	else:
		print "[Supreme Bot] "+str(len(carts))+" checkout profiles needed..."
		if len(carts)>len(config["checkouts"]):
			print "[Supreme Bot] Error: "+str(len(carts))+" profiles needed and "+str(len(config["checkouts"].items()))+" checkout profiles available!" #if you don't have enough checkout profiles for each cart, quit
			print "[Supreme Bot] Edit your configuration file and try again."
			sys.exit()
		for i in range(len(carts)):
			for item in carts[i]:
				tasks["task"+str(i+1)]=Task("task"+str(i+1),[item],config["checkouts"][config["checkouts"].keys()[i]],config["settings"]) #creates new task object for each cart with a unique name, checkout profile, and cart and the same settings
	print "[Supreme Bot] "+str(len(tasks.keys()))+" tasks created..."
	print "[Supreme Bot] Starting carting..."
	t0=time.time() #initial time for performance checking
	for key in tasks.keys(): #for every task
		while True:
			try:
				if (tasks[key].cart_items()): #cart items in task
					print "["+tasks[key].name+"] Carted all items..."
					break
			except TimeoutException: #occasionally, webdriver encounters a bug on first page load that causes them to get stuck in timeout. Only solution I found is to quit it and start again. Only happens on first page load
				tasks[key].webdriver.close()
				tasks[key].create_webdriver()
		print "["+tasks[key].name+"] Starting checkout..."
		if ("y" in config["settings"]["manual_checkout"]): #do manual checkout if specified by settings
			if (tasks[key].manual_checkout()):
				print "["+tasks[key].name+"] Checked out all items!"
				print "[Supreme Bot] Total time: "+str(time.time()-t0)
		elif ("y" in config["settings"]["ajax_checkout"]): #do ajax checkout if specified by settings
			tasks[key].ajax_checkout() #checkout task
			print "[Supreme Bot] Total time: "+str(time.time()-t0)

main()