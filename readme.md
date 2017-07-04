# Saga - Intro to Backend Project

Saga is a model blog, made as part of the Full Stack Nanodegree at Udacity.

Saga is deployed on Google App Engine and can be acccessed online [here](http://saga-blog.appspot.com). It is coded in Python 2.7, using the [Jinja2 templating language](http://jinja.pocoo.org/docs/2.9/). As well as the ability to make posts, it includes properly validated user accounts, individual pages for each user, and comment-making capabilities. It might even look quite nice.

## How to Run this Project

In order to deploy a copy of this project yourself, your first step is to gain access to the Google Cloud Console, accessible [here](https://console.cloud.google.com/home/dashboard). Once you have signed up, the option to create a new project should be available in the blue top bar of the Google Cloud Console.

The second step is to install Google Cloud SDK, available [here](https://cloud.google.com/sdk/). A guide to installing this and the app engine components can be found [here](https://cloud.google.com/appengine/docs/standard/python/download)

To gain access to the code, it should then be cloned from GitHub using git.

Once the code has been cloned onto your computer, you can then change it as you would like. To preview by running the project locally, open Google Cloud SDK (set up with appropriate components as previously described). Navigate to the directory containing the Saga project,`cd <your complete file pathway>` and then type the command `dev_appserver.py app.yaml`.

Visiting `http://localhost:8080/` in a web browser will then show you a copy of the project.

To shut down the local server, and thus gain access to the command line again, press ctrl+c (or cmd+c). 

To deploy the project to its own website, making sure you are in the directory containing the project, run the command
```
gcloud app deploy app.yaml index.yaml
```
as per [this set of instructions](https://cloud.google.com/appengine/docs/standard/python/getting-started/deploying-the-application)

There may be some delay in accessing a user's blog homepage, due to the indexes needing to update.

All of this is outlined in more detail in [this tutorial](https://cloud.google.com/appengine/docs/standard/python/getting-started/creating-guestbook).

## Collaboration

There are also quite a few features staged for future completion, and for which the ground-work has been laid. Any assistance with these updates would be appreciated.

### Customization
Blog hero images, blog names and blog color palettes are three key areas in which it would be relatively simple to add user customization. The hero image, though currently randomized, already has a column in the User database, and with an additional form could easily be changed to any of the other options.

Blog names are a simple string, and although there is no column in the User database as of yet, there is a template variable with a simple placeholder already in the bloghome.html template. All that is required is that the user be asked what they'd like it to be.

Color palettes are a slightly more complex matter. Very likely a css file would need to be created for each of the color palettes, and an aethetic way of displaying these options to the user would need to be designed. Nevertheless, implementing these is a simple matter of storing the name of the css file in the User entity and inputting it into a template variable in the head of the bloghome.html template.

All of this is likely to need a handler with many of the same features: user validation, forms and form entry, and entering the data into a database. It might most easily be done with a variant of the newpage.html template and the NewPost handler.

### About and Archive Pages

The navigation links in the bar directly underneath the header are currently unused. These represent 2 future features for which some interesting new handlers would have to be created. The About page would ideally contain a flattering placeholder description, until visited by the owner, who would then be redirected to a page with the newpage.html template, which would allow the user to write their own text for this page.

The archive page would contain all the headings for all the blogposts done by that user, each being a permalink to its post. This would provide an overview for the entire blog. Not an especially difficult feature to code, although finding the right design might be somewhat harder.

### Other useful actions:

- Comments are currently never visible when any page is loaded. This is not good for editing comments, particularly.

- A fair amount of code could be sensibly refactored into functions, and split into multiple modules/files.

- Icon accessibility issues: interactive icons should have aria-hidden alternatives to make sure they're visible to screen-readers

- A simple read-though to check how intuitive the code is.

## Contributions and Credit

Steven Huffman's videos in the [Udacity course CS253](https://www.udacity.com/course/web-development--cs253) provided much of the guidance in creating this project.

All photographs in this project are published by [Unsplash](https://unsplash.com/), and are free for any use. the unsplash licence can be read [here](https://unsplash.com/license)

### Photographers:
[Aaron Burden](https://unsplash.com/@aaronburden)
[Annie Spratt](https://unsplash.com/@anniespratt)
[Anthony Robin](https://unsplash.com/@anthonyrobinphoto)
[Arwan Sutanto](https://unsplash.com/@arwanod)
[Camille/Kmile](https://unsplash.com/@kmile_ch)
[Dominik Scythe](https://unsplash.com/@drscythe)
[Drew Hays](https://unsplash.com/@drew_hays)
[Jaromir Kavan](https://unsplash.com/@jerrykavan)
[Joshua Earle](https://unsplash.com/@joshuaearle)
[Keith Misner](https://unsplash.com/@keithmisner)
[Marko Blazevic](https://unsplash.com/@kerber)
[Matt Thornhill](https://unsplash.com/@matt_47)
[Michal Grosicki](https://unsplash.com/@groosheck)
[Ren Ran](https://unsplash.com/@renran)
[Richard Lock](https://unsplash.com/@richlock)
[Rodrigo Soares](https://unsplash.com/@rodi01)
[Sam Ferrara](https://unsplash.com/@samferrara)
[Scott Webb](https://unsplash.com/@scottwebb)
[Timothy Muza](https://unsplash.com/@timothymuza)


Licensing:
Saga is released under the MIT licence which can be read [here] https://opensource.org/licenses/MIT, copywrite [Steven Huffman](https://www.linkedin.com/in/shuffman56), [Udacity](https://www.udacity.com/), and [Siobhan Hokin](http://www.siobhanhokin.com/).

