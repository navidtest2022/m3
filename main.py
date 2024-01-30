import re
import os
import sys
import json
import html
import base64
import requests
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from json.decoder import JSONDecodeError
from random import randint, choice, uniform
from colorama import Fore, Back, Style, init
from requests.exceptions import RequestException, ConnectionError, Timeout
from http.cookies import SimpleCookie


init(autoreset=True)

sc_ver = "MULTI FAUCET EARNER"
host = 'faucetearner.org'

end = "\033[K"
res = Style.RESET_ALL
bg_red = Back.RED
red = Style.BRIGHT+Fore.RED
white = Style.BRIGHT+Fore.WHITE
green = Style.BRIGHT+Fore.GREEN
celeste = Style.BRIGHT+Fore.CYAN
lila = Style.BRIGHT+Fore.MAGENTA
yellow = Style.BRIGHT+Fore.YELLOW

def clean_screen():
    os.system("clear" if os.name == "posix" else "cls")

def banner():
    clean_screen()
    msg_line()
    print(f"{green}{sc_ver.center(50, ' ')}")
    msg_line()

def wait(x):
    for i in range(x, -1, -1):
        col = yellow if i%2 == 0 else white
        animation = "⫸" if i%2 == 0 else "⫸⫸"
        m, s = divmod(i, 60)
        t = f"[00:{m:02}:{s:02}]"
        sys.stdout.write(f"\r  {white}Please wait {col}{t} {animation}{res}{end}\r")
        sys.stdout.flush()
        sleep(1)

def carousel_msg( message):
    def first_part(message, wait):
        animated_message = message.center(48)
        msg_effect = ""
        for i in range(len(animated_message) - 1):
            msg_effect += animated_message[i]
            sys.stdout.write(f"\r {msg_effect}{res} {end}")
            sys.stdout.flush()
            sleep(0.03)
        if wait:
            sleep(1)

    msg_effect = message[:47]
    wait = True if len(message) <= 47 else False
    first_part(msg_effect, wait)
    if len(message) > 47:
        for i in range(50, len(message)):
            msg_effect = msg_effect[1:] + message[i]
            if i > 1:
                sys.stdout.write(f"\r {msg_effect} {res}{end}")
                sys.stdout.flush()
            sleep(0.1)
    sleep(1)
    sys.stdout.write(f"\r{res}{end}\r")
    sys.stdout.flush()

def msg_line():
    print(f"{green}{'━' * 50}")

def msg_action(action):
    now = datetime.now()
    now = now.strftime("%d/%b/%Y %H:%M:%S")
    total_length = len(action) + len(now) + 5
    space_count = 50 - total_length
    msg = f"[{action.upper()}] {now}{' ' * space_count}"
    print(f"{bg_red} {white}{msg}{res}{red}⫸{res}{end}")

def write_json(content):
    with open('config.json', 'w') as f:
        json.dump(content, f, indent=4)

