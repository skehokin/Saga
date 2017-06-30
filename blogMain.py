import os
import re
import random
import string
import hashlib
import unicodedata
import time
import jinja2
import webapp2
from google.appengine.ext import db
from google.appengine.api import memcache

#This sets up the regular expressions and 
#uses each in a function which checks if
#certain inputs are valid:
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

def valid_username(username):
    """Checks a username against the USER_RE regex. 
    """
    return USER_RE.match(username)

def valid_pass(passw):
    """Checks a password against the PASS_RE regex. 
    """
    return PASS_RE.match(passw)

def valid_email(mail):
    """Checks an email address against the EMAIL_RE regex. 
    """
    return EMAIL_RE.match(mail)

# Sets up template paths:
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):
    """This handler class extends the webapp2 RequestHandler class,
    and was primarily created by Steve Huffman to reduce the difficulty
    of typing out the webapp2 write function and the jinja2 template
    rendering process. The cookie validation function was later added
    by Siobhan Hokin.
    """

    def write(self, *a, **kw):
        """This shortens the webapp2 write function so it is called
        with just "self.write".
        """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """This function is used as part of the final render function,
        which can be used to shortcut rendering a jinja2 template. It
        retrieves the requisite html template and includes the given
        keywords in the template.
        """
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        """This function is the final one in the jinja2 template rendering
        shortcut. It writes the template (put together by render_str) to the
        output website.
        """
        self.write(self.render_str(template, **kw))

    def validate_cookie(self):
        """This function is a summary of the "Welcome" handler's activity:
        it checks to make sure that the the login cookie is legitimate -
        the same as a cookie created by the info in the User database.
        if so, it returns the current user's data.
        """
        current_cook = self.request.cookies.get("user_id")
        if current_cook:
            cookie_vals = current_cook.split("|")
            current_user = Users.get_by_id(int(cookie_vals[0]))
            if current_user:
                should_cookie = hashlib.sha256(current_user.name
                                               + current_user.salt).hexdigest()
                if cookie_vals[1] == should_cookie:
                    return current_user
            return None


### Databases

# Create database for blog entries:
class BlogEntries(db.Model):
    """Not much to explain here. This class creates a new data entry for
    datastore as per the model instance docs:
    https://cloud.google.com/appengine/docs/standard/python/datastore/modelclass
    This one is for blog entries.
    """
    author = db.StringProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    identity = db.StringProperty(required=False)
    last_edited = db.DateTimeProperty(auto_now=True)
    likes = db.StringListProperty(required=True)
    likes_length = db.IntegerProperty(required=True)


# Create database for Comment entries:
class Comments(db.Model):
    """Not much to explain here. This class creates a new data entry for
    datastore as per the Model instance docs:
    https://cloud.google.com/appengine/docs/standard/python/datastore/modelclass
    This one is for comments on blog posts.
    """
    author = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    post_identity = db.StringProperty(required=True)
    last_edited = db.DateTimeProperty(auto_now=True)
    comment_id = db.StringProperty(required=False)
    blog_loc = db.StringProperty(required=True)


class Users(db.Model):
    """Not much to explain here. This class creates a new data entity for
    datastore as per the model instance docs:
    https://cloud.google.com/appengine/docs/standard/python/datastore/modelclass
    This one is for blog user data.
    """
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    salt = db.StringProperty(required=False)
    pwsalt = db.StringProperty(required=False)
    mail = db.StringProperty(required=False)
    signed_up = db.DateTimeProperty(auto_now_add=True)
    blog_image = db.StringProperty(required=False)


# Caching functions:
def frontpage_cache(update=False):
    """This function does one of two things: updates memcache, or gives
    the current memcache value for the front page.
    Pretty sure the code has changed so it's no longer useful, though.
    """
    key = "top"
    blog_posts = memcache.get(key)
    if blog_posts is None or update:
        blog_posts = db.GqlQuery("SELECT * FROM BlogEntries ORDER BY "
                                 "created DESC LIMIT 10")
        blog_posts = list(blog_posts)
        memcache.set(key, blog_posts)
        memcache.set("tyme", time.time())
    return blog_posts


