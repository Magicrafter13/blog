#!/usr/bin/python3
"""Compressed Thoughts blog, by Matthew Rease."""

import threading
from os import environ

import markdown
import MySQLdb
from dotenv import load_dotenv
from flask import Flask, render_template

class HeadingShiftProcessor(markdown.treeprocessors.Treeprocessor):  # pylint: disable=too-few-public-methods
    """Find all <h> elements and increase their level."""

    def run(self, root):
        """Largely adapted from ChatGPT."""
        for element in root.iter():
            if element.tag.startswith('h') and element.tag[1:].isdigit():
                level = int(element.tag[1:])
                element.tag = f'h{level + 2}'

class HeadingShiftExtension(markdown.extensions.Extension):
    """Extend Markdown library with heading shifter."""

    def extendMarkdown(self, md):
        """Register extension in the Markdown engine."""
        # Priority arbitrarily chosen by ChatGPT...
        md.treeprocessors.register(HeadingShiftProcessor(md), 'shiftheadings', 15)

class DBContextManager:
    """Simple way to track database connection and variables."""

    def __init__(self):
        """Connect to database using environment variables."""
        load_dotenv()
        self.db = MySQLdb.connect(
            user=environ.get('MYSQL_USER'),
            password=environ.get('MYSQL_PASSWORD'),
            database=environ.get('MYSQL_DATABASE'))
        self.cursor = self.db.cursor()
        self.lock = threading.Lock()

    #def execute(self, *args):
    #    """Dumb wrapper for MySQLdb.cursor.execute."""
    #    with self.lock:
    #        self.cursor.execute(args)
    #        return self.cursor.fetchall()

    def execute(self, query, tokens):
        """Dumb wrapper for MySQLdb.cursor.execute."""
        with self.lock:
            self.cursor.execute(query, tokens)
            return self.cursor.fetchall()

    #def fetch(self):
    #    """Dumb wrapper for MySQLdb.cursor.fetchall."""
    #    return self.cursor.fetchall()

    def __del__(self):
        """Close database connections."""
        self.cursor.close()
        self.db.close()

# For Flask
app = Flask(__name__)
context = DBContextManager()

# Handle Pages
@app.route('/')
@app.route('/filter/<tag_filter>')
def index(tag_filter=None):
    """Generate main page, showing most recent posts (paginated)."""
    if not tag_filter:
        tag_filter = ''
    top_tags = [row[0] for row in context.execute("""
        SELECT Tag.name, COUNT(DISTINCT PostTag.post_id) AS post_count
        FROM PostTag
        JOIN Tag on PostTag.tag_id = Tag.tag_id
        GROUP BY Tag.name
        ORDER BY post_count DESC
        LIMIT 15""",
        tuple())]
    if tag_filter in top_tags:
        top_tags.remove(tag_filter)
        top_tags.insert(0, tag_filter)

    query = f"""
        SELECT User.name, Post.title, Post.description, Post.preview, Post.published, Post.modified, Post.filename, Post.image
        FROM Post
        JOIN User ON Post.user_id = User.user_id {'''
        WHERE Post.post_id IN (
            SELECT PostTag.post_id
            FROM PostTag
            JOIN Tag ON Tag.tag_id = PostTag.tag_id
            WHERE Tag.name = %s)''' if tag_filter != '' else ''}
        ORDER BY filename DESC
        LIMIT 5;"""

    posts = [
        {
            'id': row[6],
            'image': f'https://blog.matthewrease.net/posts/images/archive/{row[6][0:4]}/{row[6][4:6]}/{row[6][6:]}.webp',
            'image_alt': row[7],
            'title': row[1],
            'description': row[2],
            'preview': row[3],
            'author': row[0],
            'published': {
                'date': row[4].strftime('%Y%m%d'),
                'time': row[4].strftime('%H%M%S'),
            },
            'modified': {
                'date': row[5].strftime('%Y%m%d'),
                'time': row[5].strftime('%H%M%S'),
            },
            'datestr': row[4].strftime('%b %d, %Y')
        }
        for row in context.execute(query, (tag_filter,) if tag_filter != '' else None)]

    metadata = {
        'base': '',
        'canonical': '',
        'popular': [
            {
                'id': 202002101957,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/02/101957.webp',
                'image_alt': 'html code on a green crt display',
                'title': 'Old Code',
                'description': 'Ever look at your old code, and think: what the actual ****?'
            },
            {
                'id': 202002261145,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/02/261145.webp',
                'image_alt': 'a cluttered attic with cardboard boxes, among other things',
                'title': 'The Attic of Unfinished Projects',
                'description': "It makes me kinda sad to think about all the projects I've started that are \"on the backburner\", \"unfinished\", or otherwise in some form of purgatory."
            },
            {
                'id': 202004161413,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/04/161413.webp',
                'image_alt': "coronavirus image that definitely wasn't just the first image search result :)",
                'title': 'Coronavirus am I right?',
                'description': 'Ha, what kind of idiot would start a blog, then go over a month without posting... heh... yeah what kind?'
            }
        ],
        'tags': [''] + top_tags,
        'filter': tag_filter,
        'posts': posts
    }
    return render_template('index.html', metadata=metadata)
    #return '<html><body>Hello World</body></html>'

