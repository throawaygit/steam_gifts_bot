#!/usr/bin/python3
import time
import requests
import random
from bs4 import BeautifulSoup
import os
import json
import platform
os.chdir("/home/vodka/scripts/python/steam_gifts/")
if platform.system()=="Linux":
	import notify2
	from gi.repository.GdkPixbuf import Pixbuf
	pb=Pixbuf.new_from_file("icon.png")
import sys
from subprocess import call
import datetime
if platform.system()=="Windows":
	os.system("Chcp 65001")

def get_cookies():
	"""read cookies from files"""
	cookie={}
	exec(open("cookie.txt").read(), None, cookie)
	return cookie
	
def what_search_func():
	"""read search list from file"""
	what_search={}
	exec(open("search.txt").read(), None, what_search)
	return what_search

def get_requests(cookie, req_type):
	"""get first page"""
	global chose
	if req_type=="wishlist":
		print("work with wishlist")
		page_number=1
		need_next=True
		while need_next:
			try:
				r=requests.get("http://www.steamgifts.com/giveaways/search?page="+str(page_number)+"&type=wishlist", cookies=cookie, headers=headers)
			except:
				print("Site not avaliable")
				time.sleep(300)
				chose=0
				break
			get_game_links(r)
			need_next=get_next_page(r)
			page_number+=1
	elif req_type=="search":
		print("work with search list")
		for current_search in what_search.values():
			print("Search giveaways with "+str(current_search))
			page_number=1
			need_next=True
			while need_next:
				try:
					r=requests.get("http://www.steamgifts.com/giveaways/search?page="+str(page_number)+"&q="+str(current_search), cookies=cookie, headers=headers)
					get_game_links(r)
					need_next=get_next_page(r)
					page_number+=1	
				except:
					print("Site not avaliable")
					chose=0
					time.sleep(300)	
					break
			time.sleep(random.randint(14,93))
	elif req_type=="enteredlist":
		print("get entered list")
		entered_list=[]
		page_number=1
		while page_number<4:
			try:
				r=requests.get("http://www.steamgifts.com/giveaways/entered/search?page="+str(page_number), cookies=cookie, headers=headers)
				entered_list.extend(get_entered_links(r))
				page_number+=1
			except:
				print("Site not avaliable")
				chose=0
				time.sleep(300)	
				break
		print("entered list return...")
		return entered_list
	elif req_type=="someone":
		print("work with random")
		r=requests.get("http://www.steamgifts.com/", cookies=cookie, headers=headers)
		get_game_links(r)
	elif req_type=="coins_check":
		try:
			r=requests.get("http://www.steamgifts.com/giveaways/search?type=wishlist", cookies=cookie, headers=headers)
		except:
			print("Site not avaliable...")
			chose=0
			time.sleep(300)
	return r

def get_game_links(requests_result):
	"""call enter_geaways and extract link"""
	soup=BeautifulSoup(requests_result.text)
	link=soup.find_all(class_="giveaway__heading__name")
	for get_link in link:
		geaway_link=get_link.get("href")
		if not geaway_link in entered_url:
			print(geaway_link)
			entered_url.append(geaway_link)
			geaway_link="http://www.steamgifts.com/" + geaway_link
			if enter_geaway(geaway_link):
				break

def enter_geaway(geaway_link):
	"""enter to geaways"""
	global i_want_to_sleep
	global chose
	try:
		r=requests.get(geaway_link, cookies=cookie, headers=headers)
		print(r.status_code)
	except:
		print("Site not avaliable...")
		chose=0
		time.sleep(300)
		return True
	soup_enter=BeautifulSoup(r.text)
	try:
		game=soup_enter.title.string
	except:
		print("No name")
		game="Unknown game"
	link=soup_enter.find(class_="sidebar sidebar--wide").form
	if link!=None:
		link=link.find_all("input")
		params={"xsrf_token": link[0].get("value"), "do": "entry_insert", "code": link[2].get("value")}
		try:
			r=requests.post("http://www.steamgifts.com/ajax.php", data=params, cookies=cookie, headers=headers)
		except:
			print("Site not avaliable...")
			chose=0
			time.sleep(300)	
			return True
		extract_coins=json.loads(r.text)
		print(r.text)
		if extract_coins["type"]=="success":
			coins=get_coins(get_requests(cookie, "coins_check"))
			print("Game: "+game+". Coins: "+coins)
			set_notify("Бот вступил в раздачу с игрой", game+". Осталось монет: "+extract_coins["points"])
			time.sleep(random.randint(1,120))
			return False
		elif extract_coins["msg"]=="Not Enough Points":
			coins=get_coins(get_requests(cookie, "coins_check"))
			chose=0
			i_want_to_sleep=True
			print("Недостаточно монет...", geaway_link)
			return True
	else:
		link=soup_enter.find(class_="sidebar__error is-disabled")
		if link!=None and link.get_text()==" Not Enough Points":
			print("Недостаточно монет для вступления в раздачу...", geaway_link)
			time.sleep(random.randint(5,60))
			if int(get_coins(get_requests(cookie, "coins_check")))<10:
				chose=0
				i_want_to_sleep=True
				return True
		else:
			link=soup_enter.select("div.featured__column span")
			if link!=None:
				print ("Раздача уже закончилась, бот не упел в неё вступить ", geaway_link)
				print ("Она закончилась ", link[0].text)
				time.sleep(random.randint(5,60))
				return False
			else:
				print ("Критическая ошибка!")
				do_beep("critical")
				print (link)
				return False
		return False

