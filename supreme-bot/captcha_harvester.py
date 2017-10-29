'''Miles Bernhard
Created 9/5
fetches captcha response from 2captcha pi, used wrapper from here: https://github.com/My-kal/2Captcha/blob/master/twocaptcha/__init__.py
required some bug fixes'''

import os
import time
from twocaptcha import TwoCaptcha

#returns the local working directory
def get_local_directory():
	file_directory=str(__file__).split('/') 
	del file_directory[-1:]
	return '/'.join(file_directory)

#opens file, makes a call to twocaptcha api, and appends response to fileas well as a timestamp
def add_captcha(sitekey,apikey):
	file=open(get_local_directory()+"/resources/captcha_tokens.txt","a")
	site_url = 'http://www.supremenewyork.com'
	twoCaptcha = TwoCaptcha(apikey)
	file.write(twoCaptcha.solve_recaptcha(site_url=site_url, site_key=sitekey)+"|"+str(time.time())+"\n")
	file.close()

#loads settings for captcha harvesting from file and returns as dictionairy
def load_config():
	#https://stackoverflow.com/questions/1038824/how-do-i-remove-a-substring-from-the-end-of-a-string-in-python
	config={}
	rfile = open(get_local_directory()+"/configuration_files/captcha_config.txt", "r")
	for line in rfile:
		config[line.split('&')[0]]=line.split('&')[1].rstrip('\n')
	rfile.close()
	return config

#returns lenth of file (lines)
#https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
def file_len(name):
	i=0
	with open(name) as f:
		for i, l in enumerate(f):
			pass
	return i+1

#reads current tokens, rewrites only the ones that are not too old (captcha tokens have a limited lifespan)
def trim(config):
	rfile = open(get_local_directory()+"/resources/captcha_tokens.txt", "r")
	lines=rfile.readlines()
	rfile.close()
	rfile=open(get_local_directory()+"/resources/captcha_tokens.txt","w")
	for line in lines:
		if (time.time()-float(line.split("|")[1].rstrip('\n'))<float(config["maxage"])):
			rfile.write(line)
	rfile.close()

#main function: loads config, and then as long as the program runs it will trim old tokens, print the number of tokens, and if the number of tokens is not as many as desired it will add a token, then it will wait before starting again
def main():
	config=load_config()
	while True:
		trim(config)
		print "[Captcha Harvester] Current captcha pool size: "+ str(file_len(get_local_directory()+"/resources/captcha_tokens.txt"))
		if (file_len(get_local_directory()+"/resources/captcha_tokens.txt")<int(config["maxpool"])):
			print "[Captcha Harvester] Adding captcha..."
			add_captcha(config['sitekey'],config['apikey'])
		time.sleep(float(config["timedelay"]))

main()