@app.route('/post/<int:post_id>')
def post(post_id):
    """Show a post from the database."""
    res = context.execute(
        # pylint: disable=line-too-long
        """
        SELECT post_id, user_id, title, description, preview, content, published, modified, filename, image
        FROM Post
        WHERE filename = %s;""",
        (post_id,))[0]
    md_body = markdown.markdown(res[5], extensions=["fenced_code", HeadingShiftExtension()])

    tags_sql = context.execute(f"""
        SELECT Tag.name
        FROM PostTag
        JOIN Tag ON PostTag.tag_id = Tag.tag_id
        WHERE PostTag.post_id = {res[0]};""",  # Not explicitly optimized
        tuple())                               # Should do the WHERE first...

    author = context.execute(f'SELECT name FROM User WHERE user_id = {res[1]};', tuple())[0][0]

    metadata = {
        'base': '',
        'canonical': f'post/{res[8]}',
        'popular': [
            {
                'id': 202002101957,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/02/101957.webp',
                'image_alt': 'html code on a green crt display',
                'title': 'Old Code',
                'description': 'Ever look at your old code, and think: what the actual ****?'
            },
            {
                'id': 202002261145,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/02/261145.webp',
                'image_alt': 'a cluttered attic with cardboard boxes, among other things',
                'title': 'The Attic of Unfinished Projects',
                'description': "It makes me kinda sad to think about all the projects I've started that are \"on the backburner\", \"unfinished\", or otherwise in some form of purgatory."
            },
            {
                'id': 202004161413,
                'image': 'https://blog.matthewrease.net/posts/images/archive/2020/04/161413.webp',
                'image_alt': "coronavirus image that definitely wasn't just the first image search result :)",
                'title': 'Coronavirus am I right?',
                'description': 'Ha, what kind of idiot would start a blog, then go over a month without posting... heh... yeah what kind?'
            }
        ],
        'tags': [''] + [row[0] for row in tags_sql],
        'filter': '',
        'title': res[2],
        'description': res[3],
        'author': author,
        'image': {
            'url': f'https://blog.matthewrease.net/posts/images/archive/{res[8][0:4]}/{res[8][4:6]}/{res[8][6:]}.webp',  # pylint: disable=line-too-long
            'width': 64,
            'height': 64,
            'alt': res[9]
        },
        'preview': res[4],
        'published': {
            'date': res[6].strftime('%Y%m%d'),
            'time': res[6].strftime('%H%M%S'),
        },
        'modified': {
            'date': res[7].strftime('%Y%m%d'),
            'time': res[7].strftime('%H%M%S'),
        },
        'content': md_body
    }
    return render_template('post.html', metadata=metadata)
    #return f'<html><body>{md_body}</body></html>'
    #return context.fetch()

# For uWSGI
application = app
