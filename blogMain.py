import os
import jinja2
import webapp2
from google.appengine.ext import db
import cgi
import re
import random
import string
import hashlib
from libs.bcrypt import bcrypt
import unicodedata
from google.appengine.api import memcache
import datetime
import time


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
        
    def validateCookie(self):
        current_cook=self.request.cookies.get("user_id")
        if current_cook:
            cookie_vals=current_cook.split("|")
            current_user=Users.get_by_id(int(cookie_vals[0]))
            if current_user:
                if cookie_vals[1]==hashlib.sha256(current_user.name+current_user.salt).hexdigest():
                    return current_user
            return None


#create database for blog entries:
class BlogEntries(db.Model):
    author=db.StringProperty(required=True)
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    identity=db.StringProperty(required=False)
    last_edited=db.DateTimeProperty(auto_now=True)
    likes=db.StringListProperty(required=True)
    likeslength=db.IntegerProperty(required=True)
#adding caching:
def frontpage_cache(update=False):
    key="top"
    blogposts=memcache.get(key)
    if blogposts is None or update:
        blogposts= db.GqlQuery("SELECT * FROM BlogEntries ORDER BY created DESC LIMIT 10")       
        blogposts=list(blogposts)
        memcache.set(key,blogposts)
        memcache.set("tyme",time.time())
    return blogposts

def onepage_cache(ID,update=False):
    key=ID
    blogpost=memcache.get(key)
    if blogpost is None or update:
        blogpost= BlogEntries.get_by_id(int(key))   
        memcache.set(key,blogpost)
        memcache.set("time"+key,time.time())
    return blogpost

class MainPage(Handler):
    def get(self):
        userdata=self.validateCookie()
        if userdata:
            self.redirect("/"+userdata.name)
        else:
            self.render("saga.html")

#prints all posts to the home/main page:   
class BlogHome(Handler):
    def get(self, username):
        userdata=self.validateCookie()
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE name='%s'"%username)
        blogposts = db.GqlQuery("SELECT * FROM BlogEntries WHERE author='%s' ORDER BY created DESC LIMIT 10"%username)
        userbuttons=""
        if userdata:
            userbuttons="user"
            if userdata.name==username:
                userbuttons="owner"
        image="bloghero_tower_wide.jpg"
        if blog_owner_data:
            for each in blog_owner_data:
                if username==each.name and each.blog_image:
                    image=each.blog_image
        blogname=username+"'s blog"        
            
        #blogposts=frontpage_cache()
        #querytime=memcache.get("tyme")
        #now=time.time()
        #current=now-querytime
        #time=current
        self.render("bloghome.html",blogposts=blogposts,userbuttons=userbuttons,image=image,blogname=blogname)


# constructs webpage for adding new posts, including form and database entry creation
#doesn't seem like it would allow for SQL injection
class NewPost(Handler):
    def get(self):
        userdata=self.validateCookie()
        if userdata:
            image=userdata.blog_image
            blogname=userdata.name+"'s blog"
            author=userdata.name
            self.render("newpage.html", image=image, blogname=blogname, author=author)
        else:
            self.redirect("/login")
    def post(self):
        subject=self.request.get('subject')
        content=self.request.get('content')
        
        userdata=self.validateCookie()
        if subject and content:
            content="<p>"+content.replace("\n","</p>\n<p>")+"</p>"
            author=userdata.name
            a=BlogEntries(subject=subject,content=content,author=author, likes=[],likeslength=0)
            a.put()
            a.identity=str(a.key().id())
            a.put()
            post_id=a.identity
            time.sleep(1)
            frontpage_cache(True)
            self.redirect("/"+post_id)
        else:
            error="please add both a subject and body for your blog entry!"
            image=userdata.blog_image
            blogname=userdata.name+"'s blog"
            author=userdata.name
            self.render("newpage.html",subject=subject, content=content, error=error, image=image, blogname=blogname, author=author)
        
#makes a page for each specific blog entry.
class BlogPage(Handler):

    def get(self, post_id):
        userdata=self.validateCookie()
        userbuttons=""

        blogpost=onepage_cache(post_id)
        querytime=memcache.get("time"+post_id)
        now=time.time()
        current=now-querytime
        subject=blogpost.subject
        content=blogpost.content
        created=blogpost.created
        identity=blogpost.identity
        author=blogpost.author
        likeslength=blogpost.likeslength
        
        if userdata:
            userbuttons="user"
            if userdata.name==blogpost.author:
                userbuttons="owner"
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE name='%s'"%blogpost.author)
        image="bloghero_tower_wide.jpg"
        if blog_owner_data:
            for each in blog_owner_data:
                if blogpost.author==each.name and each.blog_image:
                    image=each.blog_image
        blogname=blogpost.author+"'s blog"
        
        self.render('blogpage.html', subject=subject, created=created,
                    content=content, identity=identity, time=current,
                    author=author, userbuttons=userbuttons, image=image,
                    blogname=blogname,likeslength=likeslength)