def get_entered_links(requests_result):
	entered_list=[]
	soup=BeautifulSoup(requests_result.text)
	links=soup.find_all(class_="table__row-inner-wrap")
	for get_link in links:
		url=get_link.find(class_="table__column__heading").get("href")
		check_geaways_end=get_link.find(class_="table__remove-default is-clickable")
		if check_geaways_end!=None:
			entered_list.append(url)
	return entered_list

def get_coins(requests_result):
	"""how many coins"""
	soup=BeautifulSoup(requests_result.text)
	coins=soup.find(class_="nav__points").string
	return coins

def get_next_page(requests):
	"""Next page exists?"""
	if requests.text.find("Next")!=-1:
		return True
	else:
		return False
		
def set_notify(head, text):
	if platform.system()!="Linux":
		return 0
	notify2.init('Steam_gifts_bot')
	n = notify2.Notification(head, text)
	n.set_timeout(15000)
	n.set_icon_from_pixbuf(pb)
	n.show()

def work_with_win_file(need_write, count):
	"""Function for read drom file or write to file won.txt"""
	with open('won.txt', 'r+') as read_from_file:
		if not need_write:
			count=read_from_file.read()
			read_from_file.close()
			return count
		elif need_write:
			read_from_file.seek(0)
			read_from_file.write(str(count))
			read_from_file.close()

def check_won(count):
	"""Check new won giveaway"""
	try:
		r=requests.get("http://www.steamgifts.com/giveaways/search?type=wishlist", cookies=cookie, headers=headers)
		soup=BeautifulSoup(r.text).find(class_="nav__notification").string
	except:
		print ("You not win giveaways...")
		work_with_win_file(True, 0)
		return 0
	if int(count)<int(soup):
		do_beep("won")
		set_notify("Бот выиграл в раздаче!", "Заберите свой приз на сайте.")
		work_with_win_file(True, soup)
		return soup
	elif int(count)>int(soup):
		work_with_win_file(True, soup)
		return soup
	return count

def do_beep(reason):
	if datetime.datetime.now().time().hour>9 and datetime.datetime.now().time().hour<22 and platform.system()=="Linux":
		if reason=="coockie_exept":
			call(["beep", "-l 2000",  "-f 1900", "-r 3"])
		elif reason=="critical":
			call(["beep", "-l 1000", "-r 10", "-f 1900" ])
		elif reason=="won":
			os.system("./win.sh")

print("I am started...")
chose=0
random.seed(os.urandom)
headers = {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'}
cookie=get_cookies()
try:
	r=requests.get("http://www.steamgifts.com/giveaways/search?type=wishlist", cookies=cookie, headers=headers)
except:
	set_notify("Куки устарели...", "Необходимо обновить куки")
	do_beep("coockie_exept")
	sys.exit(1)
what_search=what_search_func()
coins=get_coins(get_requests(cookie, "coins_check"))
entered_url=get_requests(cookie, "enteredlist")
func_list=("wishlist", "search", "someone")
won_count=work_with_win_file(False, 0)
set_notify("Бот начал свою работу", "Монет всего: " + str(coins))

i_want_to_sleep=False

while True:
	i_want_to_sleep=False
	requests_result=get_requests(cookie, func_list[chose])
	chose+=1
	if i_want_to_sleep:
		won_count=check_won(won_count)
		sleep_time=random.randint(1800,3600)
		coins=get_coins(get_requests(cookie, "coins_check"))
		set_notify("Монет осталось мало...", "А точнее: "+coins+". Глубокий сон на "+str(sleep_time//60)+" мин.")
		print("Монет осталось мало: "+ str(coins)+". Я спать на "+str(sleep_time//60)+" мин.")
		time.sleep(sleep_time)
		chose=0
	if chose==3:
		won_count=check_won(won_count)
		sleep_time=random.randint(1800,3600)
		coins=get_coins(get_requests(cookie, "coins_check"))
		set_notify("Я вступил во все раздачи...", "И ухожу в сон на "+str(sleep_time//60)+" мин.")
		print("Монет осталось: "+ str(coins)+". Я спать на "+str(sleep_time//60)+" мин.")
		time.sleep(sleep_time)
		chose=0
