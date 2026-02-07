# Dogeared (working title)
Dogeared is a Book Club Management System.

## Users:
Users can join or create book clubs, where book suggestions are added and voted on. 

Each user profile will have private bookshelves, which contain books of, say, a particular genre or theme. To add a book to a shelf, the user would search for a specific work (facilitated by the OpenLibrary API), then add it to a shelf. 

They can also be members (or owners) of one or more book clubs. As a book club member, they would submit recommendations from their shelves, and participate in voting for their next book. 

## Book Clubs:
Each book club is a group of user members.

The main goal of a club is to help organizers manage real world (or digital) meetings:
- Solicit book recommendations from members in "shortlists"
- Initiate and manage voting periods
- Keep track of upcoming meeting times, location, and expectations (e.g., how far to read for the next meeting)
- Maintain a history of previously read and submitted books

### Authorization:
There are three permissions levels for members of a book club.
1. Member: adds books to shortlists, voting, and forums (if implemented later)
2. Moderator: admits new members, initiates shortlists, initiates voting periods, etc. (Optional level that may be best suited for larger clubs)
3. Owner - creates/delete group, update group settings, adds moderators.


## Development:
After cloning, add a '.env' file to the project root. Variables to define:
DJANGO_SECRET_KEY=''
GOOGLE_BOOKS_API_KEY=''

$ python3 manage.py migrate

Create a superuser:
$ python3 manage.py createsuperuser
-- follow prompts