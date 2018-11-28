import mysql.connector
import re
from db_queries import *
from isInstalled import *
import datetime

dbConfigLocal = {"host":"localhost","port":"3306","user":"root","passwd":""}
dbConfigQC = {"host":"localhost","port":"3306","user":"root","passwd":""}
dbConfigUAT = {"host":"localhost","port":"3306","user":"root","passwd":""}
dbConfigStaging = {"host":"localhost","port":"3306","user":"root","passwd":""}
dbConfigProd = {"host":"localhost","port":"3306","user":"root","passwd":""}

dbConfig = dbConfigLocal
dbConn = ""

def connDB():
	global dbConn
	if dbConn == "":
		dbConn = mysql.connector.connect(
			host=dbConfig["host"],
			port=dbConfig["port"],
			user=dbConfig["user"],
			passwd=dbConfig["passwd"]
		)
	createDB()

def connDB1(db):
	global dbConn
	if dbConn != "":
		dbConn.close()
	dbConn = mysql.connector.connect(
		host=dbConfig["host"],
		port=dbConfig["port"],
		user=dbConfig["user"],
		passwd=dbConfig["passwd"],
		database=db
	)

def createDB():
	global dbConn
	if dbConn != "":
		cursor = dbConn.cursor()
		cursor.execute(dbQuery)
		cursor.close()
		dbConn.close()
		dbConn = ""
	connDB1(dbName)
	if dbConn != "":
		cursor = dbConn.cursor()
		cursor.execute(basic_query)
		cursor.execute(token_query)
		cursor.execute(login_history_query)
		cursor.execute(email_filter_query)
		cursor.execute(mail_details_query)
		cursor.execute(drive_folders_query)
		# cursor.execute(insert_basic_folder_data_query)
		cursor.close()
		dbConn.close()
		dbConn = ""
		f = open("config/isInstalled.py", "w")
		f.write("installed = '1'")
		f.close()
		# print("Done")

def insertData(dataSet,tableName):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	keySet = dataSet.keys()
	valueDataSet = ""
	for i in range(len(keySet)):
		if i == (len(keySet)-1):
			valueDataSet = valueDataSet + "'" + removeTags(str(dataSet[keySet[i]]).replace("'","\\'"))+"'"
		else:
			valueDataSet = valueDataSet + "'" + removeTags(str(dataSet[keySet[i]]).replace("'","\\'"))+"',"

	dummySql = "INSERT INTO {}({}) VALUES ({});"
	dummySql = dummySql.format(tableName,", ".join(keySet),valueDataSet)
	print("Insert Data : "+dummySql)
	val = (valueDataSet)
	cursor = dbConn.cursor()
	cursor.execute(dummySql,val)
	dbConn.commit()
	cursor.close()
	dbConn.close()
	dbConn = ""

def syncData(dataSet):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	dummySql = "INSERT INTO mail_details(basic_id,filter_id,mail_from,mail_id,mail_subject,attachment_id,no_of_attachments,mime_type,filename,mail_ts) VALUES {}"
	sqlData = ""
	for x in dataSet:
		sqlData = sqlData + "(" + ",".join(x) + "),"
	dummySql = dummySql.format(sqlData)

	if dummySql[len(dummySql)-1] == ",":
		dummySql = dummySql[:-1]
	dummySql = dummySql + ";"
	print("---------------------------")
	print("Insert Data : "+dummySql)
	print("---------------------------")
	val = (dataSet)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	dbConn.commit()
	cursor.close()
	dbConn.close()
	dbConn = ""