def onepage_cache(ID, update=False):
    """This function does one of two things: updates memcache, or gives
    the current memcache value for a single given page.
    Pretty sure the code has changed so it's no longer useful, though.
    """
    key = ID
    blog_post = memcache.get(key)
    if blog_post is None or update:
        blog_post = BlogEntries.get_by_id(int(key))
        memcache.set(key, blog_post)
        memcache.set("time"+key, time.time())
    return blog_post

# User account validating functions
def username_val(cursor, username):
    """Checks to see if the requested username already exists.
    """
    for each in cursor:
        if each.name == username:
            return False
    return True

def make_salt():
    """Makes a random 5-letter salt to add to any hashing security
    measures. This is Steven Huffman's version.
    """
    return ''.join(random.choice(string.letters)for x in xrange(5))

#JSON functions
def json_convert(cursor):
    """This function converts an entire set of blog entries to JSON"""
    entrylist = []
    for entry in cursor:
        content = unicodedata.normalize('NFKD', entry.content)
        content = content.encode('ascii', 'ignore')
        entrydict = {
            'subject': str(entry.subject),
            'content': content,
            'created': str(entry.created)
            }
        entrylist.append(entrydict)
    a = str(entrylist).replace('"', "@").replace("'", '"').replace("@", "'")
    return a


def json_convert_indiv(post):
    """This function converts a single blog entry to JSON"""
    content = unicodedata.normalize('NFKD', post.content)
    content = content.encode('ascii', 'ignore')
    entrydict = {
        'subject': str(post.subject),
        'content': content,
        'created': post.created.strftime("%H:%M on %A %d %B %Y")
        }
    a = str(entrydict).replace('"', "@").replace("'", '"').replace("@", "'")
    return a


### Handlers that render pages.

class MainPage(Handler):
    """Renders the saga main page, or redirects to a user's blog homepage.
    """

    def get(self):
        """Renders the saga main page, or redirects to a user's blog
        homepage.
        """
        user_data = self.validate_cookie()
        if user_data:
            self.redirect("/"+user_data.name)
        else:
            self.render("saga.html")


class SignUp(Handler):
    """Renders the saga signup form, then, if all the given user data is
    acceptable, stores the user data in the User database,
    "signing up the user" and creates and sets the login cookie.
    """

    def get(self):
        """Renders a simple signup form with no customised elements.
        """
        self.render('signup.html')

    def post(self):
        """Takes the user data, checks it, creates any needed error
        messages, and finally either stores the data and creates the login
        cookie, or issues a new copy of the form with errors for the user
        to correct.
        """
        user = ""
        pass1 = ""
        pass2 = ""
        email = ""
        nameval = ""
        username = self.request.get('username')
        password = self.request.get('password')
        email = self.request.get('email')
        cursor = db.GqlQuery("SELECT * FROM Users")
        username_free = username_val(cursor, username)
        error_mess = 'please enter a valid %s'
        #verify each input and create error messages
        ugood = valid_username(username)
        if not ugood or username.isdigit():
            user = error_mess % 'username'
        pgood = valid_pass(password)
        if not pgood:
            pass1 = error_mess % 'password'
        pgood2 = password == self.request.get('verify')
        if not pgood2:
            pass2 = 'your passwords did not match'
        egood = valid_email(email) or email == ""
        if not egood:
            email = error_mess % 'email'
        if not username_free:
            nameval = 'the username "%s" is already in use.' % username

        if ugood and pgood and pgood2 and egood and username_free:
            static_salt = make_salt()
            values = username + password + static_salt
            hashed_pw = str(hashlib.sha256(values).hexdigest())
            cur_salt = make_salt()
            token = hashlib.sha256(username+cur_salt).hexdigest()
            # A random image adds some automatic variation to each blog. 
            # The next feature, outside the scope of this project,
            # would be to make this customisable by the user.
            image_options = ["bloghero_tower_wide.jpg", 
                             "annie-spratt-218459.jpg",
                             "scott-webb-205351.jpg",
                             "rodrigo-soares-250630.jpg",
                             "arwan-sutanto-180425.jpg",
                             "dominik-scythe-152888.jpg",
                             "jaromir-kavan-241762.jpg",
                             "drew-hays-26240.jpg",
                             "richard-lock-262846.jpg",
                             "sam-ferrara-136526.jpg",
                             "keith-misner-308.jpg",
                             "ren-ran-232078.jpg",
                             "aaron-burden-189321.jpg",
                             "michal-grosicki-221226.jpg",
                             "joshua-earle-133254.jpg",
                             "marko-blazevic-264986.jpg",
                             "matt-thornhill-106773.jpg",
                             "camille-kmile-201915.jpg"]
            blog_image = random.choice(image_options)
            a = Users(name=username, password=hashed_pw, salt=cur_salt,
                      mail=email, pwsalt=static_salt, blog_image=blog_image)
            a.put()
            userID = str(a.key().id())
            # Here we put all the data together to make the correct
            # cookie, which is a string made of userid, a bar symbol,
            # and our token, which is the username hashed with salt.
            cookie_value = userID+"|"+str(token)
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/'
                                             % cookie_value)
            self.redirect("/")
        else:
            self.render("signup.html", user=user, pass1=pass1, pass2=pass2, 
                        email=email, nameval=nameval)


