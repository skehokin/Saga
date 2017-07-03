import os
import re
import random
import string
import hashlib
import time
import jinja2
import webapp2
from google.appengine.ext import db


# This sets up the regular expressions and
# uses each in a function which checks if
# certain inputs are valid:
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")


def valid_username(username):
    """Check a username against the USER_RE regex."""
    return USER_RE.match(username)


def valid_pass(passw):
    """Check a password against the PASS_RE regex."""
    return PASS_RE.match(passw)


def valid_email(mail):
    """Check an email address against the EMAIL_RE regex."""
    return EMAIL_RE.match(mail)


# Sets up template paths:
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                               autoescape=True)


class Handler(webapp2.RequestHandler):
    """Extend the webapp2 RequestHandler class for quick access.

    Primarily created by Steve Huffman to reduce the difficulty
    of typing out the webapp2 write function and the jinja2 template
    rendering process. The cookie validation function was later added
    by Siobhan Hokin.
    """

    def write(self, *a, **kw):
        """Shorten the webapp2 response.write function.

        Alter the webapp2 response object - the final HTTP
        response. A guide to the webapp2 response object can be
        found here:
        http://webapp2.readthedocs.io/en/latest/guide/response.html

        Args:
          *a:
            Typically a string representing an HTML webpage. Can
            also be any other object, although if expected to be
            human-readble, the object must usually be human-readable
            without any interfacing commands, e.g. lists, intergers.
          **kw:
            I honestly have no idea why response.write would take any
            keyword arguments. But if you figure out why, you can add
            them in with no trouble.
          """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """Create a string from a jinja2 template and variables.

        Args:
          template:
            The file name of a jinja2 HTML template which is located
            in the "templates" folder, which was set up earlier in the
            module.
            The jinja2 documentation is available here:
            http://jinja.pocoo.org/docs/2.9/templates/
          **params:
            Any number of variables which are already part of the
            given jinja2 template. The function of these variables is
            similar to string formatting. Quite often these variables
            are also strings, but they can also be dictionaries, lists,
            or other iterables.
            Once again, the relevant
            documentation is available here:
            http://jinja.pocoo.org/docs/2.9/templates/

        Returns:
          A string, which is the complete HTML of a website. Any
          jinja2 syntax or undefined variables within the template
          will be omitted.
        """
        temp = JINJA_ENV.get_template(template)
        return temp.render(params)

    def render(self, template, **kw):
        """Write the filled-out jinja2 template to the response object.

        Call the above two functions (write and render_str) to first
        retrieve a jinja2 template, fill it out with the requisite
        variables, and then write it as a string to the response object.

        Args:
          template:
            The file name of a jinja2 HTML template which is located
            in the "templates" folder, which was set up earlier in the
            module.
            The jinja2 documentation is available here:
            http://jinja.pocoo.org/docs/2.9/templates/
          **kw:
            Any number of variables which are already part of the
            given jinja2 template. The function of these variables is
            similar to string formatting. Quite often these variables
            are also strings, but they can also be dictionaries, lists,
            or other iterables, as some python-like syntax ("tags")
            are available within templates.
            A keyword argument should here be entered in the form of:
            name_of_variable_in_template=data_to_be_filled_in
            Once again, the relevant
            documentation is available here:
            http://jinja.pocoo.org/docs/2.9/templates/
        """
        self.write(self.render_str(template, **kw))

    def validate_cookie(self):
        """ Validate the login cookie and retrieve user data.

        Returns:
          The database entity representing the logged in user, or
          if the cookie is invalid, returns None.
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


# User account validation functions
def username_val(cursor, username):
    """Check to see if the requested username already exists.

    Args:
      cursor: a GqlQuery object, querying the User database and including
        all columns.
        Docs for the GqlQuery class can be found here:
        https://cloud.google.com/appengine/docs/standard/python/datastore/gqlqueryclass
      username: Any valid username (doesn't violate the USER_RE regex
        and is not a number.)

    Returns:
      A Boolean representing the validity of the username: False if it
      already used, True if it is not yet in the database.
    """
    for each in cursor:
        if each.name == username:
            return False
    return True


def make_salt():
    """Make a pseudo-random 5-letter salt for security hashing.

    Originally written by Steven Huffman.

    Returns:
        A pseudo-random 5-letter string.
    """
    return "".join(random.choice(string.letters)for x in xrange(5))


### Handlers that render pages.

class MainPage(Handler):
    """Render the saga main page, or redirect to a user's blog homepage."""

    def get(self):
        """Render the saga main page/redirect to a user's blog homepage.

        Render the page usually available at "/" - the "saga" homepage,
        or, if there is a valid logged-in user, redirect to that user's
        blog homepage.
        """
        user_data = self.validate_cookie()
        if user_data:
            self.redirect("/"+user_data.name)
        else:
            self.render("saga.html")


