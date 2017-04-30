import os

import jinja2
import webapp2
from google.appengine.ext import db
import cgi
import re
import random
import hashlib
from libs.bcrypt import bcrypt



#this sets up the regular expressions and puts them into functions which check if
#certain inputs are valid

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_pass(passw):
    return PASS_RE.match(passw)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
def valid_email(mail):
    return EMAIL_RE.match(mail)



#sets up template paths:

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

#basic (helper?) functions to quickly and easily do certain tasks:
# taught by reddit's spez
    
class Handler(webapp2.RequestHandler):
    
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)
        
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

#create database for blog entries:
class BlogEntries(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)

#prints all posts to the home/main page:   
class MainPage(Handler):
    def get(self):
        blogposts=db.GqlQuery("SELECT * FROM BlogEntries ORDER BY created DESC")
        self.render("mainpage.html",blogposts=blogposts)


# constructs webpage for adding new posts, including form and database entry creation
#doesn't seem like it would allow for SQL injection
class NewPost(Handler):
    def get(self):
        self.render("newpage.html")
    def post(self):
        subject=self.request.get('subject')
        content=self.request.get('content')

        if subject and content:
            a=BlogEntries(subject=subject,content=content)
            a.put()
            post_id=str(a.key().id())
            self.redirect("/"+post_id)
        else:
            error="Please add both a subject and body for your blog entry!"
            self.render("newpage.html",subject=subject, content=content, error=error,)
        
#makes a page for each specific blog entry.
class BlogPage(Handler):

    def get(self, post_id):
        blogpost=BlogEntries.get_by_id(int(post_id))
        subject=blogpost.subject
        content=blogpost.content
        created=blogpost.created

        self.render('blogpage.html', subject=subject, created=created, content=content)


#okay so. for this we need to get my form HTML, (done)
#and feed the results into a script that:

# - checks to see if the user is in the database
# - hashes the password with salt(and a secret)
# - wacks the hashed password with salt, the username,
#   and the email(if extant) into a database.
# - does something with a cookie?? idk. sets it? basically logs you in.


#creates a database for the users of the blog with current needed fields
class Users(db.Model):
    name=db.StringProperty(required=True)
    password=db.StringProperty(required=True)
    token=db.StringProperty(required=True)
    email=db.StringProperty(required=False)
    signedup=db.DateTimeProperty(auto_now_add=True)
    
def UsernameVal(cursor, username):
    for each in cursor:
        if each.name==username:
                return False
    return True


class signUp(Handler):

    def get(self):
        self.render('signup.html')

    def post(self):
    
        #Validation stuff. here we need to add an SQL? query which checks if the username is already
        #in the user database. if it is it needs to add on to the user error message or add another error
        #message
        #so what we actually need to do is create a list of users and check if username is among them. 
        #!!!!!!!! man this defs allows sql injection but I'll
        #leave escaping it til I've checked the easy way to do that again
        user=""
        pass1=""
        pass2=""
        email=""
        nameval=""
        username=self.request.get('username')
        password=self.request.get('password')
        email=self.request.get('email')

        cursor=db.GqlQuery("SELECT * FROM Users")

        username_free=UsernameVal(cursor,username)
                

        
        error_mess='please enter a valid %s.'
       
        User_Name=self.request.get('username')
        #verify each input and create error messages
        ugood=valid_username(username)
        if not ugood:
            user=error_mess % 'username'
        pgood=valid_pass(password)
        if not pgood:
            pass1=error_mess % 'password'
        pgood2=password==self.request.get('verify')
        if not pgood2:
            pass2='your passwords did not match'
        egood=valid_email(email) or email==""
        if not egood:
            email=error_mess % 'email'
        if not username_free:
            nameval='the username "%s" is already in use.'%username
            
        
        #okay so, notes: when the email is blank it's all good. when it isn't,
            #and it's not a valid email address, then it's bad.
        
        
        #if all good, not only redirect to new page, but also add to the users database and set a cookie.
        if ugood and pgood and pgood2 and egood and username_free:
            hashed_pw=bcrypt.hashpw(username+password,bcrypt.gensalt(10))
            #so we made a hashed pw. this is good. I think we're good to ignore this from now on...
            #maybe it is best to produce the token using bcrypt as well?
            #we will try.
            token=bcrypt.hashpw(username,bcrypt.gensalt())
            a=Users(name=username,password=hashed_pw,email=email,token=token)
            a.put()
            userID=""
            
            cookie=
            #so first thing is to put all the data together to make the correct cookie, which is a
            #string made of userid, a pipe, and then the hashed... password?
            #actually I think it's supposed to be both username and password.
            
            #self.response.headers.add_header('Set-Cookie', 'user_id=value; Path=/')
            self.write(hashed_pw)
            #self.redirect("/welcome?username="+User_Name)
            
        else:
            #self.write(username_exists)
            self.render("signup.html", user=user,pass1=pass1,pass2=pass2,email=email,nameval=nameval)        


class Welcome(webapp2.RequestHandler):
    #I will need to get the email address to the new page. I'll need to send it by get somehow?
    #possibly actually I can just retrieve it from the database.
    #nah, nah, we get it from the cookie.
    #cookie should be named user_id
    #with the value of the User id (in the database), a pipe and a hash
    #the cookie will also need to be validated.
    #In order to get a cookie you receive from the user, you can use 'self.request.cookies.get(name)'
    #In order to send a cookie to a user, you simply add the header to your response.
    #For example, 'self.response.headers.add_header('Set-Cookie', 'name=value; Path=/')',
    #where name is the name of the cookie, and value is the value you're setting it to.


    #Model.get_by_id (ids, parent=None) 
    def get(self):
        self.response.out.write("<h1>Welcome</h1>")
        

app=webapp2.WSGIApplication([('/', MainPage),
                             ('/newpost', NewPost),
                             (r'/(\d+)', BlogPage),
                             ('/signup',signUp),
                             ('/welcome', Welcome)],debug=True)






