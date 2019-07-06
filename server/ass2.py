from flask import Flask,render_template,request,jsonify,redirect, url_for
import json,datetime,urllib,time
from flask_cors import CORS
from mongoengine import connect,StringField, IntField, Document, EmbeddedDocument, ListField, EmbeddedDocumentField
from xml.dom.minidom import parseString
import xlrd,dicttoxml
import codecs
import pickle
import re
import os
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)
from functools import wraps

SECRET_KEY = "A RANDOM KEY"
connect(
    host='mongodb://ass2:1234567a@ds121091.mlab.com:21091/my-database'     #connect the database
)

#the followings are the attributes of the crime
class Crime(Document):
    id = StringField(required=True, primary_key=True)
    postcode = StringField(max_length=50)
    data = ListField(max_length=1000)
    def __init__(self, id, postcode, data=[],*args, **values):
        super().__init__(*args, **values)
        self.id = id
        self.postcode = postcode
        self.data = data

#configure the path
template_dir = os.path.abspath('../client/templates')
static_dir = '../client/static'
app = Flask(__name__,template_folder=template_dir,static_folder=static_dir)
app.config["APPLICATION_ROOT"] = "/abc/123"
CORS(app)

#validate the token, only the admin can import and delete data
def authenticate_by_token(token):
   if token is None:
       return False
   s = Serializer(SECRET_KEY)
   username = s.loads(token.encode())
   if(username==None):
       return False
   if username == 'admin':
      return True
   return False

def login_required(f, message="You are not authorized"):
   @wraps(f)
   def decorated_function(*args, **kwargs):
       token = request.headers.get("AUTH_TOKEN")
       if authenticate_by_token(token):
           return f(*args, **kwargs)
       return jsonify(message=message), 401
   return decorated_function

#both admin and guest can access data
def authenticate_by_token1(token):
   if token is None:
       return False
   s = Serializer(SECRET_KEY)
   username = s.loads(token.encode())
   if(username==None):
       return False
   if username == 'admin' or username=='guest':
      return True
   return False

def login_required1(f, message="You are not authorized"):
   @wraps(f)
   def decorated_function(*args, **kwargs):
       token = request.headers.get("AUTH_TOKEN")
       if authenticate_by_token1(token):
           return f(*args, **kwargs)
       return jsonify(message=message), 401
   return decorated_function


def serialize(object):
   return codecs.encode(
          pickle.dumps(object, pickle.HIGHEST_PROTOCOL), "base64").decode()

def deserialize(object_string):
   return pickle.loads(codecs.decode(object_string.encode(), "base64"))

#this is the root path
@app.route("/",methods=['GET'])
def index():
    return render_template('js_client.html'),201