class SignUp(Handler):
    """Render the saga signup form, then, if all the given user data is
    acceptable, store the user data in the User database,
    "signing up the user". Create and set the login cookie.
    """

    def get(self):
        """Render a simple saga signup form with no customised elements."""
        self.render("signup.html")

    def post(self):
        """Sign-up the user or give same sign-up form with errors.

        Take the user data, validate it, create any needed error
        messages, and finally either store the data and create the login
        cookie, or issue a new copy of the form with errors for the user
        to correct.
        """
        user = ""
        pass1 = ""
        pass2 = ""
        email = ""
        nameval = ""
        username = self.request.get("username")
        password = self.request.get("password")
        email = self.request.get("email")
        cursor = db.GqlQuery("SELECT * FROM Users")
        username_free = username_val(cursor, username)
        error_mess = "please enter a valid %s"
        # verify each input and create error messages
        ugood = valid_username(username)
        if not ugood or username.isdigit():
            user = error_mess % "username"
        pgood = valid_pass(password)
        if not pgood:
            pass1 = error_mess % "password"
        pgood2 = password == self.request.get("verify")
        if not pgood2:
            pass2 = "your passwords did not match"
        egood = valid_email(email) or email == ""
        if not egood:
            email = error_mess % "email"
        if not username_free:
            nameval = "the username '%s' is already in use." % username

        if ugood and pgood and pgood2 and egood and username_free:
            static_salt = make_salt() # To be hashed with the password.
            values = username + password + static_salt
            hashed_pw = str(hashlib.sha256(values).hexdigest())
            # cur_salt is hashed with the user ID for the cookie.
            # It changes each time the user logs in.
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
            # Place the new user's data in the Users database.
            new_entity = Users(name=username, password=hashed_pw,
                               salt=cur_salt, mail=email, pwsalt=static_salt,
                               blog_image=blog_image)
            new_entity.put()
            user_id = str(new_entity.key().id())
            # Here we put all the data together to make the correct
            # cookie, which is a string made of the user ID, a bar symbol,
            # and our token, which is the username hashed with salt.
            cookie_value = user_id+"|"+str(token)
            self.response.headers.add_header("Set-Cookie", "user_id=%s; Path=/"
                                             % cookie_value)
            self.redirect("/")
        else:
            # The sign-up page with relevant errors.
            self.render("signup.html", user=user, pass1=pass1, pass2=pass2,
                        email=email, nameval=nameval)


class LogIn(Handler):
    """Render a basic login page for saga.

    Take data from the login page. If all the data
    is correct, create a new login cookie, with a new salt,
    and overwrite the salt in the database.
    Rationale: even if cookie theft were to happen, it would only be
    valid until the account-owner goes through the login process again.
    """

    def get(self):
        """Render the saga login form."""
        self.render("login.html")

    def post(self):
        """Log the user in or re-display the login form with an error.

        Validate the data posted from the login form, construct and set
        the login cookie if all valid, re-display the login form with an
        error if not.
        """
        username_exists = False
        username = self.request.get("username")
        password = self.request.get("password")
        cursor = db.GqlQuery("SELECT * FROM Users")
        for each in cursor:
            if each.name == username and username_exists:
                username_exists = True
                values_hash = hashlib.sha256(username + password + each.pwsalt)
                # Check the given password against the one in the database.
                if each.password == str(values_hash.hexdigest()):
                    #Make a new salt for a new token.
                    each.salt = make_salt()
                    each.put()
                    user_id = each.key().id()
                    token = hashlib.sha256(each.name+each.salt).hexdigest()
                    cookie_value = str(user_id)+"|"+str(token)
                    self.response.headers.add_header("Set-Cookie",
                                                     "user_id=%s; Path=/"
                                                     % cookie_value)
                    self.redirect("/")

                else:
                    self.render("login.html", error="invalid login")