class LogIn(Handler):
    """Renders a basic login page for saga, then if all the data
    is correct, creates a new login cookie, with a new salt,
    and enters that into the database. This means that even if cookie
    theft were to happen, it would only be valid until the account-owner
    goes through the login process again.
    """

    def get(self):
        """Renders the login form.
        """
        self.render("login.html")

    def post(self):
        """Checks the data posted from the login form, constructs and sets
        the login cookie if appropriate, re-displays the login form with an
        error if not.
        """
        username_exists = False
        username = self.request.get('username')
        password = self.request.get('password')
        cursor = db.GqlQuery("SELECT * FROM Users")
        for each in cursor:
            if each.name == username:
                username_exists = True
                values_hash = hashlib.sha256(username + password + each.pwsalt)
                if each.password == str(values_hash.hexdigest()):
                    each.salt = make_salt()
                    each.put()
                    userID = each.key().id()
                    token = hashlib.sha256(each.name+each.salt).hexdigest()
                    cookie_value = str(userID)+"|"+str(token)
                    self.response.headers.add_header('Set-Cookie',
                                                     'user_id=%s; Path=/'
                                                     % cookie_value)
                    self.redirect("/")

                else:
                    self.render("login.html", error="invalid login")
        if not username_exists:
            self.render("login.html", error="invalid login")


#prints all posts to the home/main page:
class BlogHome(Handler):
    """Renders any blog's homepage.
    """

    def get(self, username):
        """Renders any blog's homepage based on the username in the URL.
        Also handles pre-entering comment data into the comments form for
        comment editing initiated on this page.
        """
        edit_comment_id = ""
        post_id = ""
        comment_content = ""
        user_buttons = ""
        logged_in_user = ""
        user_data = self.validate_cookie()
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE "
                                      "name='%s'"%username)
        blog_posts = db.GqlQuery("SELECT * FROM BlogEntries WHERE author='%s' "
                                 "ORDER BY created DESC LIMIT 10"%username)
        if user_data:
            edit_comment_id = self.request.get("comment_id")
            if edit_comment_id:
                edit_comment = db.GqlQuery("SELECT * FROM Comments WHERE "
                                           "comment_id='%s'"%edit_comment_id)
                if edit_comment:
                    for each in edit_comment:
                        if user_data.name == each.author:
                            post_id = each.post_identity
                            comment_content = each.content
                        else:
                            self.redirect("/"+username)
            user_buttons = "user"
            logged_in_user = user_data.name
            if user_data.name == username:
                user_buttons = "owner"
        image = "bloghero_tower_wide.jpg"
        exists = False
        if blog_owner_data:
            for each in blog_owner_data:
                exists = True
                if username == each.name and each.blog_image:
                    image = each.blog_image
        if not exists:
            self.redirect("/oops")
        blog_name = username+"'s blog"

        #blog_posts=frontpage_cache()
        #querytime=memcache.get("tyme")
        #now=time.time()
        #current=now-querytime
        #time=current

        website_type = "home"
        comments = db.GqlQuery("SELECT * FROM Comments WHERE blog_loc='%s' "
                               "ORDER BY created"%username)
        self.render("bloghome.html", user_buttons=user_buttons, image=image,
                    blog_name=blog_name, comments=comments, username=username,
                    logged_in_user=logged_in_user,
                    edit_comment_id=edit_comment_id,
                    post_id=post_id, comment_content=comment_content,
                    website_type=website_type, blog_posts=blog_posts)

    def post(self, username):
        """Takes the comment data from a blog homepage and enters it into
        the Comment database.
        """
        user_data = self.validate_cookie()
        content = self.request.get('content')
        if not user_data or not content:
            self.redirect("/"+username)
        comment_id = self.request.get("comment_id")
        if comment_id:
            edit_comment = db.GqlQuery("SELECT * FROM Comments WHERE "
                                       "comment_id='%s'" % comment_id)
            for each in edit_comment:
                if user_data.name == each.author:
                    each.content = content
                    each.put()
                else:
                    self.redirect("/"+username)
        else:
            author = user_data.name
            post_identity = self.request.get('post_id')
            a = Comments(content=content, author=author,
                         post_identity=post_identity, blog_loc=username)
            a.put()
            a.comment_id = str(a.key().id())
            a.put()
        time.sleep(1)
        frontpage_cache(True)
        self.redirect("/"+username)


