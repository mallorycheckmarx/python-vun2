#Software Testing

#Introduction
First of, reddit was created by a group of students to be used as an online bulletin board system. At first, the company was only a startup and reddit was supposed to be an app for ordering food. After the stakeholders (Y Combinator) received the idea, they gave their input on the subject, and reddit was created. It started with only 2 students, and no one expected it to be what it was today.

After analysing all of the tests that reddit has (on their public source code), we found out they are poor documented, are scrambled throughout folders and not entirely organized. There are tests that test the validity of a comment on a folder and then, on a different folder, we found tests that check the limit of a comment. Even the tests that are indeed documented (very few) are mostly unintelligible.

##How testable is reddit?

##How to improve its testability?
It can be improved by test-driven development and design for testability.
##CUT (Component Under Test): the component being tested

#FIRST
##Controllability: How possible is to control the state of the CUT as required for testing
##Observability: How possible is to observe intermediate and final test results.
##Isolateability: How much CUT can be tested in isolation-
##Separation of concerns: How much every test is separated. i.e. are they all on the same test? are they well separated.
##Understandability: How well is CUT documented and easy to understand.
##Heterogeneity: How many techonologies are required to run all the test methods and tools.


#Software Testing

##Unit Testing
Unit testing is one of the most common types of testing, as it tests the source code (the scope of the software). It tests an entire unit, that is usually conceived as the smallest testable part of the software. These tests are usually created by the developers and are short fragments. Besides that, the tests should also be independent between one another.

This type of testing tends to find "bugs" and problems early in the development stage but also has its flaws, as it doesn't catch system-level errors and doesn't take into account issues with performance.

#####Config
After analysing the Config folder that reddit has, we've found that these tests are not well documented and are not easy to understand. However, they test a lot of features, such as if the user has gold, if it's logged in, if it's an admin, an employee, if a certain subreddit already exists. All of these are created using Mock Objects and Classes (fake objects that simulate the behaviour of of a real object).

#####Lib
This folder is, by far, the one with most extensive tests. Most of it is uncompreensible, as shown by "Test Cookies Upgrade" (what's a cookie?). It also tests if the user has inputed the correct password,  if it has a valid user e-mail and, again, the name of a subreddit when creating it. Image resize, the XML they use to store the user data, the parse of URL's, the padding and encryption on strings, CSS on different browsers, are all tested here.

#####Models
Different from the Config folder, even though these tests are commented, they don't use the best language for the case, as some of the comments are only understandable by the ones who created it, i.e. "This class exists to allow us to call the _qa() method on Comments without having to dick around with everything else they support". These tests work mainly on the comments from threads, creating threads and the user permissions on subreddits.

##Functional Testing
Functional testing is a type of Black Box Testing () whose tests are based on the specifications of the software CUT. They accept different inputs and then the output is examined, leaving the structure of the program out of the equation. This type of test only shows what the software is doing.

Even though reddit contains a folder with the functional tests, there's only a file init.py, with 20 lines and it's mostly a license.

##Integration Testing

##Component Interface Testing

##System Testing

##Acceptance Testing

##Compatibility Testing

##Regression Testing

##Software Performance Testing

##Accessibility Testing

##Security Testing

##Black Box Testing

##White Box Testing


#Validation & Verification


#Coverage of tests (EclEmma, others)


#Bug

##Bug Report

##Test Cases

##Automated software fault diagnosis