class Bot:

    def curl(self, method, url, data=None):
        headers = {'user-agent': self.user_agent}
        if 'login' in url or 'register' in url:
            headers['x-requested-with'] = 'XMLHttpRequest'
            headers['content-type'] = 'application/json'
        while True:
            try:
                r = self.sessions[self.email].request(method, url, headers=headers, data=data, timeout=10)
                if r.status_code == 200:
                    return r
                elif r.status_code == 403:
                    print(f"{red}Access denied{end}")
                    exit()
                elif 500 <= r.status_code < 600:
                    carousel_msg(f"Server {host} down.")
                else:
                    carousel_msg(f"Unexpected response code: {r.status_code}")
                    return None
            except ConnectionError:
                carousel_msg(f"Reconnecting to {host}")
            except Timeout:
                carousel_msg("Too many requests")
            wait(10)
            
    def remove_account(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"\n{red}File config not found{res}")
            exit()
        except Exception:
            print(f"\n{red}Error reading config file{res}")
            exit()
        
        if config['Data']:
            accounts = [entry['Email'] for entry in config['Data']]
        else:
            print(f"\n{red}No accounts found{res}")
            exit()
    
        print(f"\n{celeste}Available accounts{red}:{res}\n")
        for idx, email in enumerate(accounts, start=1):
            print(f"{green}{idx}{white}.- {email}")
    
        idx_to_remove = input(f"\n{yellow}Enter the number of the account you want to remove{red}:{res} ")
        if idx_to_remove.isspace() or idx_to_remove == '' or idx_to_remove.lower() == 'exit':
            print(f"\n{red}Operation aborted{res}")
            exit()
        try:
            idx_to_remove = int(idx_to_remove)
        except Exception:
            print(f"\n{red}Error selection")
            exit()
    
        if 1 <= idx_to_remove <= len(accounts):
            email_to_remove = accounts[idx_to_remove - 1]
            config['Data'] = [entry for entry in config['Data'] if entry.get('Email') != email_to_remove]
            
            write_json(config)
    
            print(f"\n{red}Account with email {yellow}' {email_to_remove} '{red} successfully removed{res}")
        else:
            print(f"\n{red}Invalid account number{res}")
            exit()
    
    def data_account(self):
        carousel_msg("Getting user info")
        while True:
            url = f"https://{host}/dashboard.php"
            r = self.curl('GET', url)
            v = {}
            soup = BeautifulSoup(r.text, 'html.parser')
            username = soup.find('p', {'style': 'max-width: 130px;overflow: hidden;text-wrap: nowrap;text-overflow: ellipsis;'})
            v['username'] = username.text.strip() if username else None
    
            keywords = {
                'total_bal': 'Total Balance:',
                'faucet_earn': 'Faucet Earnings:',
                'ptc_earn': 'PTC Earnings:',
                'invest_earn': 'Investment Earnings:',
                'reff_earn': 'Referrals Earnings:'
            }
            
            for key, value in keywords.items():
                element = soup.find('div', string=lambda text: text and value in text).find_next('b', {'translate': 'no'})
                v[key] = element.text.split(' ')[0].strip() if element else None
                if v[key] is not None:
                    v[key] = "{:.8f}".format(float(v[key]))
    
            if any(value is None or len(value) < 5 for value in v.values()):
                continue
            else:
                break
        return v
    
    def mainbot(self):
        
        def lottery():
            nonlocal total_claims_lottery
            nonlocal total_collected_lottery
            carousel_msg("Go to lottery section")
            while True:
                r = self.curl('GET', f"https://{host}/referrals.php")
                if r:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    tickets = soup.find('b', {'id': 'reward'}).text
                    if tickets is not None and tickets.isdigit() and int(tickets) > 0:
                        r =  self.curl('POST', f"https://{host}/api.php?act=reward")
                        if r:
                            r = json.loads(r.text)
                            if 'message' in r and r['message']:
                                v = self.data_account()
                                self.total_balance += float(v['total_bal'])
                                match = re.search(r'(\d+\.\d+) XRP', r['message'])
                                if match:
                                    earn = float(match.group(1))
                                else:
                                    earn = 0
                                total_claims_lottery += 1
                                total_collected_lottery += earn
                                earn = "{:.8f}".format(float(earn))
                                msg_action("LOTTERY")
                                print(f" {red}# {white}Reward: {green}{earn}{white} XRP{res}{end}")
                                print(f" {red}# {white}Balance: {green}{v['total_bal']}{white} XRP{res}{end}")
                                msg_line()
                            else:
                                print(r)
                            return
                    else:
                        carousel_msg("Not availables tickets")
                        return
                        
        def faucet():
            nonlocal total_claims_faucet
            nonlocal total_collected_faucet
            carousel_msg("Go to faucet section")
            while True:
                r =  self.curl('POST', f"https://{host}/api.php?act=faucet")
                if r:
                    r = json.loads(r.text)
                    if 'message' in r and r['message']:
                        v = self.data_account()
                        self.total_balance += float(v['total_bal'])
                        match = re.search(r'(\d+\.\d+) XRP', r['message'])
                        if match:
                            earn = float(match.group(1))
                        else:
                            earn = 0
                        total_claims_faucet += 1
                        total_collected_faucet += earn
                        earn = "{:.8f}".format(float(earn))
                        if float(earn) > self.best_claim[self.email]:
                            self.streak[self.email] = 1
                            self.best_claim[self.email] = float(earn)
                        elif float(earn) == self.best_claim[self.email]:
                            self.streak[self.email] += 1
                        best_claim = "{:.8f}".format(self.best_claim[self.email])
                        msg_action("FAUCET")
                        print(f" {red}# {white}Reward: {green}{earn}{white} XRP{res}{end}")
                        print(f" {red}# {white}Balance: {green}{v['total_bal']}{white} XRP{res}{end}")
                        print(f" {red}# {white}Highest Reward: {green}{best_claim} {white}XRP / Streak: [ {yellow}{self.streak[self.email]}{res} ]{end}")
                        if self.show_emails:
                            print(f" {red}# {white}Account: {yellow}{self.email}{res}{end}")
                        msg_line()
                    else:
                        print(r)
                    return
        
        def history_wd(opt=None):
            carousel_msg("Go to history withdraw section")
            while True:
                r = self.curl('GET', f"https://{host}/withdraw.php")
                if r:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    history = soup.select('.welcome-card table.text-center tbody tr')
                    if history:
                        if opt and opt == 'tx':
                            tx_hash = history[0].find('a', class_='text-primary')
                            tx_hash = tx_hash['href'] if tx_hash else None
                            return tx_hash
                        if any(val is None for val in history):
                            continue
                        for i in range(len(history)):
                            tx_hash = history[i].find('a', class_='text-primary')
                            tx_hash = tx_hash['href']
        
                            amount = history[i].find('td', translate='no')
                            amount = amount.get_text(strip=True)
        
                            status = history[i].find('span', style='color: #38cf89')
                            status = status.get_text(strip=True)
        
                            date = history[i].find('div', style='width: 150px;')
                            date = date.get_text(strip=True)
                            if opt and opt == 'last wd' and i == (len(history)-1):
                                try:
                                    return datetime.strptime(date, "%d/%m/%Y %H:%M")
                                except Exception:
                                    return None
                    else:
                        carousel_msg("Not withdrawal history found.")
                        return 'first wd'
                else:
                    carousel_msg("Error getting withdrawal history.")
                return None

        def withdraw():
            nonlocal total_withdraw
            nonlocal total_requests_wd
            carousel_msg("Go to withdraw section")
            while True:
                r = self.curl('GET', f"https://{host}/withdraw.php")
                if r:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    amount = soup.find('input', {'id': 'withdraw_amount'})['value']
                    carousel_msg("Checking if amount >= min withdrawl")
                    try:
                        amount_wd = float(amount)
                        if amount_wd < 0.01:
                            carousel_msg("Wd amount is very low")
                            break
                    except Exception:
                        carousel_msg("Error read amount")
                        break
                    carousel_msg("Checking date last withdrawal")
                    last_date_wd = history_wd(opt='last wd')
                    if last_date_wd:
                        if last_date_wd != 'first wd':
                            local_time = datetime.now()
                            local_time_utc = local_time.astimezone(timezone.utc)
                            local_time_utc = local_time_utc.replace(tzinfo=None)
                        if last_date_wd == 'first wd' or isinstance(last_date_wd, datetime) and local_time_utc >= last_date_wd:
                            if amount:
                                payload = {'amount': str(amount), 'wallet': str(self.wallet), 'tag': str(self.tag)}
                                payload = json.dumps(payload)
                                r =  self.curl('POST', f"https://{host}/api.php?act=withdraw", payload)
                                if r:
                                    r = json.loads(r.text)
                                    if 'message' in r:
                                        carousel_msg(r['message'])
                                        if 'insufficient balance' in r['message'] or 'withdrawal time is too long' in r['message']:
                                            break
                                        elif 'successfully' in r['message']:
                                            total_withdraw += amount_wd
                                            self.total_balance -= amount_wd
                                            total_requests_wd += 1
                                            carousel_msg("Waiting for website generated transsaction")
                                            wait(randint(10,15))
                                            tx_hash = history_wd(opt='tx')
                                            amount = "{:.8f}".format(float(amount))
                                            msg_action("WITHDRAW")
                                            wd_status = 'Completed' if tx_hash else 'Pending'
                                            print(f" {red}# {white}Status: {yellow}{wd_status}{end}")
                                            print(f" {red}# {white}Amount: {green}{amount}{white} XRP{res}{end}")
                                            print(f" {red}# {white}Address XRP: {yellow}{self.wallet}{res}{end}")
                                            print(f" {red}# {white}Tag Address XRP: {white}{self.tag}{res}{end}")
                                            if self.show_emails:
                                                print(f" {red}# {white}Account: {yellow}{self.email}{res}{end}")
                                            msg_line()
                                            break
                                        else:
                                            print(r)
                                    else:
                                        print(r)
                                else:
                                    carousel_msg("Error making withdraw")
                            else:
                                carousel_msg("Error getting max amount withdrawal now, try later moment")
                        else:
                            carousel_msg("You still cannot make a new withdrawal ")
                    break
        
        def login():
            self.sessions[self.email].close()
            while True:
                carousel_msg("Login proccessing...")
                url = f"https://{host}/api.php?act=login"
                payload = {
                    "email": self.email,
                    "password": self.password
                }
                payload = json.dumps(payload)
                r = self.curl('POST', url, payload)
                if r:
                    r = json.loads(r.text)
                    if 'message' in r and 'Login successful' in r['message']:
                        carousel_msg("Successfully Login")
                        return
                    carousel_msg("Login failed")
                wait(10)
        
        total_collected_faucet = 0
        total_collected_lottery = 0
        
        total_claims_faucet = 0
        total_claims_lottery = 0
        
        total_withdraw = 0
        total_requests_wd = 0
        
        self.total_balance = 0
        
        while True:
            time_claim = self.data['Claim Time'] if self.data['Claim Time'] is not None and self.data['Claim Time'].isdigit() else 2
            if float(time_claim) < 0.1:
                time_claim = 0.1
            wait(int(time_claim) * 60)
            for i in range(len(self.data['Data'])):
                self.email = self.data['Data'][i]['Email']
                self.password = self.data['Data'][i]['Password']
                self.wallet = self.data['Data'][i]['XRP']['Address']
                self.tag = self.data['Data'][i]['XRP']['Tag']
                self.check_lottery = self.data['Data'][i]['Check Lottery']
                if len(str(self.data['Data'][i]['Withdraw Time'])) >= 18:
                    try:
                        self.withdraw_time = datetime.strptime(self.data['Data'][i]['Withdraw Time'], "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        self.withdraw_time = None
                else:
                    self.withdraw_time = None

                if self.email not in self.sessions:
                    self.sessions[self.email] = requests.Session()
                if self.email not in self.best_claim:
                    self.best_claim[self.email] = 0
                if self.email not in self.streak:
                    self.streak[self.email] = 0
                
                if not self.sessions[self.email].cookies:
                    login()
                faucet()
                if self.check_lottery == "on":
                    lottery()
                if self.autowd and self.wallet and len(self.wallet) > 10 and self.tag and len(self.tag) > 3:
                    current_time = datetime.now()
                    if self.withdraw_time:
                        if current_time >= self.withdraw_time:
                            withdraw()
                else:
                    if self.autowd:
                        if self.wallet.isspace() or self.wallet == '':
                            carousel_msg(f"Wallet for account {self.email} not found")
                        if self.tag.isspace() or self.tag == '':
                            carousel_msg(f"Tag of wallet XRP for account {self.email} not found")
                        if not isinstance(self.withdraw_time, datetime):
                            carousel_msg("Time withdraw not found, automatic update after updated config again")
                
                if i == len(self.data['Data'])-1:
                    carousel_msg("Success run task in alls accounts")
                    if self.show_information:
                        line = f"{celeste}="
                        collected_faucet = "{:.8f}".format(total_collected_faucet)
                        collected_lottery = "{:.8f}".format(total_collected_lottery)
                        wd_lottery = "{:.8f}".format(total_withdraw)
                        total_balance = "{:.8f}".format(self.total_balance)
                        print(line * 17 + "[ INFORMATION ] " + line * 17)
                        print(f" {yellow}Emails{red}: {white}[ {len(self.data['Data'])} ]{res}")
                        print(f" {yellow}Balance{red}: {white} {total_balance} XRP{res}")
                        print(f" {yellow}Faucet{red}: {white} {collected_faucet} XRP   -   ( {total_claims_faucet} ){res}")
                        print(f" {yellow}Lottery{red}: {white} {collected_lottery} XRP   -   ( {total_claims_lottery} ){res}")
                        print(f" {yellow}Withdrawal{red}: {white} {wd_lottery} XRP   -   ( {total_requests_wd} ){res}")
                        print(line * 50)
                        msg_line()
                    break
                else:
                    carousel_msg("Switching account")
                    sleep(randint(1,2))
            
            self.update_config(re_loading=True)
            self.total_balance = 0
    
    def update_config(self, re_loading=None):
        
        def fill_key(keyword):
            key = ''
            if keyword == 'Check Lottery':
                key = input(f"{yellow}{keyword}? (y/n):{res} ").lower()
                while key not in ["y", "n"]:
                    key = input(f"{yellow}{keyword}? (y/n):{res} ").lower()
                key = "on" if key == 'y' else "off"
            else:
                while len(key) < 5:
                    key = input(f"{yellow}{keyword}{red}:{res} ")
            return key.strip()
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            carousel_msg("Not found config file")
            if re_loading:
                carousel_msg("Skip update config")
                return
            else:
                banner()
                carousel_msg("Creatin new config file")
                config = {
                    "Claim Time": "",
                    "Auto Wd": {"Toggle": "off", "Every Day": "off"},
                    "Data": []
                }
        except (ValueError, TypeError):
            carousel_msg("Error reading config file")
            if re_loading:
                carousel_msg("Skip update config")
                return
            exit()
        
        if not re_loading:
            
            while True:
                print(f"{lila}(press Enter to skip){res}")
                email = input(f"{yellow}Email{red}:{res} ")
                if email == '' or email.isspace():
                    banner()
                    break
                elif email and '@' in email:
                    email_exist = any(entry['Email'] == email for entry in config['Data']) if config['Data'] else False
                    if not email_exist:
                        new_entry = {'Email': email}
                        new_entry['Password'] = fill_key('Password')
                        new_entry['XRP'] = {}
                        new_entry['XRP']['Address'] = fill_key('Address XRP')
                        new_entry['XRP']['Tag'] = fill_key('Tag')
                        new_entry['Check Lottery'] = fill_key('Check Lottery')
                        new_entry['Withdraw Time'] = ''
                        config['Data'].append(new_entry)
                        print()
                        msg_line()
                        print()
                    else:
                        carousel_msg("Already exist email")
                else:
                    carousel_msg("Email not valid")
                
            if not config['Data']:
                print(f"{red}Not found accounts data")
                exit()
            
            auto_wd_choice = input(f"{yellow}Do you want to activate 'auto withdraw'? (y/n):{res} ").lower()
            while auto_wd_choice not in ["y", "n"]:
                print("Please enter a valid choice ('y' or 'n').")
                auto_wd_choice = input(f"\n{yellow}Do you want to activate 'auto withdraw'? (y/n):{res} ").lower()
            config['Auto Wd']['Toggle'] = "on" if auto_wd_choice == "y" else "off"
    
            if auto_wd_choice == "y":
                auto_wd_every_day = input(f"\n{yellow}Do you want to activate 'auto withdraw one account every day'? (y/n):{res} ").lower()
                while auto_wd_every_day not in ["y", "n"]:
                    print("Please enter a valid choice ('y' or 'n').")
                    auto_wd_every_day = input(f"\n{yellow}Do you want to activate 'auto withdraw one account every day'? (y/n):{res} ").lower()
                config['Auto Wd']['Every Day'] = "on" if auto_wd_every_day == "y" else "off"
                self.auto_wd = True
            
            while not config['Claim Time'].isdigit():
                config['Claim Time'] = input(f"\n{yellow}Enter Claim Time in minutes:{res} ").lower()
        
            banner()
        
        carousel_msg("Updating config")
        
        last_time = datetime.now()
        add_minutes = 24 * 60 if config['Auto Wd']['Every Day'] == 'on' else 60
        
        for i in range(len(config['Data'])):
            entry = config['Data'][i]
            last_time += timedelta(minutes=add_minutes)
            if i == 0:
                if isinstance(entry['Withdraw Time'], datetime):
                    last_time = entry['Withdraw Time']
            config['Data'][i]['Withdraw Time'] = str(last_time.replace(microsecond=0))
        
        write_json(config)

        self.data = config

        if not re_loading:
            banner()
        
        carousel_msg("Success updated config")
    
    def config(self):
        
        def get_valid_user_agent():
            user_agent = ''
            while len(user_agent) < 10 or 'Mozilla' not in user_agent:
                user_agent = input(f"{yellow}Enter User-Agent{red}:{res} ")
                banner()
            return user_agent.strip()
        
        try:
            with open('User_Agent', 'r') as f:
                user_agent = f.read().strip()
        except FileNotFoundError:
            user_agent = get_valid_user_agent()
            with open('User_Agent', 'w') as f:
                    f.write(user_agent)
        
        self.user_agent = user_agent
        
        banner()
        
        opt = ''
        while opt not in ["y", "n"]:
            opt = input(f"{celeste}Show Emails? (y/n):{res} ").lower()
        self.show_emails = True if opt == 'y' else False
        
        opt = ''
        while opt not in ["y", "n"]:
            opt = input(f"{celeste}Show Information? (y/n):{res} ").lower()
        self.show_information = True if opt == 'y' else False
        
        banner()
        
        self.update_config(re_loading=False)
        
        banner()

banner()

if __name__ == "__main__":
    bot = Bot()
    bot.captcha = {
    'balance': {},
    'count': {
        'spent': 0,
        'failed': 0,
        'attemps': 0,
        't_attemps': 0
    }
}
    bot.sessions = {}
    bot.best_claim = {}
    bot.streak = {}
    bot.autowd = False
    bot.show_emails = False
    bot.show_information = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "-d":
            bot.remove_account()
    else:
        bot.config()
        bot.mainbot()
