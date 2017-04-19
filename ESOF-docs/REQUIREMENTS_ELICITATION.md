#Requirements Elicitation

##Index

1. [Introduction](#introduction)
	* Purpose
	* Scope
	* Definitions, acronyms, and abbreviations
	* References
	* Overview
2. [Overall description](#overall-description)
	* Product perspective
	* Product functions
	* User Characteristics
	* Constraints
	* Assumptions and dependencies
		* Servers
		* Libraries
		* Misc. Utilities
3. [Requirements Specification](#requirements-specification)
	* External interface requirements
		* User interfaces
		* Hardware interfaces
		* Software interfaces)
		* Communications interfaces
4. [System features](#system-features)
	* User Case Models
5. [Performance requirements](#performance-requirements)
	* Design constraints
	* Software systems attributes
	* Other requirements


## Introduction
###Purpose

The purpose of this document is to present a detailed description of Reddit.
It will illustrate the purpose and features of the system, what it will do and it's constraints.
This document is intended for both the developers and stakeholders of Reddit.

###Scope
Reddit is the engine that powers https://reddit.com, a community-focused online bulletin board system where registered users can post content, such as text, videos, photos or links.
Users can then vote submissions up or down influencing it's rank in the overall standings. 
Reddit's aim is to harbor an open nature and diverse user community where the community generates it's content.

Reddit's content is divided into subreddits, smaller portions of reddit whose purpose is to organize the different content entries according to it's category or area of interest, such as news, movies, music, gaming, food and many others.

###Definitions, acronyms, and abbreviations

###References
*IEEE. IEEE Std 830-1998 IEEE Recommended Practice for Software Requirements Specifications. IEEE Computer Society, 1998.*

*Duggan, Maeve and Aaron Smith (2013, July 23). 6% of Online Adults are reddit Users. Retrieved from http://pewinternet.org/ .*

*https://blog.shareaholic.com/reddit-wtf/ .*

###Overview
The next chapter, the Overall Description section, of this document gives an overview of the functionality of the product. It describes the informal requirements and is used to establish a context for the technical requirements specification in the next chapter.
The third chapter, Requirements Specification section, of this document is written primarily for the developers and describes in technical terms the details of the functionality of the product. 


## Overall Description
This section will give an overview of the whole system. The system will be explained in its context to
show how the system interacts with other systems and introduce the basic functionality of it. It will also
describe what type of stakeholders that will use the system and what functionality is available for each
type. At last, the constraints and assumptions for the system will be presented.

###Product perspective
Reddit stands out from other online bulletin board systems due to its open culture and focus in providing User-generated content.
It consists of a web portal used to view/post submissions, upvote or downvote them, comment on them, and access subreddits and user account management.
![Block Diagram](https://i.imgur.com/uwO6Ula.png)

###Product functions
Reddit has a lot of functions for a website, such as sending messages and archiving all of the threads that people have created. However, its main function is bringing popular content to everyone as quickly as possible and it gives the possibility for all of the users to share their opinions on whatever matter is being discussed.

###User Characteristics
Reddit community is consists usually of young male users, with no specific range of educational level. According to [PewResearchCenter](http://pewinternet.org) As of May 2013, 15% of the internet users between the age of 18-29 say they use reddit.
![Reddit Demographics May,2013](http://www.pewinternet.org/files/old-media/177A4307EC6E400F91716BD228C4B747.jpg)

###Constraints
###Assumptions and dependencies
[reddit has a PPA on launchpad.net](https://launchpad.net/~reddit/+archive/ppa) where packages can be found for Ubuntu 12.04 Precise Pangolin. If a dependency below cannot be satisfied by the Ubuntu 12.04 archives, it will be marked `reddit ppa` and can be fetched from there. Alternative package managers may provide these packages in the right version natively.

#### Servers

In a simple environment, these can all be run on one machine. For a larger site, they will almost certainly need to be split out to different hosts.

Dependency   | Version | Ubuntu Package(s)                      | Description
-------------|---------|----------------------------------------|----------------------------------------------------------
PostgreSQL   | 9.0+    | `postgresql`                           | Robust RDBMS. Used as primary data store.
Cassandra    | 1.0+    | `cassandra` in (reddit ppa)            | Distributed database. Slowly becoming primary data store. 
memcached    | 1.4+    | `memcached`                            | Fast in-memory caching server. Used throughout reddit.
RabbitMQ     | 2.0+    | `rabbitmq-server`                      | AMQP server. Used for offline processing.
HAProxy      |         | `haproxy`                              | Load balancer for distributing requests to app servers.
stunnel      | patched | `stunnel` (reddit ppa)                 | For HTTPS support. Needs to be a version with the X-Forwarded-For patches on top.

#### Libraries

The following libraries are prerequisites before an install can begin. With these requirements satisfied, `setup.py` should be able to take care of the remaining python dependencies.

Dependency   | Version | Ubuntu Package(s)                      | Description
-------------|---------|----------------------------------------|----------------------------------------------------------
Setuptools   | 0.6.16+ | `python-setuptools`                    | Python package management.
Python       | 2.7.x   | `python-dev`                           | Headers for building python modules.
libmemcached | 0.32+   | `libmemcached-dev`                     | For communication with memcached.
libpq        |         | `libpq-dev`                            | C library for PostgreSQL.
libxml2      |         | `libxml2-dev`                          | XML Parsing Library (for python's `lxml`)
libxslt1     |         | `libxslt1-dev`                         | XSLT library (for python's `lxml`)
PIL          |         | `python-imaging`                       | This is not strictly necessary as `setup.py` will install it. However, a PyPI-installed copy of PIL will not work out of the box on a Debian/Ubuntu install because it will have trouble finding the C libraries for JPEG / PNG etc.

#### Misc. Utilities

Dependency   | Version | Ubuntu Package(s)                      | Description
-------------|---------|----------------------------------------|----------------------------------------------------------
Git          |         | `git-core`                             | reddit code is stored in Git.
GCC          |         | `gcc`                                  | Used for compiling python modules etc.
optipng      |         | `optipng`                              | Used to compress auto-generated CSS spritemap and thumbnails.
jpegoptim    |         | `jpegoptim`                            | Used to compress thumbnails.
psql         |         | `postgresql-client`                    | CLI client for managing PostgreSQL. Used by some processing jobs.
make         |         | `make`                                 | Build tool.
gettext      |         | `gettext`                              | Tools for internationalization.
node.js      | 0.6.19+ | `nodejs` (reddit ppa)                  | Javascript environment.
less.js      | 1.4+    | `node-less` (reddit ppa)               | CSS Precompiler.
uglify.js    | 1.3+    | `node-uglify` (reddit ppa)             | Javascript compression


## Requirements specification
All of the requirements come from the users of reddit that propose them and sometimes are also implemented by them.
###External interface requirements
####User interfaces
The user is allowed to post a new thread, comment, upvote or downvote any thread and their comments.
The user can also set a flair for each subreddit he has subscribed, tag his own posts with reddit own-flairs (usually Spoilers or NSFW).
The user can also create his own subreddit, search for terms in all of the threads existing in a subreddit and send private messages to other users.
####Hardware interfaces
Reddit doesn't have an hardware interface.
####Software interfaces
Reddit's interface is organized in 3 different sections, top bar, right sidebar and the body of the site.
The top bar shows the user all of the subreddit he has subscribed, a few default subreddits, the friends of the user, the subreddit banner and all of the different pages that can be acessed on the subreddit: the top, new, rising, controversial, hot and gilded pages.
The right sideba contains the description and rules of the subreddit, the information on the number of people browsing at the moment and that the subscribers, the moderators and, sometimes, a calendar with events that are coming up.
The body is located on the center of the page and is the most important one. It has all of the threads, the number of upvotes/downvotes on each one and the user that created it.
####Communications interfaces
The communication interface can be done in a number of ways. First of, users can send each other private messages and communicate that way. However, as the whole idea of reddit is to bring the news as quickly as possible, users can communicate inside threads, replying to comments from each other.
# System features
#User Case Models
##Subreddits
![User (subreddits)](http://i.imgur.com/vOugXTu.png?1)
###Create a subreddit
Access the sidebar and click the button "Create your own subreddit".

Fill all the text area available (name, title, description, sidebar, submission text)-

Change the language, type of subreddit, the content options and the wiki option.

Set the filter for the posts, links and comments.
###Search for a term
Access the sidebar and enter the term you're searching in the text box.

Sort the results by time, relevance, newest, hottest or on top.

It is also possible to do an advance search, adding the author of the post or the subreddit.
###Modding a subreddit
It is only possible to mod a subreddit if you're invited to one or if you own a subreddit.
As a mod, you can:

Change the subreddit settings.

Edit the stylesheet (html).

Edit approved submitters.

Access the traffic stats.

Access the reports.

Access the spam.

Change banned and muted users.

Edit flairs.
##Threads
![User (threads)](http://i.imgur.com/xaRjfI1.png?1)
###Post a thread
Access the sidebar and press "Submit a new link".

Create a link thread or a text thread.

Change the title.

Change the url it redirects to.

Choose the subreddit where you want to post the thread.
###Comment a thread
Access a thread.

Fill the text box below the post.

Press "save".
###Upvote/downvote a thread
Choose a thread.

Click on the arrow pointing up to upvote or click on the arrow pointing down to downvote.
###Reply to a comment on a thread
Access a thread.

Choose the comment you want to reply to.

Press the "reply".

Fill the text box that just appeared.

Press "save".
##Flairs
![User (flair)](http://i.imgur.com/vhrEgUo.png?1)
###Set a user flair
Access the sidebar and press the "edit flair" next to your username.

Choose the flair.

Press the checkbox that says "Show my flair on this subreddit. It looks like:".
###Set a thread flair
Create a thread.

Submit the thread.

Below the title of your thread press "flair".

Change to one that is available.
##Communication
![User (communication)](http://i.imgur.com/w8ho3XX.png?1)
###Send private messages
Access www.reddit.com/user/username in which username is the user you want to send a message to.
##User preferences
![User (preferences)](http://i.imgur.com/Y95p4xM.png?1)
###Change options
In the right side of the screen press "Preferences" next to your username.

Change the link, comment, messaging, display, content, privacy and beta options.
###Manage applications
In the right side of the screen press "Preferences" next to your username.

Press "apps" in the tabs menu.

Manage your authorized applications (either revoke their access or don't).
###Access RSS feeds
In the right side of the screen press "Preferences" next to your username.

Press "RSS feeds" in the tabs menu.

Access the private and moderator listings, private profile pages, user inbox and moderator inbox.
###Add friends
In the right side of the screen press "Preferences" next to your username.

Press "friends" in the tabs menu.

Fill the text box with the username of whom you want to add as a friend.
###Block users from messaging
Receive a message from the user you want to block.

In the right side of the screen, press the envelope next to your username.

Press "messages" in the tabs menu.

Search for a message from the user you want to block.

Press "block user" below the message.

Press "yes".
###Unblock users from messaging
In the right side of the screen press "Preferences" next to your username.

Press "blocked" in the tabs menu.

Search for the user you want to remove from your blocked list, and press "remove" next to their username.

Press "yes."
###Change e-mail
In the right side of the screen press "Preferences" next to your username.

Press "password/email" in the tabs menu.

Input your password.

Change your e-mail.

Press "save".
###Change password
In the right side of the screen press "Preferences" next to your username.

Press "password/email" in the tabs menu.

Input your password.

Input your password twice.

Press "save".
###Deleting the account
In the right side of the screen press "Preferences" next to your username.

Press "delete" in the tabs menu.

Input your account credentials.

Optionally, fill the text area explaining why you're deleting the account.

Press the checkbox saying "I understand that deleted accounts are not recoverable".

Press "delete account".
## Performance requirements
Reddit's performance requirements keep increasing year by year. On 2013 it had 56 billion pageviews and 731 million unique pageviews. However, the servers just aren't enough. During heavy traffic times, the site usually goes down and needs maintenance. 
###Design constraints
Reddit's design constraints are not public code, do to security purposes. So, we can't be precise on the design constraints.
###Software systems attributes
####Accessibility
Reddit can be accessed through any computer and any browser given that it has internet connection.
####Compatibility
Reddit has immense adaptability, as it runs smoothly on every web browser.
####Affordability
Reddit has 0 costs for the user, being sustained by advertisement and reddit gold, which is coin bought by users to offer each other. This gold gives a few perks to who owns it.
####Customizability
Reddit is extremely customizable, as the owner of a subreddit is allowed to change his stylesheet and create something completely different from other subreddits. However, they all have the same layout.
####Durability
Reddit archives all of the threads for several years. Users can access threads up to 4 years old.
####Maintainability
Reddit's servers run on Apache Cassandra and are maintained by the company.
####Reliability
Reddis is extremely reliable when it comes to its main function. However, the servers tend to lag on rush hours.
####Stability
As mentioned before, reddit tends to lag and sometimes even crash during rush hours.

##Authors
* Duarte Pinto - up201304777@fe.up.pt
* João Baião - up201305195@fe.up.pt
* Miguel Botelho - up201304828@fe.up.pt