def updateData(dataSet, tableName):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	keySet = dataSet.keys()
	idTables = ["basic","login_history"]
	whereClause = " basic_id = " + str(dataSet["basic_id"]);
	if tableName in idTables :
		whereClause = " id = " + str(dataSet["basic_id"]);
	if tableName == "drive_folders" or tableName == "mail_details":
		whereClause = " id = " + str(dataSet["id"]);

	valueDataSet = ""
	for i in range(len(keySet)):
		if keySet[i] != "basic_id" and keySet[i] != "id":
			if i == (len(keySet)-1):
				valueDataSet = valueDataSet + keySet[i] + " = '" + removeTags(str(dataSet[keySet[i]]).replace("'","\\'"))+"'"
			else:
				valueDataSet = valueDataSet + keySet[i] + " = '" + removeTags(str(dataSet[keySet[i]]).replace("'","\\'"))+"',"

	if valueDataSet[len(valueDataSet)-1] == ",":
		valueDataSet = valueDataSet[:-1]

	dummySql = "UPDATE {} SET {} WHERE {};"
	dummySql = dummySql.format(tableName,valueDataSet,whereClause)
	print("Update Data : "+dummySql)
	val = (valueDataSet)
	cursor = dbConn.cursor()
	cursor.execute(dummySql,val)
	dbConn.commit()
	cursor.close()
	dbConn.close()
	dbConn = ""

def removeTags(data):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', data)

def getUserByEmail(email):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	dummySql = "SELECT * FROM basic WHERE email_id = '"+email+"'"
	print("Get User By Email : "+dummySql)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	userDetails = cursor.fetchone()
	cursor.close()
	dbConn.close()
	dbConn = ""
	print(userDetails)
	return userDetails;

def getTableDetails(data):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	dummySql = "SELECT * FROM "+str(data["table_name"])
	if len(str(data["where"])) > 0:
		dummySql = dummySql + " WHERE "+ str(data["where"])
	if len(str(data["group"])) > 0:
		dummySql = dummySql + " GROUP BY "+ str(data["group"])
	if len(str(data["order"])) > 0:
		dummySql = dummySql + " ORDER BY "+ str(data["order"])
	if len(str(data["limit"])) > 0:
		dummySql = dummySql + " LIMIT "+ str(data["limit"])

	print("Get Table details : "+dummySql)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	tableDetails = cursor.fetchall()
	cursor.close()
	dbConn.close()
	dbConn = ""
	return tableDetails;

def getMailBox(data):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	dummySql = "SELECT GROUP_CONCAT(a.filename SEPARATOR ' *^* '),GROUP_CONCAT(a.id SEPARATOR ' *^* '),b.folder_name,b.id FROM mail_details a LEFT JOIN drive_folders b on b.id = a.drive_path WHERE a.basic_id = '"+str(data["id"])+"' AND a.deleted_at = '1970-12-31 23:59:59' GROUP BY b.id ORDER BY b.id "
	
	print("Get Table details : "+dummySql)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	tableDetails = cursor.fetchall()
	cursor.close()
	dbConn.close()
	dbConn = ""
	return tableDetails;

def updateLogin(basic_id, loggedIn):
	global dbConn
	if dbConn == "":
		connDB1(dbName)
	filterData = "NULL"
	filterType = "NULL"

	dummySql = "SELECT * FROM email_filter WHERE basic_id = '"+str(basic_id)+"' ORDER BY id DESC LIMIT 1"
	print("Update Login : "+dummySql)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	filterDetails = cursor.fetchone()	
	if filterDetails != None:
		filterData = filterDetails[2]
		filterType = filterDetails[3]
	cursor.close()
	print("updateLogin: "+str(filterData)+", "+str(filterType))

	dummySql = "SELECT * FROM login_history WHERE basic_id = '"+str(basic_id)+"' ORDER BY id DESC LIMIT 1"
	print("Update Login : "+dummySql)
	cursor = dbConn.cursor()
	cursor.execute(dummySql)
	userDetails = cursor.fetchone()
	print("Update Login details data : "+str(userDetails))
	if userDetails != None:
		print("updateLogin: update Logout")
		dbloginHistoryData = {"login_history":{"id":userDetails[0],"basic_id":str(basic_id),"updated_at":datetime.datetime.now()}}
		updateData(dbloginHistoryData["login_history"],"login_history")

	if loggedIn == "1":
		print("updateLogin: insert")
		dbloginHistoryData = {"login_history":{"basic_id":basic_id,"filter_data":filterData,"filter_type":filterType}}
		print("updateLogin: insert1 : "+ str(dbloginHistoryData))
		insertData(dbloginHistoryData["login_history"],"login_history")
	
def dbMain():
	global dbConn	
	if installed == '0':
		connDB()
	else:
		connDB1(dbName)
	# insertRegistration()