class Flush(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect("/")
        
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
    salt=db.StringProperty(required=False)
    pwsalt=db.StringProperty(required=False)
    mail=db.StringProperty(required=False)
    signedup=db.DateTimeProperty(auto_now_add=True)
    blog_image=db.StringProperty(required=False)
    
    
def UsernameVal(cursor, username):
    for each in cursor:
        if each.name==username:
                return False
    return True

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


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

            #bcrypt might take too long, hilariously. let's try sha-256 instead.
            
            static_salt=make_salt()
            hashed_pw=str(hashlib.sha256(username+password+static_salt).hexdigest())
            

            
            cur_salt=make_salt()
            
            token=hashlib.sha256(username+cur_salt).hexdigest()
            #image adds some automatic variation to each blog. The next feature, outside the scope of this project,
            #would be to make this customisable by the user.
            image_options=["bloghero_tower_wide.jpg","annie-spratt-218459.jpg",
                           "scott-webb-205351.jpg","rodrigo-soares-250630.jpg",
                           "arwan-sutanto-180425.jpg","dominik-scythe-152888.jpg",
                           "jaromir-kavan-241762.jpg","drew-hays-26240.jpg",
                           "richard-lock-262846.jpg","sam-ferrara-136526.jpg",
                           "keith-misner-308.jpg","ren-ran-232078.jpg",
                           "aaron-burden-189321.jpg","michal-grosicki-221226.jpg",
                           "joshua-earle-133254.jpg","marko-blazevic-264986.jpg",
                           "matt-thornhill-106773.jpg","camille-kmile-201915.jpg"]
            blog_image=random.choice(image_options)
            
            a=Users(name=username,password=hashed_pw,salt=cur_salt,mail=email,pwsalt=static_salt,blog_image=blog_image)
            a.put()
            userID=str(a.key().id())

            #here we put all the data together to make the correct cookie, which is a
            #string made of userid, an exclamation mark, and our token, which is the username hashed with salt.
            
            cookie_value=userID+"|"+str(token)
            
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/'%cookie_value)
            
            current_cook=self.request.cookies.get("user_id")
            self.redirect("/welcome")
            
        else:
            #self.write(username_exists)
            self.render("signup.html", user=user,pass1=pass1,pass2=pass2,email=email,nameval=nameval)
            
class logIn(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        username_exists=False
        username=self.request.get('username')
        password=self.request.get('password')
        cursor=db.GqlQuery("SELECT * FROM Users")
        for each in cursor:
            if each.name==username:
                username_exists=True
                #self.write(each.name+each.password+each.pwsalt)
                if each.password==str(hashlib.sha256(username+password+each.pwsalt).hexdigest()):
                    each.salt=make_salt()
                    each.put()
                    userID=each.key().id()
                    token=hashlib.sha256(each.name+each.salt).hexdigest()
                    cookie_value=str(userID)+"|"+str(token)
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/'%cookie_value)
                    self.redirect("/welcome")

                    
                else:
                   self.render("login.html",error="invalid login")
        if username_exists==False:
                self.render("login.html",error="invalid login")

class logOut(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/'%"")
        self.redirect("/signup")
class Welcome(Handler):
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
        current_cook=self.request.cookies.get("user_id")
        if current_cook:
            cookie_vals=current_cook.split("|")
            current_user=Users.get_by_id(int(cookie_vals[0]))
            if current_user:
                if cookie_vals[1]==hashlib.sha256(current_user.name+current_user.salt).hexdigest():
                    self.redirect ("/"+current_user.name)
                else:
                    #self.write("cookie vals 1:"+cookie_vals[1]+" hash I made jsut now: "+hashlib.sha256(current_user.name+current_user.salt).hexdigest()+" user: "+current_user.name+" salt:"+current_user.salt)
                    self.redirect("/signup")
            else:
                self.redirect("/signup")
                #self.write("user:"+cookie_vals[0])
        else:
            self.redirect("/signup")

def JSONconvert(cursor):
    entrylist=[]
    for entry in cursor:
        entrydict={
            'subject':str(entry.subject),
            'content':unicodedata.normalize('NFKD',entry.content).encode('ascii','ignore'),
            'created':str(entry.created)
            }
        entrylist.append(entrydict)
    a=str(entrylist).replace('"',"@").replace("'",'"').replace("@","'")
    
    return a
def JSONconvert2(post):

    entrydict={
        'subject':str(post.subject),
        'content':unicodedata.normalize('NFKD',post.content).encode('ascii','ignore'),
        'created':post.created.strftime("%H:%M on %A %d %B %Y")
        }
    a=str(entrydict).replace('"',"@").replace("'",'"').replace("@","'")
    
    return a

class jsonApi (Handler):
    def get(self):
        self.response.headers.add_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(JSONconvert(db.GqlQuery("SELECT * FROM BlogEntries ORDER BY created DESC")))
    
class jsonApiIndiv (Handler):
        def get(self, post_id):
            self.response.headers.add_header('Content-Type', 'application/json; charset=UTF-8')
            blogpost=BlogEntries.get_by_id(int(post_id))
            ## ^^ fuck I think I should have used this approach
            self.write(JSONconvert2(blogpost))
class EditPage(Handler):
    def get(self, post_id):
        content=""
        subject=""
        userdata=self.validateCookie()
        if not userdata:
            self.redirect("/login")
            
        else:
            cursor= db.GqlQuery("SELECT * FROM BlogEntries WHERE identity='%s'"% post_id)
            for each in cursor:
                if each.identity==post_id:
                    if userdata.name==each.author: 
                        content=each.content[3:-4].replace("</p>\n<p>","\n")
                        subject=each.subject
                        self.render("newpage.html", subject=subject, content=content)
                    else:
                        self.redirect("/"+post_id)

    def post(self,post_id):
        content=""
        userdata=self.validateCookie()
        if not userdata:
            self.redirect("/login")
        else:
            cursor= db.GqlQuery("SELECT * FROM BlogEntries WHERE identity='%s'"% post_id)
            for each in cursor:
                if each.identity==post_id:
                    if userdata.name!=each.author:
                        self.redirect("/"+post_id)
                    else:
                        subject=self.request.get('subject')
                        content=self.request.get('content')
                        if content and subject:
                            content="<p>"+content.replace("\n","</p>\n<p>")+"</p>"
                            cursor= db.GqlQuery("SELECT * FROM BlogEntries WHERE identity='%s'"%post_id)
                            for each in cursor:
                                if each.identity==post_id:
                                    each.subject=subject
                                    each.content=content
                                    each.put()
                                    time.sleep(1)
                                    frontpage_cache(True)
                                    onepage_cache(post_id,True)
                                    self.redirect("/"+post_id)

                        else:
                            error="please add both a subject and body for your blog entry!"
                            self.render("newpage.html",subject=subject, content=content, error=error)

class DeletePost(Handler):
        def get(self, post_id):
            userdata=self.validateCookie()
            blogpost=BlogEntries.get_by_id(int(post_id))
            if blogpost:    
                if not userdata:
                    self.redirect("/login")
                elif blogpost.author!=userdata.name:
                    self.redirect("/"+post_id)
                else:
                    cursor= db.GqlQuery("SELECT * FROM BlogEntries WHERE identity='%s'"%post_id)
                    for each in cursor:
                        if each.identity==post_id:
                            each.delete()
                            time.sleep(1)
                            frontpage_cache(True)
                            onepage_cache(post_id,True)
                            self.redirect("/"+userdata.name)
                
class LikePost(Handler):
        def get(self, post_id):
            userdata=self.validateCookie()
            blogpost=BlogEntries.get_by_id(int(post_id))
            if blogpost:    
                if not userdata:
                    self.redirect("/login")
                elif blogpost.author!=userdata.name:
                    cursor= db.GqlQuery("SELECT * FROM BlogEntries WHERE identity='%s'"%post_id)
                    for each in cursor:
                        if each.identity==post_id:
                            if userdata.name in each.likes:
                                self.redirect("/"+post_id)
                            else:
                                each.likes.append(userdata.name)
                                each.likeslength=len(each.likes)
                            each.put()
                            time.sleep(1)
                            frontpage_cache(True)
                            onepage_cache(post_id,True)
                            self.redirect("/"+post_id)
                else:
                    self.redirect("/"+post_id)
                
            
    
app=webapp2.WSGIApplication([('/', MainPage),
                             ('/newpost', NewPost),
                             (r'/(\d+)', BlogPage),
                             (r'/(\d+).json', jsonApiIndiv),
                             ('/signup',signUp),
                             ('/welcome', Welcome),
                             ('/login', logIn),
                             ('/logout', logOut),
                             ('/.json', jsonApi),
                             ('/flush', Flush),
                             (r'/_edit/(\d+)', EditPage),
                             (r'/_delete/(\d+)', DeletePost),
                             (r'/_like/(\d+)', LikePost),
                             (r'/(.*)', BlogHome)],debug=True)






