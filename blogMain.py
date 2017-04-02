import os

import jinja2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

class BlogEntries
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
        self.write("Welcome to my blog")

class NewPost(Handler):
    def get(self):
        self.render("newpage.html")
        subject=self.request.get('subject')
        content=self.request.get('content')
        


app=webapp2.WSGIApplication([('/', MainPage),('/newpost',NewPost)],debug=True)