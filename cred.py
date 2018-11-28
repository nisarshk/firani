from flask import Flask, redirect, url_for, session, request, jsonify, render_template, send_from_directory
from flask_oauthlib.client import OAuth
from config.db import *
import ast, json
import datetime
import base64
import time
from apiclient.http import MediaFileUpload,MediaIoBaseDownload
from apiclient.discovery import build
import urllib2
import requests
from oauth2client import file, client, tools
import flask
import base64
import httplib2
from httplib2 import Http
import uuid
import os
from apiclient import errors
import dateutil.parser
import io
import PyPDF2 

app = Flask(__name__)
app.config['GOOGLE_ID'] = ""
app.config['GOOGLE_SECRET'] = ""
app.debug = True
app.secret_key = 'firani_production'
oauth = OAuth(app)

keywords = ["bill","transaction","premium","misc"]

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'email', 'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/userinfo.profile']

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': SCOPES
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    date = dateutil.parser.parse(str(date))
    native = date.replace(tzinfo=None)
    format='%d%m%Y%H%M%S'
    return native.strftime(format) 


@app.route('/')
def index():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Index-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')

        return redirect(url_for('mailbox'))
    return render_template('login.html')

@app.route('/open_pdf')
def openPdf():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Open Attachment-------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        getData = getUserByEmail(session["email"])
        if getData is None:
            return redirect(url_for('login'))
        filterData = {"table_name":"mail_details","where":"id = '"+str(request.args.get("attachment"))+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)

        att=service.users().messages().attachments().get(userId="me", messageId=str(filterData[0][5]),id=str(filterData[0][8])).execute()
        data=att['data']
        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
        path = "downloads/"+str(filterData[0][1])
        if not os.path.exists(path):
            os.makedirs(path)

        path1 = path
        path = path + "/"+filterData[0][7]
        f = open(path, 'w')
        f.write(file_data)
        f.close()

        return send_from_directory(path1,filterData[0][7])
    return render_template('login.html')