class BlogPage(Handler):
    """Renders the appropriate webpage for any single blog entry, also
    stores any comment data entered on that page.
    """

    def get(self, post_id):
        """Sets up and renders a page for a single blog entry, based
        on the entry data and the author's customised blog appearance.
        Also handles pre-entering comment data into the comments form for
        any comment editing initiated on this page.
        """
        edit_comment_id = ""
        comment_content = ""
        blog_post = BlogEntries.get_by_id(int(post_id))
        username = blog_post.author
        user_data = self.validate_cookie()
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE "
                                      "name='%s'" % username)
        blog_posts = db.GqlQuery("SELECT * FROM BlogEntries WHERE "
                                 "identity='%s'" % post_id)
        user_buttons = ""
        logged_in_user = ""
        post_id = ""
        if user_data:
            edit_comment_id = self.request.get("comment_id")
            if edit_comment_id:
                edit_comment = db.GqlQuery("SELECT * FROM Comments WHERE "
                                           "comment_id='%s'" % edit_comment_id)
                if edit_comment:
                    for each in edit_comment:
                        if user_data.name == each.author:
                            post_id = each.post_identity
                            comment_content = each.content
                        else:
                            self.redirect("/"+username)
            user_buttons = "user"
            logged_in_user = user_data.name
            if user_data.name == username:
                user_buttons = "owner"
        image = "bloghero_tower_wide.jpg"
        if blog_owner_data:
            for each in blog_owner_data:
                if username == each.name and each.blog_image:
                    image = each.blog_image
        blog_name = username+"'s blog"
        #blog_posts=frontpage_cache()
        #querytime=memcache.get("tyme")
        #now=time.time()
        #current=now-querytime
        #time=current
        comments = db.GqlQuery("SELECT * FROM Comments WHERE blog_loc='%s' "
                               "ORDER BY created" %username)
        self.render("bloghome.html", blog_posts=blog_posts,
                    user_buttons=user_buttons, image=image,
                    blog_name=blog_name, comments=comments,
                    username=username, logged_in_user=logged_in_user,
                    edit_comment_id=edit_comment_id, post_id=post_id,
                    comment_content=comment_content, website_type="single")

    def post(self, post_id):
        """Takes the comment data from a single blog page and enters it into
        the Comment database.
        """
        blog_post = BlogEntries.get_by_id(int(post_id))
        username = blog_post.author
        user_data = self.validate_cookie()
        content = self.request.get('content')
        if not user_data or not content:
            self.redirect("/"+username)
        comment_id = self.request.get("comment_id")
        if comment_id:
            edit_comment = db.GqlQuery("SELECT * FROM Comments WHERE "
                                       "comment_id='%s'"%comment_id)
            for each in edit_comment:
                if user_data.name == each.author:
                    each.content = content
                    each.put()
                else:
                    self.redirect("/"+username)
        else:
            blog_loc_search = db.GqlQuery(("SELECT * FROM BlogEntries "
                                           "WHERE identity='%s'"%post_id))
            if blog_loc_search:
                for each in blog_loc_search:
                    if each.identity == post_id:
                        blog_loc = each.author
            post_identity = self.request.get('post_id')
            author = user_data.name
            a = Comments(content=content, author=author,
                         post_identity=post_identity, blog_loc=blog_loc)
            a.put()
            a.comment_id = str(a.key().id())
            a.put()
        time.sleep(1)
        frontpage_cache(True)
        self.redirect("/"+post_id)