# Creating a data entry with the data service
@app.route("/crimes", methods=['POST'])
@login_required
def post_cirmes():
    data = json.loads(request.data.decode())
    input = data['name']
    if(input.isdigit()==False):      #when the user input lganame
        connect('c')
        for t in Crime.objects:
            if (t.id == input):
                return jsonify({'lgname': input,'status':200}), 200
        data = json.load(codecs.open('data.json', 'r', 'utf-8-sig'))
        for t in data['lga_postcode_mappings']:
            if (t['State']=='New South Wales' and t['LGA region']==input):
                if ' ' in input:               #process the lganame when there are spaces in the word
                    input = input.replace(" ", "")
                    dls = 'http://www.bocsar.nsw.gov.au/Documents/RCS-Annual/'+input+'lga.xlsx'    #download the file
                    urllib.request.urlretrieve(dls, input+".xlsx")
                    data = toxml(input)        #process the data
                    xml = dicttoxml.dicttoxml(data)
                    dom = parseString(xml).toprettyxml()
                    t1 = Crime(input, t['Postcode'],data=[data])
                    t1.save()
                    return jsonify({'lgname': input,'status':201}), 201
                else:
                    dls = 'http://www.bocsar.nsw.gov.au/Documents/RCS-Annual/' + input + 'lga.xlsx'
                    urllib.request.urlretrieve(dls, input + ".xlsx")
                    data  = toxml(input)
                    xml = dicttoxml.dicttoxml(data)
                    dom = parseString(xml).toprettyxml()
                    t1 = Crime(input, t['Postcode'], data=[data])
                    t1.save()
                    return jsonify({'lgname': input,'status':201}), 201
        return jsonify({'lgname': "The LGA name you inputed doesn't exist.", 'status': 400}), 400

    if (input.isdigit()==True):        #when the user input postcode
        connect('c')
        result = []
        data = json.load(codecs.open('data.json', 'r', 'utf-8-sig'))
        for t in data['lga_postcode_mappings']:
            if (t['State'] == 'New South Wales' and t['Postcode'] == input):
                if ' ' in t['LGA region']:
                    t['LGA region'] = t['LGA region'].replace(" ", "")
                    dls = "http://www.bocsar.nsw.gov.au/Documents/RCS-Annual/"+t['LGA region']+"lga.xlsx"
                    urllib.request.urlretrieve(dls, t['LGA region']+".xlsx")
                    data = toxml(t['LGA region'])
                    xml = dicttoxml.dicttoxml(data)
                    dom = parseString(xml).toprettyxml()
                else:
                    dls = "http://www.bocsar.nsw.gov.au/Documents/RCS-Annual/" + t['LGA region'] + "lga.xlsx"
                    urllib.request.urlretrieve(dls, t['LGA region'] + ".xlsx")
                    data = toxml(t['LGA region'])
                    xml = dicttoxml.dicttoxml(data)
                    dom = parseString(xml).toprettyxml()
                t1 = Crime(t['LGA region'], t['Postcode'], data=[data])
                t1.save()
                result.append({'locationID': t['LGA region']})
        for t in Crime.objects:
            if (t.postcode == input):
                return jsonify({'lgname': result, 'status': 200}), 200
        if len(result) == 0:
            return jsonify({'lgname': "The postcode you inputed doesn't exist.", 'status': 404}), 404
        return jsonify({'lgname': result, 'status': 201}), 201

#Retreiving the available collection with the data service
@app.route("/getall", methods=['GET'])
@login_required1
def getall():
    connect('c')
    storedata={}
    type = request.args.get('type')
    if(type=='json'):
        for t in Crime.objects:
            storedata[t.id] = t.data
        return jsonify({'alldata': storedata}), 200
    else:
        for t in Crime.objects:
            nowtime = datetime.datetime.fromtimestamp(time.time())
            xml = dicttoxml.dicttoxml(t.data, custom_root='content')
            dom = parseString(xml).toprettyxml()
            dom = re.sub('<\?xml version="[0-9]*\.[0-9]*" \?>\n', '', dom)
            feed = AtomFeed(id='https://mlab.com/databases/my-database/collections/crime/' + t.id, title=t.id,
                            updated=nowtime, author="z5129269")
            storedata[t.id] = feed.to_string() + dom
        return jsonify({'alldata': storedata}), 200

#Retreiving a data entry with the data service
@app.route("/getsingle", methods=['GET'])
@login_required1
def getsingle():
    connect('c')
    storedata={}
    name1 = request.args.get('name1')
    type = request.args.get('type')
    if " " in name1:
        name1 = name1.replace(" ", "")
    if(type=='json'):
        for t in Crime.objects:
            if (t.id == name1):
                storedata[t.id] = t.data
        return jsonify({'alldata': storedata}), 200
    if(type=='xml'):
        for t in Crime.objects:
            if (t.id == name1):
                nowtime= datetime.datetime.fromtimestamp(time.time())
                xml = dicttoxml.dicttoxml(t.data[0],custom_root='content')
                dom = parseString(xml).toprettyxml()
                dom = re.sub('<\?xml version="[0-9]*\.[0-9]*" \?>\n','', dom)
                feed = AtomFeed(id='https://mlab.com/databases/my-database/collections/crime/'+t.id, title=t.id, updated=nowtime, author="z5129269")
                storedata[t.id] = feed.to_string()+dom
        return jsonify({'alldata': storedata}), 200

