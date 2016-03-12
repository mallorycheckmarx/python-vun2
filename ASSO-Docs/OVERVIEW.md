# Reddit - A Brief Overview

Reddit is a social news and link aggregrator website where users or *Redditors*, post links from the Internet and original content. It was launched in 23 of June in the year of 2005. As of begining of 2016, it has a few billion of monthly page views.
It is built mainly in Python, with a PostgreSQL database, and several side technologies added over time as the website needed to scale.

Main technological components (by subjective order of importance)
* Python (with too many libraries to name, although a noteworthy one would be pylons [web framework])
(of course Python itself brings a ton of [hopefully seperate] components)
* PostgreSQL (primary backend database. It is used for storing data on Accounts, Subreddits, Links, Comments, Votes, etc.)
* HAProxy (essentially a HTTP load balancer)
* Cassandra (for some fancy caching)
* Memcached (for caching [duh], and ad-hoc locking/synchronization between architectural components. Almost everything on reddit depends on memcached running properly)
* RabbitMQ (fancy implementation of AMQP, used to store jobs for offline processing)

Reddit is primarily deployed on AWS, along with S3 storage for static objects.