# constructs webpage for adding new posts, including form and database entry creation
#doesn't seem like it would allow for SQL injection
class NewPost(Handler):
    """Renders a form then acts upon the given data, adding it as a new
    blog entry.
    """

    def get(self):
        """Renders a new post form with the user's custom data.
        """
        user_data = self.validate_cookie()
        if user_data:
            image = user_data.blog_image
            blog_name = user_data.name+"'s blog"
            author = user_data.name
            self.render("newpage.html", image=image, blog_name=blog_name,
                        author=author)
        else:
            self.redirect("/login")

    def post(self):
        """Checks the new post data, and either enters it into the database,
        or asks again for the right data.
         """
        subject = self.request.get('subject')
        content = self.request.get('content')

        user_data = self.validate_cookie()
        if subject and content:
            content = "<p>"+content.replace("\n", "</p>\n<p>")+"</p>"
            author = user_data.name
            a = BlogEntries(subject=subject, content=content, author=author,
                            likes=[], likes_length=0)
            a.put()
            a.identity = str(a.key().id())
            a.put()
            post_id = a.identity
            time.sleep(1)
            frontpage_cache(True)
            self.redirect("/"+post_id)
        else:
            error = "please add both a subject and body for your blog entry!"
            image = user_data.blog_image
            blog_name = user_data.name+"'s blog"
            author = user_data.name
            self.render("newpage.html", subject=subject, content=content,
                        error=error, image=image, blog_name=blog_name, 
                        author=author)


class EditPage(Handler):
    """This handler allows for the editing of blog posts by the user who
    originally made them. It uses the same newpage.html form as the
    NewPost handler, but enters the data from the requested blog post.
    """

    def get(self, post_id):
        """retrieving the post id from the URL, this function finds the user
        data appropriate to the logged in user, checking that the user is also
        the author of the post. This and the post's data are used to
        create the edit page."""
        content = ""
        subject = ""
        user_data = self.validate_cookie()
        if not user_data:
            self.redirect("/login")
        else:
            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                 "WHERE identity='%s'" % post_id)
            for each in cursor:
                if each.identity == post_id:
                    if user_data.name == each.author:
                        image = user_data.blog_image
                        content = each.content[3:-4].replace("</p>\n<p>", "\n")
                        subject = each.subject
                        self.render("newpage.html", subject=subject,
                                    content=content, image=image)
                    else:
                        self.redirect("/"+post_id)

    def post(self, post_id):
        """Once the edit form has been posted, this function overwrites
        the content of the original post with the new content.
        """
        content = ""
        user_data = self.validate_cookie()
        if not user_data:
            self.redirect("/login")
        else:
            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                 "WHERE identity='%s'" % post_id)
            for each in cursor:
                if each.identity == post_id:
                    if user_data.name != each.author:
                        self.redirect("/"+post_id)
                    else:
                        subject = self.request.get('subject')
                        content = self.request.get('content')
                        image = user_data.blog_image
                        if content and subject:
                            content = content.replace("\n", "</p>\n<p>")
                            content = "<p>"+content+"</p>"
                            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                                 "WHERE identity='%s'"
                                                 % post_id)
                            for each in cursor:
                                if each.identity == post_id:
                                    each.subject = subject
                                    each.content = content
                                    each.put()
                                    time.sleep(1)
                                    frontpage_cache(True)
                                    onepage_cache(post_id, True)
                                    self.redirect("/"+post_id)
                        else:
                            error = ("please add both a subject and "
                                     "body for your blog entry!")
                            self.render("newpage.html", subject=subject,
                                        content=content, error=error,
                                        image=image)


class Oops(Handler):
    """This is the "404" page, which is visited each time a post or
    user page proves not to exist.
    """
    def get(self):
        self.render("oops.html")


### Utility handlers that don't render webpages.


class DeletePost(Handler):
    """This handler allows a user to delete a blog entry they wrote.
    """

    def get(self, post_id):
        """This function retrieves the post id from the URL and, after
        checking that the user is the author of the post, deletes it
        from the database.
        """
        user_data = self.validate_cookie()
        blog_post = BlogEntries.get_by_id(int(post_id))
        if blog_post:
            if not user_data:
                self.redirect("/login")
            elif blog_post.author != user_data.name:
                self.redirect("/"+post_id)
            else:
                cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                     "WHERE identity='%s'"%post_id)
                for each in cursor:
                    if each.identity == post_id:
                        each.delete()
                        time.sleep(1)
                        frontpage_cache(True)
                        onepage_cache(post_id, True)
                        self.redirect("/"+user_data.name)


