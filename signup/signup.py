#okay so. for this we need to get my form HTML,
#and feed the results into a script that:

# - checks to see if the user is in the database
# - hashes the password with salt(and a secret)
# - wacks the hashed password with salt, the username,
#   and the email(if extant) into a database.
# - does something with a cookie?? idk. sets it? basically logs you in.

import os
import jinja2
import webapp2

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


class MainPage(Handler):
    pass


app=webapp2.WSGIApplication([('/', MainPage)],debug=True)
