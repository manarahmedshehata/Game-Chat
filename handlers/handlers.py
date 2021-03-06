from tornado import gen,web
from tornado import websocket
import json,os,time
import pymongo
from pprint import pprint
from bson.objectid import ObjectId #deal with object pymongo
from bson.code import Code
from bson import ObjectId
import uuid
import tornado.ioloop
import tornado.web

templateurl = "../template/"


class BaseHandler(web.RequestHandler):
	def get_current_user(self):
		user_id = self.get_secure_cookie("id")
		if not user_id: return None
		user_name = str(self.get_secure_cookie("name"),'utf-8')
		user_status = str(self.get_secure_cookie("status"),'utf-8')
		user = {
			'user':str(user_id,'utf-8'),
			'name':user_name,
			'status':user_status
		}
		print("in current user")
		print(type(user_id))

		return user

class PrivateChatHandler(websocket.WebSocketHandler,BaseHandler):
	@web.authenticated
	def post(self):
		fname=self.get_argument("fnamee")
		print("pchat")
		pprint(self.current_user)
		count = 0
		history_content = True

		try:
			filePath = "chatHistory/people/" + self.current_user['name'] + "/" + fname + ".txt"
			f = open(filePath)
		except OSError as e:
			f = open(filePath, 'w')

		try:
			for line in f:
				count = count + 1
		except OSError as e:
			count = 0
			history_content = False

		f.seek(0);

		pprint(f)

		self.render(templateurl+"privatechat.html",user_name=self.current_user['name'], status=self.current_user['status'], file_content=history_content, id_last_index=0, filename=f, username="1", friend_name=fname, posts_no=count,user_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")

class GroupChatHandler(websocket.WebSocketHandler,BaseHandler):
	@web.authenticated

	def post(self):
		pprint(self.current_user)
		gname=self.get_argument("gname")
		gid=self.get_argument("gid")

		count = 0
		history_content = True

		try:
			filePath = "chatHistory/groups/" + gid + ".txt"
			f = open(filePath)

		except OSError as e:
			f = open(filePath, 'w+')

		members = []

		try:
			for line in f:
				count = count + 1
		except OSError as e:
			count = 0
			history_content = False

		f.seek(0);



		#get groups user with name, id and status
		db = self.application.database
		gusers=db.users.find({"groups_id":ObjectId(gid)},{"name":1,"status"	:1})
		gusr=[]
		for gu in gusers:
			gusr.append(gu)
			members.append(gu["name"])
			# pprint(members)

		pprint(gusr)


		self.render(templateurl+"groupchat.html", group_members=members, file_content=history_content, user_name=self.current_user['name'], status=self.current_user['status'], id_last_index=0, group_name=gname,gidd=gid,gusr=gusr, posts_no=count, chat_members=["2","3","4"], filename=f, username="1", group_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")

class HomeHandler(BaseHandler):
	@web.authenticated
	def get(self):
		print("++++++++++++++++++++++++++++++++")
		print(self.current_user)
		db = self.application.database
		#GET MSG IF EXIST
		requests=[]
		msgs=db.users.find({"_id":ObjectId(self.current_user['user'])},{"msgs":1,"_id":0})
		for msg in msgs:
			requests=msg["msgs"]

		# GET PUBLIC FIGURE and PARTY MAN
		pubicfigure_condition=[{"$project":{"name":1,"_id":0,"count":{"$size":"$friendId"}}},{"$sort":{'count':-1}},{"$limit":5}]
		partyman_condition=[{"$project":{"name":1,"_id":0,"count":{"$size":"$groups_id"}}},{"$sort":{'count':-1}},{"$limit":5}]

		pubicfigure_name=[]
		pubicfigure=db.users.aggregate(pubicfigure_condition)
		for u in pubicfigure:
			pubicfigure_name.append(u['name'])

		partymans=[]
		partyman=db.users.aggregate(partyman_condition)
		for party in partyman:
			partymans.append(party['name'])

		pprint(pubicfigure_name)
		pprint(partymans)

		# Best friend and chatty man
		privateChatDir = "chatHistory/people/"
		pprint(privateChatDir)
		currentUserDir = privateChatDir + self.current_user['name'] + "/"
		pprint(currentUserDir)
		groupChatDir = "chatHistory/groups"


		# Best Friend List
		friends_dict = {}


		for filename in os.listdir(currentUserDir):

			pprint("inside for")
			fname = currentUserDir + filename
			with open(fname) as f:
				friends_dict[filename.replace(".txt","")] = len(f.readlines())

		pprint(friends_dict)
		bfriend = sorted(friends_dict, key=friends_dict.get, reverse=True)


		pprint("lol")
		pprint(bfriend)

		# Chatty One List
		chatty_dict = {}
		chatty_list = []

		subdirs = [x[0] for x in os.walk(privateChatDir)]
		for subdir in subdirs:

			chatty_dict[subdir] = 0
			files = os.walk(subdir).__next__()[2]

			if (len(files) > 0):
				for file in files:
					chatty_dict[subdir] += 1



		chatty_list = sorted(chatty_dict, key=chatty_dict.get, reverse=True)

		x = 0

		while x < len(chatty_list):
			chatty_list[x] = chatty_list[x].replace(privateChatDir,"")
			x += 1



		length = len(chatty_list) - 2
		chatty_list = chatty_list[:length]

		self.render(templateurl+"home.html", chatty_ones=chatty_list[:5], best_friends=bfriend[:5], user_name=self.current_user['name'], status=self.current_user['status'], rquests=requests, pubicfigure_name=pubicfigure_name, partymans=partymans,  group_name="Eqraa", posts_no="2000",group_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")

#handling signup in db and cookies (registeration and login)
class SignupHandler(BaseHandler):

	def post(self):
		#insert user info
		db = self.application.database
		username=self.get_argument("signupname")
		email=self.get_argument("signupemail")
		pwd=self.get_argument("signuppwd")
		new_user = {"name":username,"password":pwd,"email":email,"status":'on','groups_id':[],'friendId':[],'msgs':[]}
		try:
			user_id = db.users.insert(new_user)
			self.set_secure_cookie("id",str(user_id))
			self.set_secure_cookie("name", username)
			self.set_secure_cookie("status", 'on')
			# create user chat history directory
			directory = "chatHistory/people/" + username
			if not os.path.exists(directory):
				os.makedirs(directory)

			self.redirect("/home")
		except pymongo.errors.DuplicateKeyError:
			# error in signup if duplicated name
			self.redirect("/?sp=1")


class GroupsHandler(BaseHandler):
	@web.authenticated
	def get(self):
		groupslist_in=[]
		groupslist_notin=[]
		owner=[]
		db = self.application.database
		user_id =ObjectId(self.current_user['user'])


		groups=db.users.find({'_id':user_id},{'groups_id':1,'_id':0})
		for g in groups:
			for group in g["groups_id"]:
				name=db.groups.find({'_id':group})

				for n in name:
					pprint(n)
					groupslist_in.append({'_id':n['_id'],'name':n['name']})
					if n['owner'] == user_id:
						owner.append(n['_id'])
			notin_name=db.groups.find({'_id':{'$nin':g["groups_id"]}},{'name':1})
			for nin in notin_name:
				groupslist_notin.append(nin)
		pprint(owner)


		self.render(templateurl+"groups.html", user_name=self.current_user['name'], status=self.current_user['status'], groups_list=groupslist_in,nin_grouplist=groupslist_notin, owner=owner, posts_no="2000",group_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")

class PeopleHandler(BaseHandler):
	@web.authenticated
	def get(self):
		db = self.application.database
		userName =self.current_user['name']
		friends_list_in=[]
		friends_list_notin=[]
		db = self.application.database
		user_id =self.current_user['name']
		friends=db.users.find({'name':user_id},{'friendId':1,'_id':0})
		for f in friends:
			for friend in f["friendId"]:
				name=db.users.find({'_id':friend},{'name':1})
				for n in name:
					friends_list_in.append(n)
			notin_name=db.users.find({"$and":[{'_id':{'$nin':f["friendId"]}},{"name":{"$ne":user_id}}]},{'name':1})
			for nin in notin_name:
				friends_list_notin.append(nin)
		self.render(templateurl+"people.html", user_name=self.current_user['name'], status=self.current_user['status'], friend_nin_list=friends_list_notin,friend_in_list=friends_list_in, posts_no="2000",group_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")
# Handler to Create Group
class CreateGroupHandler(BaseHandler):
	@web.authenticated
	def get(self):
		userID = str(self.get_secure_cookie("id"),'utf-8')
		self.render(templateurl+"creategroup.html")
	@web.authenticated
	def post(self):

		db = self.application.database
		groupname = self.get_argument("groupname")
		owner=ObjectId(self.current_user['user'])
		group_id = db.groups.insert({'name':groupname,'owner':owner})
		db.users.update({"_id":owner},{"$push":{'groups_id':group_id}})

		filePath = "chatHistory/groups/" + str(group_id) + ".txt"
		f = open(filePath, 'w+')

		self.redirect("/groups")



		self.render(templateurl+"people.html", user_name=self.current_user['name'], status=self.current_user['status'], group_name="Eqraa", posts_no="2000",group_avatar="http://cs625730.vk.me/v625730358/1126a/qEjM1AnybRA.jpg")

class AddingHandler(BaseHandler):
	@web.authenticated
	def post(self):
		uid = ObjectId(self.current_user['user'])
		fgadd=self.get_argument("add")
		addid=ObjectId(self.get_argument("join"))
		#open connection with database
		db = self.application.database
		if fgadd== "friend":

			add = "friendId"
		elif fgadd== "group":
			add = "groups_id"
		#__TODO__Exceptions handling
		print("adding")
		print(fgadd)
		print(addid)
		# 	print("duplicates")
		db.users.update({"_id":uid},{"$push":{add:addid}})
		#add userid at friend list also update user msg field -->another user add u
		db.users.update({"_id":addid},{"$push":{add:uid,"msgs":self.current_user['name']}})

		if fgadd== "friend":
			self.redirect("/people")
		elif fgadd== "group":
			self.redirect("/groups")

class BlockHandler(BaseHandler):
	@web.authenticated
	def post(self):

		fgblock=self.get_argument("block")
		removeid=ObjectId(self.get_argument("remove"))
		db = self.application.database

		uid=ObjectId(self.current_user['user'])
		print(fgblock)
		print(removeid)
		if fgblock== "friend":
			block = "friendId"
		elif fgblock== "group":
			block = "groups_id"
		update=db.users.update_one({"_id":uid},{"$pull":{block:removeid}})
		update=db.users.update_one({"_id":removeid},{"$pull":{block:uid}})
		if fgblock== "friend":
			self.redirect("/people")
		elif fgblock== "group":
			self.redirect("/groups")

		pprint(update.modified_count)



#handling websocket
clients = []
class WSHandler(websocket.WebSocketHandler,BaseHandler):

	def open(self):
		if self.current_user:
			print("ws")
			client={'id':self.current_user['user'],'info':self,'name':self.current_user['name']}
			clients.append(client)
		pprint(clients)
	def on_message(self,message):
		pprint(clients)
		msg=json.loads(message)
		pprint(msg)

		# Private Chats
		# save new message to current user's chat history and friend's chat history
		privateChatDir = "chatHistory/people/"

		saved_message = self.current_user['name'] + "#" + msg['msg'] + '\n'

		subdir = privateChatDir + msg['fname']

		if not os.path.exists(subdir):
			os.makedirs(subdir)

		my_file_path = "chatHistory/people/" + self.current_user['name'] + "/" + msg['fname'] + ".txt"
		friend_file_path = "chatHistory/people/" + msg['fname'] + "/" + self.current_user['name'] + ".txt"

		with open(my_file_path, "a") as myfile:
			myfile.write(saved_message)

		with open(friend_file_path, "a") as friendfile:
			friendfile.write(saved_message)

		for c in clients:
				if c['name'] in [msg['fname'],msg['myname']]:
					msgsent={'name':msg['fname'],'msg':msg['msg']}
					pprint("--------------------------")
					pprint(msgsent)
					c['info'].write_message(json.dumps(msgsent))
	def on_close(self):
		for u in clients:
			if self == u['info']:
				clients.remove(u)





groups = []
class GWSHandler(websocket.WebSocketHandler,BaseHandler):
	def open(self):
		# print(self.current_user)
		if self.current_user:
		 	print('gws')

	def on_message(self,message):
		print("----------------ONMSG--------------")
		msg=json.loads(message)
		pprint(msg)
		if not "msg" in msg:
			# Start group msg
			# __TODO add user to group id
			if groups ==[]:
				group={'gid':msg['gid'],'users_info':[self]}
				groups.append(group)
			else:
				group_modified=False
				for g in groups:
					print("for")
					if g['gid'] == msg['gid']:
						print("if")
						g["users_info"].append(self)
						group_modified=True
				print("modified",group_modified)
				if(not group_modified):
					group={'gid':msg['gid'],'users_info':[self]}
					groups.append(group)
			print('=====start')
			pprint(groups)
		else:
			pprint("HELLO WORLD")
			print('=====msg')
			pprint(groups)
			pprint(msg)

			group_file_path = "chatHistory/groups/" + msg['gid'] + ".txt"
			pprint(group_file_path)
			saved_message = msg['sender'] + "#" + msg['msg'] + '\n'

			with open(group_file_path,"a") as groupfile:
				groupfile.write(saved_message)

			for g in groups:
				if g['gid'] == msg['gid']:
					print(msg['gid'])
					print('hi')
					#db = self.application.databas
					for user in g['users_info']:
						msgsent={'sender':msg['sender'],'msg':msg['msg']}
						pprint("--------------------------")
						pprint(msgsent)
						user.write_message(json.dumps(msgsent))




	def on_close(self):
		# print("(===========close=============)")
		pprint(groups)
		for g in groups:
			for user in g['users_info']:
				if user == self:
					g['users_info'].remove(user)
		print("(===========close=============)")
		pprint(groups)








##########################################
class LogoutHandler(BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("id")
		self.redirect("/")

class StatusChangeHandler(BaseHandler):
	@web.authenticated
	def get(self):
		db=self.application.database
		uid=ObjectId(self.current_user['user'])
		status=self.get_argument('status')
		print("/////////////////////////")
		print("test chang status")
		print(type(status))
		print("//////-///////////////////")
		if status=="true":
			#update "on" in user db
			#and update cookies status
			stat='on'
		elif status=="false":
			stat='off'
		print(uid)
		update=db.users.update({"_id":uid},{"$set":{'status':stat}})

		self.set_secure_cookie("status", stat)

class RmmsgsHandler(BaseHandler):
	@web.authenticated
	def get(self):
		db=self.application.database
		uid=ObjectId(self.current_user['user'])
		update=db.users.update({"_id":uid},{"$set":{'msgs':[]}})