class BlogHome(Handler):
    """Render any blog's homepage.
    """

    def get(self, username):
        """Render any blog's homepage

        Render a user's blog homepage based on the username in the URL.
        Will also, using form data in the URL, pre-enter any relevent comment
        data into the relevent comments form for any comment editing previously
        initiated on this page.

        A user's blog homepage consists of their blog's image, any relevent
        links (depending on the accessing user's identity) and the ten most
        recent posts by that user.

        Args:
          username: this argument is derived from the URL. It represents
          any existing username. If the username does not exist,
          meaning there is no signed-up user with this name, then the
          user is redirected to a 404 page.
        """
        edit_comment_id = ""
        post_id = ""
        comment_content = ""
        user_buttons = ""
        logged_in_user = ""
        error = ""
        error_author = ""
        user_data = self.validate_cookie()
        # Check that the username exists and redirects if not:
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE "
                                      "name='%s'"%username)
        image = "bloghero_tower_wide.jpg"
        exists = False
        if blog_owner_data:
            for each in blog_owner_data:
                exists = True
                if username == each.name and each.blog_image:
                    image = each.blog_image

        blog_posts = db.GqlQuery("SELECT * FROM BlogEntries WHERE author='%s' "
                                 "ORDER BY created DESC LIMIT 10"%username)

        # Check for user permission errors indicated in the URL.
        error = self.request.get("error")
        if error:
            if error == "other":
                error_author = self.request.get("author")
        if user_data:
            # Check for comment data to be edited.
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
                            self.redirect("/" + username
                                          + "?error=other&author="
                                          + each.author)
            user_buttons = "user"
            logged_in_user = user_data.name
            if user_data.name == username:
                user_buttons = "owner"

        blog_name = username+"'s blog"
        website_type = "home"
        comments = db.GqlQuery("SELECT * FROM Comments WHERE blog_loc='%s' "
                               "ORDER BY created" % username)
        if not exists:
            self.redirect("/oops")
        self.render("bloghome.html", user_buttons=user_buttons, image=image,
                    blog_name=blog_name, comments=comments, username=username,
                    logged_in_user=logged_in_user,
                    edit_comment_id=edit_comment_id,
                    post_id=post_id, comment_content=comment_content,
                    website_type=website_type, blog_posts=blog_posts,
                    error=error, error_author=error_author)

    def post(self, username):
        """Enter or update any comment made on this page.

        Comments are implemented so that they're handled on the same
        page that they're made.

        Args:
          As is the same with the get method function in this handler,
          the post method function takes the blog owner's username as
          an argument. This is added as the "blog_loc", the blog on
          which the comment is located.
        """
        user_data = self.validate_cookie()
        content = self.request.get("content")
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
                    self.redirect("/" + username
                                  + "?error=other&author="
                                  + each.author)
        else:
            author = user_data.name
            post_identity = self.request.get("post_id")
            new_entity = Comments(content=content, author=author,
                                  post_identity=post_identity,
                                  blog_loc=username)
            new_entity.put()
            new_entity.comment_id = str(new_entity.key().id())
            new_entity.put()
        time.sleep(1) # Gives the database a little time to update.
        self.redirect("/"+username)


class BlogPage(Handler):
    """Renders the appropriate webpage for any single blog entry, also
    stores any comment data entered on that page.
    """

    def get(self, post_id):
        """Render a page for a single blog entry.

        Set up and render a page for a single blog entry, based
        on the entry data and the author's customised blog appearance.
        Also, handle pre-entering comment data into the comments form for
        any comment editing initiated on this page.

        Args:
          post_id: this is automatically recieved from the URL. it is
          used to get the right post from the database and create the
          page. If this post_id doesn't refer to a real entry in the
          database the user is redirected to the 404 page "/oops".
        """
        edit_comment_id = ""
        comment_content = ""
        user_buttons = ""
        logged_in_user = ""
        error = ""
        error_author = ""
        blog_post = BlogEntries.get_by_id(int(post_id))
        if not blog_post:
            self.redirect("/oops")
        username = blog_post.author
        user_data = self.validate_cookie()
        blog_owner_data = db.GqlQuery("SELECT * FROM Users WHERE "
                                      "name='%s'" % username)
        blog_posts = db.GqlQuery("SELECT * FROM BlogEntries WHERE "
                                 "identity='%s'" % post_id)
        # Check for user permission errors indicated in the URL.
        error = self.request.get("error")
        if error:
            if error == "other":
                error_author = self.request.get("author")
        post_id = ""
        if user_data:
            # Check for comment data to be edited.
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
                            self.redirect("/" + username
                                          + "?error=other&author="
                                          + each.author)
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
        comments = db.GqlQuery("SELECT * FROM Comments WHERE blog_loc='%s' "
                               "ORDER BY created" %username)
        self.render("bloghome.html", blog_posts=blog_posts,
                    user_buttons=user_buttons, image=image,
                    blog_name=blog_name, comments=comments,
                    username=username, logged_in_user=logged_in_user,
                    edit_comment_id=edit_comment_id, post_id=post_id,
                    comment_content=comment_content, website_type="single",
                    error=error, error_author=error_author)

    def post(self, post_id):
        """Enters or updates the comment data from this page.

        Similarly to the BlogHome handler, any comments made on this page
        are also managed on this page, and entered into the Comments
        database.

        Args:
          the post_id is accessible to the post method as well. Its main
          purpose in this function is to ocate the comment in relation to
          the post.
        """
        blog_post = BlogEntries.get_by_id(int(post_id))
        username = blog_post.author
        user_data = self.validate_cookie()
        content = self.request.get("content")
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
            post_identity = self.request.get("post_id")
            author = user_data.name
            a = Comments(content=content, author=author,
                         post_identity=post_identity, blog_loc=blog_loc)
            a.put()
            a.comment_id = str(a.key().id())
            a.put()
        time.sleep(1) # Gives the database a little time to update.
        self.redirect("/"+post_id)


