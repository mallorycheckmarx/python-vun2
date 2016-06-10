Process view 

Subtitle:
U - User
H - Http server
M - Memcached
C - Cassandra Database
P - PostGres Database
Q - RabitMQ
Co- Consumer


POST

When someone wants to insert a post on Reddit the first step is to send a HTTP POST to the HTTP server. In the next step, the server not only checks Memcached to see if there is already information present using a GET through a Unix or a TCP socket but also checks on Cassandra using a SELECT instead. Finnaly the server hits the Postgres with several queries getting the result from the database in a form of a Remote Procedure call. The final step of this procedure consists on the HTTP server sending the response to the user.

COMMENT

The process of creating a comment on Reddit starts from a HTTP POST to the HTTP server by a user, that ends his interaction with Reddit right after the server insert the comment on Memcached and on Postgres, receiving an OK response but will not see the added comment in the right place of the webpage. The process of reordering the comment tree is done in "back-end". 
After sending the response to the user, the server adds the comment to the queue waiting for the consumer to handle it, sorting the comment tree and adding it to Cassandra and memcached in the last step.

UPVOTE / DOWNVOTE

When a user upvotes or downvotes a "thing" on Reddit the same mechanisms are called. For starters, an HTTP post is sent to the HTTP server. Then Memcached increments the information displayed on the page instantly and the Up/Downvote is sent to the queue to recompute the information and proceed to sorting the information on the page if needed, at this point the user receives the response from the server. 
After the Up/Downvote is on the queue it will be fetched by the consumer that will hit the Postgres database with queries in order to retrieve information and to instert the updated information into Cassandra.