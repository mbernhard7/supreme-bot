# twocaptcha/__init__.py
#NOT WRITTEN BY MILES BERNHARD
#found on github here: https://github.com/My-kal/2Captcha/blob/master/twocaptcha/__init__.py
#a few bug fixes were required, and made a few tweaks to what is printed

import requests
from time import sleep

class TwoCaptcha(object):
    """Interface for 2Captcha API."""
    

    def __init__(self, api_key):
        self.session = requests.session()
        self.session.params = {'key': api_key}
        self.BASE_URL = 'http://2captcha.com'

    def solve_recaptcha(self, site_url, site_key, proxy=None, poll=None):
        payload = {
            'googlekey': site_key,
            'pageurl': site_url,
            'method': 'userrecaptcha'
        }
        # post site key to get captcha ID
        if proxy:
            req = self.session.post('http://2captcha.com/in.php', params=payload, proxies=proxy)
        else:
            req = self.session.post('http://2captcha.com/in.php', params=payload)
        captcha_id = req.text.split('|')[1]

        # retrieve response [recaptcha token]
        payload = {}
        payload['id'] = captcha_id
        payload['action'] = 'get'

        if proxy:
            req = self.session.get('http://2captcha.com/res.php', params=payload, proxies=proxy)
        else:  
            req = self.session.get('http://2captcha.com/res.php', params=payload)


        recaptcha_token = req.text
        while 'CAPCHA_NOT_READY' in recaptcha_token:
            recaptcha_token = req.text
            if ('CAPCHA_NOT_READY' in recaptcha_token):
                print "[Captcha Harvester] "+recaptcha_token
            sleep(5)
            req = self.session.get('http://2captcha.com/res.php', params=payload)
        recaptcha_token = recaptcha_token.split('|')[1]
        print "[Captcha Harvester] "+recaptcha_token
        return recaptcha_token

    def get_balance(self):
        
        payload = {
            'action': 'getbalance',
            'json': 1,
        }
        response = self.session.get(url=self.BASE_URL + '/res.php', params=payload)
        JSON = response.json()
        if JSON['status'] == 1:
            balance = JSON['request']
            return balance
