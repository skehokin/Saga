import os

import jinja2
import webapp2
from google.appengine.ext import db
import cgi
import re

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_pass(passw):
    return PASS_RE.match(passw)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
def valid_email(mail):
    return EMAIL_RE.match(mail)




template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


    
class Handler(webapp2.RequestHandler):
    
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)
        
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

class BlogEntries(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)

    
class MainPage(Handler):
    def get(self):
        blogposts=db.GqlQuery("SELECT * FROM BlogEntries ORDER BY created DESC")
        self.render("mainpage.html",blogposts=blogposts)

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
        

class BlogPage(Handler):

    def get(self, post_id):
        blogpost=BlogEntries.get_by_id(int(post_id))
        subject= blogpost.subject
        content=blogpost.content
        created=blogpost.created

        self.render('blogpage.html', subject=subject, created=created, content=content)



class signUp(webapp2.RequestHandler):

    def get(self):

        error_mess='please enter a valid %s.'
        input_dict={'User_Name':'','user':'', 'pass':'', 'pass2':"",'email':''}
        self.response.out.write(form % input_dict)

    def post(self):
        
        error_mess='please enter a valid %s.'
        input_dict={'User_Name':'', 'user':'', 'pass':'', 'pass2':"",'email':''}
        User_Name=self.request.get('username')
        #verify each input and create error messages
        ugood=valid_username(self.request.get('username'))
        if not ugood:
            input_dict['User_Name']=User_Name
            input_dict['user']=error_mess % 'username'
        pgood=valid_pass(self.request.get('password'))
        if not pgood:
            input_dict['pass']=error_mess % 'password'
        pgood2=self.request.get('password')==self.request.get('verify')
        if not pgood2:
            input_dict['pass2']='your passwords did not match'
        egood=valid_email(self.request.get('email')) or self.request.get('email')==""
        if not egood:
            input_dict['email']=error_mess % 'email'
        
        #okay so, notes: when the email is blank it's all good. when it isn't,
            #and it's not a valid email address, then it's bad.
        
        
        #if all good, redirect to new page
        if ugood and pgood and pgood2 and egood:
            self.redirect("/welcome?username="+User_Name)
        else:
            self.response.out.write(form % input_dict)        


class Welcome(webapp2.RequestHandler):
    #I will need to get the email address to the new page. I'll need to send it by get somehow?
    def get(self):
        username=self.request.get("username")
        self.response.out.write("<h1>Welcome, %s </h1>"% username)
        

app=webapp2.WSGIApplication([('/', MainPage),
                             ('/newpost', NewPost),
                             (r'/(\d+)', BlogPage)],debug=True)