#Retreiving data entries with filter
@app.route("/crimes/filter", methods=['GET'])
@login_required1
def filter():
    connect('c')
    name1 = request.args.get('name1')
    name2 = request.args.get('name2')
    type = request.args.get('type')
    if " " in name1:
        name1 = name1.replace(" ", "")
    if " " in name2:
        name2 = name2.replace(" ", "")
    storedata= {}
    a={}
    if(type=="json"):
        if (name2.isdigit() == False):
            for t in Crime.objects:
                if(t.id==name1 or t.id==name2):
                    storedata[t.id] = t.data
            return jsonify({'alldata': storedata}), 200
        if (name2.isdigit()):
            for t in Crime.objects:
                if (t.id == name1):
                    a[t.id] = name1
            if(len(a)==0):
                return jsonify({'alldata': "The data does not exist."}), 400
            else:
                data = filtertoxml(name1, name2)
        storedata[name1] = data
        return jsonify({'alldata': storedata}), 200
    else:
        if (name2.isdigit() == False):
            for t in Crime.objects:
                if (t.id == name1 or t.id == name2):
                    nowtime = datetime.datetime.fromtimestamp(time.time())
                    xml = dicttoxml.dicttoxml(t.data, custom_root='content')
                    dom = parseString(xml).toprettyxml()
                    dom = re.sub('<\?xml version="[0-9]*\.[0-9]*" \?>\n', '', dom)
                    feed = AtomFeed(id='https://mlab.com/databases/my-database/collections/crime/' + t.id, title=t.id,
                                    updated=nowtime, author="z5129269")
                    storedata[t.id] = feed.to_string() + dom
            return jsonify({'alldata': storedata}), 200
        if (name2.isdigit()):
            for t in Crime.objects:
                if (t.id == name1):
                    a[t.id] = name1
            if(len(a)==0):
                return jsonify({'alldata': "The data does not exist."}), 400
            else:
                data = filtertoxml(name1, name2)
        nowtime = datetime.datetime.fromtimestamp(time.time())
        xml = dicttoxml.dicttoxml(data, custom_root='content')
        dom = parseString(xml).toprettyxml()
        dom = re.sub('<\?xml version="[0-9]*\.[0-9]*" \?>\n', '', dom)
        feed = AtomFeed(id='https://mlab.com/databases/my-database/collections/crime/' + name1, title=name1,
                        updated=nowtime, author="z5129269")
        storedata[name1] = feed.to_string() + dom
        return jsonify({'alldata': storedata}), 200

#Deleting a data entry with the data service
@app.route("/delete", methods=['DELETE'])
@login_required
def delete_data():
    connect('c')
    name = request.args.get('name')
    if " " in name:
        name = name.replace(" ", "")
        for t in Crime.objects:
            if(t.id==name):
                Crime.objects(id=name).delete()
                return jsonify(id=name), 200
        return jsonify({'alldata': 'The Id is not in the database.'}), 404
    else:
        for t in Crime.objects:
            if(t.id==name):
                Crime.objects(id=name).delete()
                return jsonify(id=name), 200
        return jsonify({'alldata': 'The Id is not in the database.'}), 404


@app.route("/auth", methods=['POST'])
def generate_token():
    data = json.loads(request.data.decode())
    name = data['name']
    password = data['password']
    s = Serializer(SECRET_KEY, expires_in=600)
    token = s.dumps(name)
    if (name == 'admin' and password == 'admin') or (name == 'guest' and password == 'guest'):
        return jsonify(id=token.decode()), 200
    return 404

#processing the data from specific.xlsx file
def toxml(lga_name):
    wb = xlrd.open_workbook(lga_name +'.xlsx')
    sheet = wb.sheets()[0]
    data = []
    keys = [v.value for v in sheet.row(5) if v.value != ""]
    number_of_columns = sheet.ncols
    tem={}
    tem['title'] = sheet.cell(0, 0).value
    tem['detail'] = sheet.cell(2, 0).value
    tem['area'] = sheet.cell(4, 0).value
    tem['updated'] = str(datetime.datetime.now())
    data.append(tem)
    for row_number in range(7, 69):
        c = 0
        for col in range(number_of_columns):
            try:
                value = round(float((sheet.cell(row_number, col).value)),1)
            except ValueError as e:
                value = (sheet.cell(row_number, col).value)
            if col == 0 and value != '':
                temp = {}
                data.append(temp)
                temp['Offence group '] = value.strip()
                temp['Offence type'] = []
            if col == 1:
                temp2 = {}
                temp2['type'] = value
                temp2['data'] = []
                temp['Offence type'].append(temp2)
            if col > 1 and col < 12 and col % 2 == 0:
                temp3 = {}
                temp3['Duration'] = keys[c]
                temp3['Number of incidents'] = value
                temp2['data'].append(temp3)
            if col > 1 and col < 12 and col % 2 != 0:
                temp3 = {}
                temp3['Duration'] = keys[c]
                temp3['Rate per 100,000 population'] = value
                temp2['data'].append(temp3)
                c += 1
            if col == 12:
                temp3 = {}
                temp3['24-month trend^^'] = value
                temp2['data'].append(temp3)
            if col == 13:
                temp3 = {}
                temp3['60-month trend^^'] = value
                temp2['data'].append(temp3)
            if col == 14:
                temp3 = {}
                temp3['2016 LGA Rank*'] = value
                temp2['data'].append(temp3)
    return data