class NewPost(Handler):
    """Render and act upon a "new post" form."""

    def get(self):
        """Render a new post form with the user's custom data."""
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
        """Validate the new post data, and either enter or reject it.

        Check the new post data, and either enter it into the database,
        or re-display the form with an error.
        """
        subject = self.request.get("subject")
        content = self.request.get("content")

        user_data = self.validate_cookie()
        if subject and content:
            #Allow for new lines, although not any other kinds of HTML.
            content = "<p>"+content.replace("\n", "</p>\n<p>")+"</p>"
            author = user_data.name
            new_entity = BlogEntries(subject=subject, content=content,
                                     author=author, likes=[], likes_length=0)
            new_entity.put()
            # For easy post ID searches:
            new_entity.identity = str(new_entity.key().id())
            new_entity.put()
            post_id = new_entity.identity
            time.sleep(1)
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
        """Show a form for editing an existing post.

        Retrieve the post id from the URL, find the user data
        appropriate to the logged in user, checking that the user
        is also the author of the post. Use this and the post's data
        to create the edit page.

        Args:
          post_id: A number in the URL which refers to an existing blog
          post.
        """
        content = ""
        subject = ""
        user_data = self.validate_cookie()
        post_exists = False
        if not user_data:
            self.redirect("/login")
        else:
            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                 "WHERE identity='%s'" % post_id)
            for each in cursor:
                if each.identity == post_id:
                    post_exists = True
                    if user_data.name == each.author:
                        image = user_data.blog_image
                        # Transform back from HTML. A future fix might be to
                        # only add the tags just before putting the post on
                        # the site. That sounds a little more processing-heavy
                        # though.
                        content = each.content[3:-4].replace("</p>\n<p>", "\n")
                        subject = each.subject
                        self.render("newpage.html", subject=subject,
                                    content=content, image=image)
                    else:
                        self.redirect("/"+post_id)
        if not post_exists:
            self.redirect("/oops")
    def post(self, post_id):
        """Overwrite original post.

        Once the edit form has been posted, overwrite the content of
        the original post with the new content. Or don't, if the editor
        isn't the original author.

        Args:
          post_id: A number in the URL which refers to an existing blog
          post.
        """
        content = ""
        post_exists = False
        user_data = self.validate_cookie()
        if not user_data:
            self.redirect("/login")
        else:
            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                 "WHERE identity='%s'" % post_id)
            for each in cursor:
                if each.identity == post_id:
                    post_exists = True
                    if user_data.name != each.author:
                        self.redirect("/"+post_id+"?error=other&author="
                                      +each.author)
                    else:
                        subject = self.request.get("subject")
                        content = self.request.get("content")
                        image = user_data.blog_image
                        if content and subject:
                            content = content.replace("\n", "</p>\n<p>")
                            content = "<p>"+content+"</p>"
                            cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                                 "WHERE identity='%s'"
                                                 % post_id)
                            for each in cursor:
                                if each.identity == post_id:
                                    # Overwrite old post.
                                    each.subject = subject
                                    each.content = content
                                    each.put()
                                    time.sleep(1) # Wait for the database.
                                    self.redirect("/"+post_id)
                        else:
                            error = ("please add both a subject and "
                                     "body for your blog entry!")
                            self.render("newpage.html", subject=subject,
                                        content=content, error=error,
                                        image=image)
        if not post_exists:
            self.redirect("/oops")