class LikePost(Handler):
    """This Handler allows any user to like a post they did not write.
    This is limited to only one like per user per post.
    """

    def get(self, post_id):
        """After checking that the user making this request is not the
        author of the post, the user's name is added to a list of users
        who have liked the post, which is recorded in the post's database
        entry. This list is checked each time anyone attempts to like a
        post, so they can only like the post once. The current length
        of this list is also recorded in the database for easy addition
        to the blog post representations on the website.
        """
        user_data = self.validate_cookie()
        blog_post = BlogEntries.get_by_id(int(post_id))
        if blog_post:
            if not user_data:
                self.redirect("/login")
            elif blog_post.author != user_data.name:
                cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                     "WHERE identity='%s'" % post_id)
                for each in cursor:
                    if each.identity == post_id:
                        if user_data.name in each.likes:
                            self.redirect("/"+post_id)
                        else:
                            each.likes.append(user_data.name)
                            each.likes_length = len(each.likes)
                        each.put()
                        time.sleep(1)
                        frontpage_cache(True)
                        onepage_cache(post_id, True)
                        self.redirect("/"+post_id)
            else:
                self.redirect("/"+post_id)


class DeleteComment(Handler):
    """This handler allows the author of a comment to delete it"""

    def get(self, comment_id):
        """This function allows the author of a comment to delete it.
        It then redirects to the page the user was on previously,
        using data posted by the comment delete button."""
        user_data = self.validate_cookie()
        comment = Comments.get_by_id(int(comment_id))
        if comment:
            website_type = self.request.get("website_type")
            if website_type == "home":
                target = comment.blog_loc
            else:
                target = comment.post_identity

            post_loc = comment.post_identity
            if not user_data:
                self.redirect("/login")
            elif comment.author != user_data.name:
                self.redirect("/"+target)
            else:
                cursor = db.GqlQuery("SELECT * FROM Comments "
                                     "WHERE comment_id='%s'"%comment_id)
                for each in cursor:
                    if each.comment_id == comment_id:
                        each.delete()
                        time.sleep(1)
                        frontpage_cache(True)
                        onepage_cache(post_loc, True)
                        self.redirect("/"+target)
        else:
            self.redirect("/")


class LogOut(Handler):
    """Deletes the cookie content to log out the user.
    """
    def get(self):
        """Deletes the cookie content to log out the user.
        """
        self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/'%"")
        self.redirect("/signup")


class Flush(Handler):
    """Removes all data from the cache.
    """
    def get(self):
        """Removes all data from the cache.
        """
        memcache.flush_all()
        self.redirect("/")


class JsonApi(Handler):
    """This API uses the JSON convert function to create a JSON version of
    all the blog entries"""

    def get(self):
        """This function uses the JSON convert function to create a JSON 
        version of all the blog entries"""
        self.response.headers.add_header('Content-Type',
                                         'application/json; charset=UTF-8')
        self.write(json_convert(db.GqlQuery("SELECT * FROM BlogEntries "
                                           "ORDER BY created DESC")))


class JsonApiIndiv(Handler):
    """This API uses the JSON convert function to create a JSON version of
    a single blog entry"""
    
    def get(self, post_id):
        """This function uses the JSON convert function to create a 
        JSON version of a single blog entry"""
        self.response.headers.add_header('Content-Type',
                                         'application/json; charset=UTF-8')
        blog_post = BlogEntries.get_by_id(int(post_id))
        self.write(json_convert_indiv(blog_post))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPost),
                               ('/oops', Oops),
                               (r'/(\d+)', BlogPage),
                               (r'/(\d+).json', JsonApiIndiv),
                               ('/signup', SignUp),
                               ('/login', LogIn),
                               ('/logout', LogOut),
                               ('/.json', JsonApi),
                               ('/flush', Flush),
                               (r'/_edit/(\d+)', EditPage),
                               (r'/_delete/(\d+)', DeletePost),
                               (r'/_commentdelete/(\d+)', DeleteComment),
                               (r'/_like/(\d+)', LikePost),
                               (r'/(.*)', BlogHome)], debug=True)