#processing the data from specific.xlsx file
def filtertoxml(name1,name2):
    dls = "http://www.bocsar.nsw.gov.au/Documents/RCS-Annual/" + name1 + "lga.xlsx"
    urllib.request.urlretrieve(dls, name1 + ".xlsx")
    wb = xlrd.open_workbook(name1 + '.xlsx')
    sheet = wb.sheets()[0]
    data = []
    keys = [v.value for v in sheet.row(5) if v.value != ""]
    number_of_columns = sheet.ncols
    period = sheet.cell(0, 0).value
    if('2012' in period):
        tem = {}
        tem['title'] = sheet.cell(0, 0).value
        tem['detail'] = sheet.cell(2, 0).value
        tem['area'] = sheet.cell(4, 0).value
        tem['updated'] = str(datetime.datetime.now())
        data.append(tem)
        for row_number in range(7, 69):
            for col in range(number_of_columns):
                try:
                    value = round(float((sheet.cell(row_number, col).value)), 1)
                except ValueError as e:
                    value = (sheet.cell(row_number, col).value)
                if col == 0 and value != '':
                    temp = {}
                    data.append(temp)
                    temp['Offence group '] = value.strip()
                    temp['Offence type'] = []
                if col == 1:
                    temp2 = {}
                    temp2['type'] = value
                    temp2['data'] = []
                    temp['Offence type'].append(temp2)
                if (name2 == "2012"):
                    c = 0
                    if col > 1 and col < 4 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 1 and col < 4 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2013"):
                    c = 1
                    if col > 3 and col < 6 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 3 and col < 6 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2014"):
                    c = 2
                    if col > 5 and col < 8 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 5 and col < 8 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2015"):
                    c = 3
                    if col > 7 and col < 10 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 7 and col < 10 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2016"):
                    c = 4
                    if col > 9 and col < 12 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 9 and col < 12 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
    else:
        tem = {}
        tem['title'] = sheet.cell(0, 0).value
        tem['detail'] = sheet.cell(2, 0).value
        tem['area'] = sheet.cell(4, 0).value
        tem['updated'] = str(datetime.datetime.now())
        data.append(tem)
        for row_number in range(7, 69):
            for col in range(number_of_columns):
                try:
                    value = round(float((sheet.cell(row_number, col).value)), 1)
                except ValueError as e:
                    value = (sheet.cell(row_number, col).value)
                if col == 0 and value != '':
                    temp = {}
                    data.append(temp)
                    temp['Offence group '] = value.strip()
                    temp['Offence type'] = []
                if col == 1:
                    temp2 = {}
                    temp2['type'] = value
                    temp2['data'] = []
                    temp['Offence type'].append(temp2)
                if (name2 == "2013"):
                    c = 0
                    if col > 1 and col < 4 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 1 and col < 4 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2014"):
                    c = 1
                    if col > 3 and col < 6 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 3 and col < 6 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2015"):
                    c = 2
                    if col > 5 and col < 8 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 5 and col < 8 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2016"):
                    c = 3
                    if col > 7 and col < 10 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 7 and col < 10 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
                if (name2 == "2017"):
                    c = 4
                    if col > 9 and col < 12 and col % 2 == 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Number of incidents'] = value
                        temp2['data'].append(temp3)
                    if col > 9 and col < 12 and col % 2 != 0:
                        temp3 = {}
                        temp3['Duration'] = keys[c]
                        temp3['Rate per 100,000 population'] = value
                        temp2['data'].append(temp3)
                        c += 1
    return data

if __name__ == "__main__":
   app.run('localhost', 5000)