class Oops(Handler):
    """This is the "404" page, which is visited each time a post, comment or
    user page proves not to exist.
    """
    def get(self):
        """Render a 404 error page"""
        #self.request.status = 404 # Does this do anything?
        self.render("oops.html")


### Utility handlers that don't render webpages.


class DeletePost(Handler):
    """This handler allows a user to delete a blog entry they wrote.
    """

    def get(self, post_id):
        """Delete a post.

        Retrieve the post id from the URL and, if the user is the
        author of the post, delete it from the BlogEntries database.

        Args:
          post_id: A number in the URL which refers to an existing blog
          post.
        """
        user_data = self.validate_cookie()
        blog_post = BlogEntries.get_by_id(int(post_id))
        if blog_post:
            if not user_data:
                self.redirect("/login")
            elif blog_post.author != user_data.name:
                self.redirect("/"+post_id+"?error=other&author="
                              +blog_post.author)
            else:
                cursor = db.GqlQuery("SELECT * FROM BlogEntries "
                                     "WHERE identity='%s'"%post_id)
                for each in cursor:
                    if each.identity == post_id:
                        each.delete()
                        time.sleep(1) # Gives the database a little time.
                        self.redirect("/"+user_data.name)
        else:
            self.redirect("/oops")

class LikePost(Handler):
    """Like a post.

    This Handler allows any user to like a post they did not write.
    This is limited to only one like per user per post.
    """

    def get(self, post_id):
        """Like a post.

        If the user making this request is not the author of the post,
        add the user's name to a list of users who have liked the post,
        which is recorded in the post's database entry. check this list
        each time anyone attempts to like a post, so they can use this
        handler to also unlike this post.  Record the current length
        of this list in the database for easy addition to the blog post
        representations on the website.

        Args:
          post_id: A number in the URL which refers to an existing blog
          post.
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
                            # Remove username from the list of people
                            # who have liked the post.
                            each.likes.remove(user_data.name)
                        else:
                            each.likes.append(user_data.name)
                        each.likes_length = len(each.likes)
                        each.put()
                        time.sleep(1) # Gives the database a little time.
                        self.redirect("/"+post_id)
            else:
                self.redirect("/"+post_id+"?error=self")
        else:
            self.redirect("/oops")


class DeleteComment(Handler):
    """This handler allows the author of a comment to delete it"""

    def post(self, comment_id):
        """Delete a comment.

        Let the author of a comment delete it from the Comments database.
        Then redirects to the previous page the user was on.

        Args:
          post_id: A number in the URL which refers to an existing comment.
        """
        user_data = self.validate_cookie()
        comment = Comments.get_by_id(int(comment_id))
        if comment:
            website_type = self.request.get("website_type")
            if website_type == "home":
                target = comment.blog_loc
            else:
                target = comment.post_identity
            if not user_data:
                self.redirect("/login")
            elif comment.author != user_data.name:
                self.redirect("/"+target+"?error=other&author="+comment.author)
            else:
                cursor = db.GqlQuery("SELECT * FROM Comments "
                                     "WHERE comment_id='%s'"%comment_id)
                for each in cursor:
                    if each.comment_id == comment_id:
                        each.delete()
                        time.sleep(1) # Gives the database a little time.
                        self.redirect("/"+target)
            


class LogOut(Handler):
    """Deletes the cookie content to log out the user."""
    def get(self):
        """Delete the cookie content to log out the user."""
        self.response.headers.add_header("Set-Cookie", "user_id=; Path=/")
        self.redirect("/signup")


app = webapp2.WSGIApplication([("/", MainPage),
                               ("/signup", SignUp),
                               ("/login", LogIn),
                               ("/logout", LogOut),
                               ("/oops", Oops),
                               ("/newpost", NewPost),
                               (r"/(\d+)", BlogPage),
                               (r"/_edit/(\d+)", EditPage),
                               (r"/_delete/(\d+)", DeletePost),
                               (r"/_like/(\d+)", LikePost),
                               (r"/_commentdelete/(\d+)", DeleteComment),
                               (r"/(.*)", BlogHome)], debug=True)