@app.route('/mailbox')
def mailbox():
    print("------------------------------------------------------------------------------------")
    print("--------------------------MailBox-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        getData = getUserByEmail(session["email"])
        if getData is None:
            return redirect(url_for('login'))
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(getData[0])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        data = ()
        filterMail = ""
        filterId = 1
        if len(filterData) > 0:
            filterData = filterData[0]
            session["lastSync"] = filterData[4]
            filterId = filterData[0]
            filterMail = filterData[2]
            data = syncMail(service,filterMail,filterId)

        moveToDrive()
        # mailData = {"table_name":"mail_details","where":"basic_id = '"+str(getData[0])+"' AND filter_id = '"+str(filterId)+"' AND deleted_at = '1970-12-31 23:59:59'","group":"mail_id","order":"mail_ts DESC","limit":""}
        data = getMailBox(session)
        # mailData = {"table_name":"mail_details","where":"basic_id = '"+str(getData[0])+"' AND filter_id = '"+str(filterId)+"' AND deleted_at = '1970-12-31 23:59:59'","group":"","order":"mail_ts DESC","limit":""}
        # data = getTableDetails(mailData)
        d = {}
        for a in data:
            d.setdefault(a[3],[]).append(a)
        # open("mails Query.txt","w").write(str(d))
        return render_template('mailbox.html', data=d, filterMail=filterMail)
        # return render_template('mailbox.html', data=data, filterMail=filterMail)
    return redirect(url_for('index'))

@app.route('/mailbox1')
def mailbox1():
    print("------------------------------------------------------------------------------------")
    print("--------------------------MailBox-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        getData = getUserByEmail(session["email"])
        if getData is None:
            return redirect(url_for('login'))
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(getData[0])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        data = ()
        filterMail = ""
        filterId = 1
        if len(filterData) > 0:
            filterData = filterData[0]
            session["lastSync"] = filterData[4]
            filterId = filterData[0]
            filterMail = filterData[2]
            data = syncMail(service,filterMail,filterId)
        # mailData = {"table_name":"mail_details","where":"basic_id = '"+str(getData[0])+"' AND filter_id = '"+str(filterId)+"' AND deleted_at = '1970-12-31 23:59:59'","group":"mail_id","order":"mail_ts DESC","limit":""}
        # data = getMailBox(mailData)
        mailData = {"table_name":"mail_details","where":"basic_id = '"+str(getData[0])+"' AND filter_id = '"+str(filterId)+"' AND deleted_at = '1970-12-31 23:59:59'","group":"","order":"mail_ts DESC","limit":""}
        data = getTableDetails(mailData)
        d = {}
        for a in data:
            d.setdefault(a[5],[]).append(a)
        return render_template('mailbox1.html', data=d, filterMail=filterMail)
        # return render_template('mailbox.html', data=data, filterMail=filterMail)
    return redirect(url_for('index'))

def default(o):
  if type(o) is datetime.date or type(o) is datetime.datetime:
    return o.isoformat()

@app.route('/api/updateFilterEmail', methods=["POST"])
def updateFilterUrl():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Update Filter Email-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        print(request.form['email'])
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(session["id"])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        data = ()
        filterMail = ""
        filterId = 1
        if len(filterData) > 0:
            filterData = filterData[0]
            filterId = filterData[0]
            filterMail = filterData[2]
        formMail = request.form["email"]
        if filterMail == formMail:
            return '{"status":"1","message":"success"}'
        service = authenticator('gmail','v1')
        userDetails = {}
        userDetails["basic_id"] = str(session["id"])
        userDetails["filter_data"] = str(formMail)
        userDetails["filter_type"] = "email"
        dbBasicData = {"email_filter":userDetails}
        insertData(dbBasicData["email_filter"],"email_filter")
        return '{"status":"1","message":"success"}'
    return '{"status":"-1","message":"login_required"}'


@app.route('/api/sync_new_mails', methods=["POST"])
def syncNewMail():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Update Filter Email-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(session["id"])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        data = ()
        filterMail = ""
        filterId = 1
        if len(filterData) > 0:
            filterData = filterData[0]
            filterId = filterData[0]
            filterMail = filterData[2]
            session["lastSync"] = filterData[4]
            session["basic_id"] = filterData[1]
            data = syncMail(service,filterMail,filterId)
            mailData = {"table_name":"mail_details","where":"basic_id = '"+str(session["id"])+"' AND filter_id = '"+str(filterId)+"' AND deleted_at = '1970-12-31 23:59:59'","group":"","order":"mail_ts DESC","limit":""}
            data = getTableDetails(mailData)
            return '{"status":"1","message":"success","mails":'+json.dumps(data, default=default)+'}'
        else:
            return '{"status":"-1","message":"no_key_found"}'
    return '{"status":"-1","message":"login_required"}'

@app.route('/api/upload_attachment', methods=["POST"])
def uploadFile(detailedData = ""):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Upload file-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        details = ""
        if "details" in request.form:
            details = request.form['details']
        if details == "":
            if detailedData != "":
                details = detailedData.split("_")
        else:
            details = details.split("_")

        service = authenticator('gmail','v1')
        filterData = {"table_name":"mail_details","where":"basic_id = '"+str(details[1])+"' AND id = '"+str(details[0])+"' AND mail_id = '"+str(details[2])+"'","group":"","order":"","limit":"1"}
        filterData = getTableDetails(filterData)
        print(filterData)
        if filterData[0][11] != None:
            return '{"status":"1","message":"already success","path":"'+path+'"}'

        att=service.users().messages().attachments().get(userId="me", messageId=str(details[2]),id=str(filterData[0][8])).execute()
        data=att['data']
        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
        path = "downloads/"+str(details[1])
        if not os.path.exists(path):
            os.makedirs(path)

        path = path + "/"+filterData[0][7]
        f = open(path, 'w')
        f.write(file_data)
        f.close()

        service = authenticator('drive','v3')
        driveMiscName = "misc"
        driveId = session["drive_folder_id"]
        driveMiscId = session["drive_misc_folder_id"]

        getData = getUserByEmail(session["email"])
        if getData is None:
            return redirect(url_for('login'))

        if driveId == None or driveId == "":
            driveId = getData[13]
            driveName = getData[12]
            if driveId == None or driveId == "":
                driveId = createDriveDirectory(driveName,"")
                session["drive_folder_id"] = driveId
                session['drive_misc_folder_id'] = createDriveDirectory(driveMiscName,driveId)
                dbBasicData = {"basic":{"drive_folder_id":str(driveId),"drive_misc_folder_id":str(session['drive_misc_folder_id']),"id":str(session["id"]),"basic_id":str(session["id"])}}
                updateData(dbBasicData["basic"],"basic")

        if session["drive_misc_folder_id"] == None or session["drive_misc_folder_id"] == "":
            driveId = getData[13]
            if driveId == None or driveId == "":
                session['drive_misc_folder_id'] = createDriveDirectory(driveMiscName,driveId)
                dbBasicData = {"basic":{"drive_misc_folder_id":str(session['drive_misc_folder_id']),"id":str(session["id"]),"basic_id":str(session["id"])}}
                updateData(dbBasicData["basic"],"basic")
        
        drivePath = getKeywords(path)
        driveFoldersData = {"table_name":"drive_folders","where":"basic_id = '"+str(session["id"])+"' AND folder_name = '"+drivePath+"' ","group":"","order":"","limit":"1"}
        driveFoldersData = getTableDetails(driveFoldersData)
        if drivePath != "":
            if len(driveFoldersData) == 0:
                folderData = {"drive_folders":{"basic_id":str(session["id"]), "folder_name":drivePath}}
                insertData(folderData["drive_folders"],"drive_folders")

            driveFoldersData = {"table_name":"drive_folders","where":"basic_id = '"+str(session["id"])+"' AND folder_name = '"+drivePath+"' ","group":"","order":"","limit":"1"}
            driveFoldersData = getTableDetails(driveFoldersData)
            if len(driveFoldersData) > 0:
                driveFoldersData = driveFoldersData[0]
                driveMiscId = driveFoldersData[3]
                if driveMiscId == None or driveMiscId == "":
                    driveMiscId = createDriveDirectory(driveFoldersData[2], driveId)
                    dbBasicData = {"drive_folders":{"folder_id":str(driveMiscId),"folder_name":str(drivePath),"basic_id":str(session["id"]),"id":str(driveFoldersData[0])}}
                    updateData(dbBasicData["drive_folders"],"drive_folders")
        if drivePath == "":
            getData = getUserByEmail(session["email"])
            driveMiscId = getData[14]
            if len(driveMiscId) > 0:
                if len(driveFoldersData) > 0:
                    driveFoldersData = driveFoldersData[0]
                    dbBasicData = {"drive_folders":{"folder_id":str(driveMiscId),"folder_name":str(drivePath),"basic_id":str(session["id"]),"id":str(driveFoldersData[0])}}
                    updateData(dbBasicData["drive_folders"],"drive_folders")


        driveFoldersData = {"table_name":"drive_folders","where":"basic_id = '"+str(session["id"])+"' AND folder_name = '"+drivePath+"' ","group":"","order":"","limit":"1"}
        driveFoldersData = getTableDetails(driveFoldersData)
        file_metadata = {
            'name': filterData[0][7],
            'parents': [driveMiscId]
        }
        if drivePath != "":
            media = MediaFileUpload(path, mimetype=filterData[0][10], resumable=True)
            file = service.files().create(body=file_metadata,media_body=media,fields='id').execute()
            dbBasicData = {"mail_details":{"drive_id":str(file.get("id")),"drive_path":str(driveFoldersData[0][0]),"id":str(details[0]),"basic_id":str(session["id"])}}
            updateData(dbBasicData["mail_details"],"mail_details")
        if os.path.exists(path): 
            os.remove(path)

        return '{"status":"1","message":"success","path":"'+path+'"}'
    return '{"status":"-1","message":"login_required"}'

def createDriveDirectory(directoryName, parentID):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Create Directory------------------------------------------")
    print("------------------------------------------------------------------------------------") 
    if 'google_token' in session:
        service = authenticator('drive','v3')
        file_metadata = {
            'name': directoryName,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if len(parentID) > 0:
            file_metadata = {
                'name': directoryName,
                'parents': [parentID],
                'mimeType': 'application/vnd.google-apps.folder'
            }
        file = service.files().create(body=file_metadata,fields='id').execute()
        return file.get('id')

def syncMail(service,mailId,filterData):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Sync Mail-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        print("Emails")
        ts = time.time()
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(session["id"])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        dateToSync = datetime.datetime.strptime(str(filterData[0][4]), "%Y-%m-%d %H:%M:%S").strftime('%s')
        query = "after:"+str(dateToSync)+" AND has:attachment AND filename:pdf AND from:"+str(mailId)
        dataFormat = "full"
        print(query)
        try:
            response = service.users().messages().list(userId="me",
                                                       q=query).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = service.users().messages().list(userId="me", q=query,
                                                 pageToken=page_token).execute()
                messages.extend(response['messages'])

            if len(messages) > 0:
                return getMailDetails(messages, mailId,filterData,ts)

            return messages
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    return redirect(url_for('login'))

def getMailDetails(mailDetails, mailId,filterData,ts):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Get mail Details-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        service = authenticator('gmail','v1')
        details1 = []
        details_1 = {}
        for data in mailDetails:
            response = service.users().messages().get(userId="me", id=data["id"]).execute()
            mail_id = response["id"]
            msg_str = response['payload']
            # ['headers']
            # msg_parts = response['payload']['parts']
            dateTime = datetime.datetime.fromtimestamp(float(response["internalDate"])/1000.0)
            mail_subject = datetime.datetime.fromtimestamp(float(response["internalDate"])/1000.0)
            for v in msg_str:
                for v2 in msg_str["headers"]:
                    for v1 in v2.iterkeys():
                        if v1 == "name" and v2[v1] == "Subject":
                            mail_subject = v2["value"]
                            break

                for v1 in msg_str["parts"]:
                    details = []
                    if v1["filename"] and len(v1["filename"]) > 0 and v1["filename"].split(".")[len(v1["filename"].split("."))-1] == "pdf":
                        # if 'data' in v1['body']:
                        #     details1[mail_id] = v1['body']['data']
                        if 'attachmentId' in v1['body']:
                            details.append("'"+str(session["basic_id"]).replace("'","\\'")+"'")
                            details.append("'"+str(filterData[0][1]).replace("'","\\'")+"'")
                            details.append("'"+str(mailId).replace("'","\\'")+"'")
                            details.append("'"+str(mail_id).replace("'","\\'")+"'")
                            details.append("'"+str(mail_subject).replace("'","\\'")+"'")
                            details.append("'"+str(v1['body']['attachmentId']).replace("'","\\'")+"'")
                            details.append("'"+str(1).replace("'","\\'")+"'")
                            details.append("'"+str(v1['mimeType']).replace("'","\\'")+"'")
                            details.append("'"+str(v1['filename']).replace("'","\\'")+"'")
                            details.append("'"+str(dateTime).replace("'","\\'")+"'")
                            if len(details) > 0:
                                details_1[str(mail_id)+"_"+str(v1['body']['attachmentId'])] = tuple(details)
                                # details1.append(tuple(details))
                    # details1.extend(details)

        if len(details_1) > 0:
            for x in details_1:
                details1.append(details_1[x])
            syncData(details1)
        ts = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        dbBasicData = {"basic":{"last_sync":str(ts),"basic_id":session["id"]}}
        updateData(dbBasicData["basic"],"basic")
        updateData(dbBasicData["basic"],"email_filter")
        session["lastSync"] = str(ts)

@app.route('/api/move_to_drive', methods=["POST"])
def moveToDrive():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Move To Drive---------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session:
        syncNewMail()
        getData = getUserByEmail(session["email"])
        if getData is None:
            return redirect(url_for('login'))
        filterData = {"table_name":"email_filter","where":"basic_id = '"+str(getData[0])+"'","group":"","order":"id DESC","limit":"1"}
        filterData = getTableDetails(filterData)
        basic_id = ""
        filter_id = ""
        last_sync = ""
        if len(filterData) > 0:
            filterData = filterData[0]
            basic_id = filterData[1]
            filter_id = filterData[0]
            last_sync = filterData[4]

        filterData = {"table_name":"mail_details","where":"basic_id = '"+str(basic_id)+"' AND filter_id = '"+str(filter_id)+"' AND drive_id IS NULL","group":"","order":"","limit":""}
        filterData = getTableDetails(filterData)
        if len(filterData) > 0:
            for row in filterData:
                if row[11] == None or row[11] == "":
                    open("type.txt","a").write(str(row))
                    uploadFile(str(row[0])+"_"+str(row[1])+"_"+str(row[5]))

        return  '{"status":"1","message":"success"}' 

@app.route('/login')
def login():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Login-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    # return google.authorize(callback=url_for('authorized', _external=True))
    return authorized()


@app.route('/logout')
def logout():
    print("------------------------------------------------------------------------------------")
    print("--------------------------Logout-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    session.pop('google_token', None)
    session.pop('email', None)
    session.pop('lastSync', None)
    session.pop('basic_id', None)
    session.pop('drive_folder_id', None)
    session.pop('drive_misc_folder_id', None)
    session.pop('drive_folder_name', None)
    updateLogin(session.get('id'),"0")
    session.pop('id', None)
    return redirect(url_for('index'))

def authenticator(service,version):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Auth-----------------------------------------------------")
    print("------------------------------------------------------------------------------------")
    if 'google_token' in session and 'email' in session:
        credFile = "tokenDatas/"+session["email"]+"_token.json"
        store = file.Storage(credFile)
        credentials = store.get()
        if not credentials or credentials.invalid:
            return redirect(url_for('login'))

        commonAuthFunction(credentials)
        service = build(service, version, http=credentials.authorize(Http()))
        return service
    return redirect(url_for('login'))
    

@app.route('/authorized')
def authorized():
    uniID = uuid.uuid4()
    tokenFilePath = "tokenDatas/"+str(uniID)+".json"
    # if not os.path.exists(tokenFilePath):
    #     open(tokenFilePath, 'w').close()
    try:
        credentials = ""
        store = file.Storage(tokenFilePath)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets('config/client_secret.json',
                scope=SCOPES,
                redirect_uri=flask.url_for('authorized', _external=True)) # access drive api using developer credentials
            credentials = tools.run_flow(flow, store)

        dataAuth = credentials.to_json()
        dataAuth = json.loads(dataAuth)
        email_id = dataAuth["id_token"]["email"]
        os.rename(tokenFilePath,"tokenDatas/"+email_id+"_token.json")

        commonAuthFunction(credentials)
        return redirect(url_for('mailbox'))
    except:
        return redirect(url_for('index'))


def commonAuthFunction(credentials):
    print("------------------------------------------------------------------------------------")
    print("--------------------------Common Auth-----------------------------------------------")
    print("------------------------------------------------------------------------------------")
    dataAuth = credentials.to_json()
    dataAuth = json.loads(dataAuth)
    encryptedAuth = base64.b64encode(str(dataAuth))
    email_id = dataAuth["id_token"]["email"]

    service = build('plus', 'v1', http=credentials.authorize(Http()))
    dataPeople = service.people().get(userId="me").execute()

    print(dataPeople)

    tokenPath = "tokenDatas/"+email_id+"_token.json"
    userDataPath = "tokenDatas/"+email_id+"_data.json"

    userDetails = {}
    userDetails["email_id"] = email_id
    userDetails["pic"] = dataPeople["image"]["url"].split("?")[0]
    userDetails["name"] = dataPeople["displayName"]
    userDetails["given_name"] = dataPeople["name"]["givenName"]
    userDetails["family_name"] = dataPeople["name"]["familyName"]
    userDetails["gender"] = "Male"
    if "gender" in dataPeople:
        userDetails["gender"] = dataPeople["gender"]
    userDetails["gmail_id"] = dataPeople["id"]
    userDetails["profile_details"] = ""
    if "url" in dataPeople:
        userDetails["profile_details"] = dataPeople["url"]
    userDetails["locale"] = dataPeople["language"]
    userDetails["verified_email"] = dataPeople["verified"]
    userDetails["full_details"] = base64.b64encode(json.dumps(dataPeople))
    userDetails["drive_folder_name"] = "gSyncSuite"

    session["user_details"] = userDetails
    getData = getUserByEmail(email_id)
    dbBasicData = {"basic":userDetails}
    if getData is None:
        print("Authorize: Basic Insert")
        insertData(dbBasicData["basic"],"basic")
    else:
        print("Authorize: Basic Update")
        getData1 = getUserByEmail(email_id)
        basic_id = getData1[0]
        userDetails["basic_id"] = basic_id
        updateData(dbBasicData["basic"],"basic")

    getData1 = getUserByEmail(email_id)
    basic_id = getData1[0]
    session['id'] = basic_id
    session['basic_id'] = basic_id
    session['email'] = email_id
    session['google_token'] = (dataAuth['access_token'], '')
    session['drive_folder_name'] = userDetails["drive_folder_name"]
    session["drive_folder_id"] = getData1[13]
    session["drive_misc_folder_id"] = getData1[14]
    session["lastSync"] = getData1[8]
    dbTokenData = {"token":{"token_details":encryptedAuth,"access_token":dataAuth['access_token'],"basic_id":basic_id}}
    if getData is None:
        print("Authorize: Token Insert 1")
        insertData(dbTokenData["token"],"token")
    else:
        tokenData = {"table_name":"token","where":"basic_id = '"+str(basic_id)+"'","group":"","order":"","limit":"1"}
        tokenData = getTableDetails(tokenData)
        if tokenData is None:
            print("Authorize: Token Insert 2")
            insertData(dbTokenData["token"],"token")
        elif not tokenData:
            print("Authorize: Token Insert 3")
            insertData(dbTokenData["token"],"token")
        else:
            print("Authorize: Token Update")
            updateData(dbTokenData["token"],"token")

    updateLogin(basic_id,"1")

    # open(tokenPath,'w').write(credentials.to_json()) # write access token to credentials.json locally 
    open(userDataPath,'w').write(json.dumps(dataPeople)) # write access token to credentials.json locally 

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')


def getKeywords(path):
    print(path)
    if 'google_token' in session:
        path1 = path.split(".")
        if len(path1) > 1:
            if path1[1] == "docx":
                return ""
        pdfFileObj = open(path, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 

        for i in range(0,int(pdfReader.numPages)):
            pageObj = pdfReader.getPage(int(i))
            text = pageObj.extractText()
            for x in keywords:
                if text.find(x) > -1:
                    pdfFileObj.close() 
                    return x

        pdfFileObj.close() 
        return "misc"

    return redirect(url_for('login'))


if __name__ == '__main__':
    dbMain()
    app.run()