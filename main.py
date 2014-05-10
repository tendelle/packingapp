#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#Packing List App Main

import os
import webapp2
import cgi
import jinja2
import validation
import listdetermination
from collections import namedtuple

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'packinglist') 
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
class MainHandler(Handler):
    #write the form
    def write_form(self, username="", error_user="", error_password="", error_verify="", 
        email="", error_email=""):
        self.render('registration.html', username=username, error_user=error_user, 
            error_password=error_password, error_verify=error_verify, 
            email=email, error_email=error_email)
    #what happens when user "gets"
    def get(self):
        self.write_form()

    def post(self):
        username, password = self.request.get("username"), self.request.get("password")
        verify, email = self.request.get("verify"), self.request.get("email")
        errors = validation.valid(username, password, verify, email)
        error_user, error_password, error_verify, error_email = "", "", "", ""
        #check if username already exists in googgledb
        b=db.GqlQuery("Select * from Users where username=:1", username)
        user = b.get()
        if user:
            error_user="Username already exists"
            username = ""
            self.write_form(username=username, error_user=error_user, email=email)
        else:
            if sum(errors)==0: #if there are no errors, redirect to success page
                global username
                #put username in cookie
                self.response.headers.add_header("set-cookie", "username=%s" %str(username))
                #store user info in database
                a = Users(username=username, password=password, email=email)
                a.put()

                self.redirect("/packinglist/welcome")

            else:
                error_user, error_password, error_verify, error_email = "", "", "", ""
                if errors[0]==1:
                    error_user="Invalid Username"
                if errors[1]==1:
                    error_password="Invalid Password"
                if errors[2]==1:
                    error_verify="Password Mismatch"
                if errors[3]==1:
                    error_email="Invalid Email"
                self.write_form(username, error_user, error_password, error_verify, email,
                error_email)

class Users(db.Model):
    username=db.StringProperty(required=True)
    password=db.TextProperty(required=True)
    email=db.StringProperty(required=False)
    created=db.DateTimeProperty(auto_now_add=True)

class Welcome(MainHandler):
    def write_form(self):
        username=self.request.cookies.get("username")
        self.write("Welcome, "+ username)

class Login(Handler):
    def write_form(self, username="", error_login=""):
        self.render("login.html", username=username, error_login=error_login)
    def get(self):
        self.write_form()
    def post(self):
        username, password = self.request.get("username"), self.request.get("password")
        b=db.GqlQuery("Select * from Users where username=:1", username)
        user = b.get()
        if user and user.password==password:
            self.response.headers.add_header("set-cookie", "username=%s" %str(username))
            self.redirect("/packinglist/welcome")
        elif user:
            error_login="Incorrect password"
            self.write_form(username=username, error_login=error_login)
        else:
            error_login="User doesn't exist"
            self.write_form(username="", error_login=error_login)

class Logout(Handler):
    def get(self):
        self.response.headers.add_header("set-cookie", "username=;Path=/")
        self.redirect("/packinglist/signup")

class Generator(Handler):
    def write_form(self, name="", days="", error_name="", error_days="", error_gender="", error_temp=""): #I need to make checkbox "sticky" too
        self.render("generator.html", name=name, days=days, error_days=error_days, 
            error_gender=error_gender, error_temp=error_temp)
    def get(self):
        self.write_form()
    def post(self):
        name, days, gender = self.request.get("name"), self.request.get("days"), self.request.get("gender")
        cold, warm= self.request.get("cold"), self.request.get("warm")
        rainy, beach = self.request.get("rainy"), self.request.get("beach")
        work, hiking, festival = self.request.get("work"), self.request.get("hiking"), self.request.get("festival")
        style = self.request.get("style")
        error=0
        error_name, error_days, error_gender, error_temp = "", "", "", ""
        if name=="":
            error_name="Name is required"
            error=1
        if days=="":
            error_days="Duration of trip is required"
            error=1
        if gender=="":
            error_gender="Gender is required"
            error=1
        if all([cold=="", warm=="", rainy==""]):
            error_temp="Temperature is required"
            error=1
        if error==1:
            self.write_form(name=name, days=days, error_name=error_name, error_days=error_days, error_gender=error_gender,
                error_temp=error_temp)
        else:
            a = Preferences(name=name, days=int(days), gender=gender, cold=cold, warm=warm, rainy=rainy, beach=beach, 
                work=work, hiking=hiking, festival=festival, style=style)
            a.put()
            selection = db.GqlQuery("Select * from Packing")
            for e in selection:
                e.name=False
                db.put(e)
            self.response.headers.add_header("set-cookie", "name=%s" %str(name))
            self.response.write("Success")        


class Preferences(db.Model):
    name=db.StringProperty(required=True)
    days=db.IntegerProperty(required=True)
    gender=db.StringProperty(required=True)
    cold=db.StringProperty(required=False)
    warm=db.StringProperty(required=False)
    rainy=db.StringProperty(required=False)
    beach=db.StringProperty(required=False)
    work=db.StringProperty(required=False)
    hiking=db.StringProperty(required=False)
    festival=db.StringProperty(required=False)
    style=db.StringProperty(required=False)
    created=db.DateTimeProperty(auto_now_add=True)
    

class Checklist(Handler):
    def get(self):
        name=self.request.cookies.get("name")
        b=db.GqlQuery("Select * from Preferences where name=:1", name)
        preference = b.get()
        days=preference.days
        gen_user=preference.gender
        beach=preference.beach
        hiking=preference.hiking
        festival=preference.festival
        work=preference.work
        cold=preference.cold
        rainy=preference.rainy
        type_packer=preference.style
        packed_side = "No" #To make flexible

        Unit = namedtuple("Unit", ["item", "category","gender", "freq","type","packed"])
        items = [Unit("toothbrush", "Toiletry", "N", "Single", "All","No"),
                Unit("toothpaste","Clothing", "N", "Single","Beach","No"),
                Unit("Towel","Clothing", "N", "Multiple", "All","No")]
        self.render("checklist.html", items=items)

#class ListStorage(db.Model): #generates the list of items for the trip name, do i need to transpose it?
#    b=db.GqlQuery("Select * from Packing")
#    items=b.get()
#    for item in items.item:
#        item=db.StringProperty(required=True)
class Packing(db.Model):
    item=db.StringProperty(required=True)
    category=db.StringProperty(required=False)
    gender=db.StringProperty(required=False)
    freq = db.StringProperty(required=False)
    type = db.StringProperty(required = False)
    names = db.GqlQuery("Select name from Preferences").fetch(5) #generate list of columns
    for e in names:
        e = db.BooleanProperty(indexed=True)
    
""" How to change to status of a packed item
packed_list = ["Toothbruth", "Toothpaste"]
selection = db.GqlQuery("Select * from Packing where name is :1 and item in :1", name, 
    packed_list)
for e in packed_list:
    e.name=True
    db.put(e)
"""


app = webapp2.WSGIApplication([
    ('/packinglist/signup', MainHandler),
    ('/packinglist/welcome', Welcome),
    ('/packinglist/login', Login),
    ('/packinglist/logout', Logout),
    ('/packinglist/generator', Generator),
    ('/packinglist/checklist', Checklist)
], debug=True)
