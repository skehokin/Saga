import os

import jinja2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

class BlogEntries(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    
class Handler(webapp2.RequestHandler):
    
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)
        
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

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
            self.redirect("/")
        


app=webapp2.WSGIApplication([('/', MainPage),('/newpost',NewPost)],debug=True)
