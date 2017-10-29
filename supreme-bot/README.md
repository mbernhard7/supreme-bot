Supreme Bot
Created by Miles Bernhard

This is a bot for supremenewyork.com. The original code is on supreme.py and captcha_harvester.py

How this bot works is as follows:
1. It reads the config file and sets up separate Tasks, each with its own cart, each with item(s) inside.
2. For each task, it will add the items to cart
3. It will attempt to checkout based on the method the user specified in the config file.

The code is written by myself, with the exception of the twocaptcha API wrapper which I sourced from github and tweaked to my liking, and a few code snippets from stackoverflow that are all linked. Some elements (like the way I load configs, or the get_local_directory functions), came from older programs that I wrote, and may have been previously inspired by other’s work on stackoverflow or github, but at this point are common knowledge.

Going forward, I plan on a few upgrades. In order by priority:
1. Multithreading captcha token requests
2. Multithreading tasks
3. Proxy integration
4. Adding to cart by AJAX request 

For operation, the user needs to edit the main_config.txt file. The instructions to do so are included. Don’t leave any blank lines or break any of the conventions described. The checkout information included is for testing purposes, and the order will not go through. If the user wants to use AJAX checkouts in order to try and bypass captcha (will be explained later) they will also need to fill in the captcha_config.txt file. The convention for that file is key&value. Do not leave blank lines or lines that don’t follow this convention. Do not change the sitekey (unless you know what you’re doing), the supreme.py file will do this automatically. The API key needed is from 2captcha.com, a captcha solving api. The useragents.txt and captcha_tokens.txt files do not need to be changed.

The methods of checkout are “manually”, or through an AJAX POST request. 

The manual checkout method is more likely to be successful, and easier to troubleshoot in the event of something going wrong, but it’s slower. It requires you to solve the captcha supreme presents you manually (however, sometimes they don’t prompt you at all).

To do this, simply fill in the main_config.txt, and run the supreme.py program however you would like (Terminal —> Python path/to/supreme.py)

The AJAX method is faster, but it’s more fragile and is hit or miss. If it fails, it will be difficult to attempt to checkout again. As of now, it fills in the checkout form in order to get a few cookies that supreme sets, and then sends the request itself rather than clicking the button. This bypasses the manual solving of the captcha, instead sending one of the tokens harvested from the 2captcha API (a captcha solving API).

To run this program, it’s important to fill out both config files. You will then start the captcha_harvester.py (Terminal —> Python path/to/captcha_harvester.py). Wait until it has a satisfactory amount of tokens in the pool (normally one per cart), then in a separate terminal window run the supreme.py file (Terminal —> Python path/to/supreme.py).

If you were actually trying to get an item on release day (Every Thursday at 11 AM EST), you would want to start the supreme.py (regardless of method), at least a minute early to give it a chance to start up. It will refresh until the item becomes available. It’s important to note that if your refresh_delay is too low, you may get banned (by cookies, ip, ect.), and if you test the AJAX checkout method too much, you may get banned.

Additionally, I recommend running this in a virtualenv. I am running it on Python 2.7.1. Here is a list of what I have installed in the virtualenv I am running it in:

asn1crypto (0.22.0)
beautifulsoup4 (4.6.0)
bs4 (0.0.1)
certifi (2017.7.27.1)
cffi (1.10.0)
chardet (3.0.4)
cryptography (2.0.3)
enum34 (1.1.6)
idna (2.6)
ipaddress (1.0.18)
ndg-httpsclient (0.4.3)
pip (9.0.1)
pyasn1 (0.3.4)
pycparser (2.18)
pyOpenSSL (17.2.0)
requests (2.18.4)
requests-file (1.4.2)
selenium (3.5.0)
selenium-requests (1.3)
setuptools (36.4.0)
six (1.10.0)
tldextract (2.1.0)
urllib3 (1.22)
wheel (0.30.0)