#!/usr/bin/python3
"""Compressed Thoughts blog, by Matthew Rease."""

import threading
from collections import Counter
from datetime import datetime, timedelta
from os import environ

import markdown
import MySQLdb
from dotenv import load_dotenv
from flask import Flask, render_template, Response
from PIL import Image

from md_ext import HeadingShiftExtension, HeadingLinkExtension

load_dotenv()

TWO_HOUR_DELTA = timedelta(hours = 2)

class DBContextManager:
    """Simple way to track database connection and variables."""

    def __init__(self):
        """Create persistent Blog MySQL database connection and establish cache."""
        self.credentials = {
            'host': environ.get('MYSQL_HOST', 'localhost'),
            'user': environ.get('MYSQL_USER', 'blog'),
            'password': environ.get('MYSQL_PASSWORD', 'blog'),
            'database': environ.get('MYSQL_DATABASE', 'blog') }

        self.db = None
        self.cursor = None
        self.lock = threading.Lock()
        self.connect()


        _2ha = datetime.now() - TWO_HOUR_DELTA
        self.cache = {
            'all_posts': {},
            'all_posts_req': _2ha,

            'top_tags': [],
            'top_tags_req': _2ha,

            'users': {},

            'post_count': 0,
            'post_count_req': _2ha
        }

    def __del__(self):
        """Close database connections."""
        self.cursor.close()
        self.db.close()

    def connect(self):
        """Connect to database using environment variables."""
        self.db = MySQLdb.connect(
            host=self.credentials['host'],
            user=self.credentials['user'],
            password=self.credentials['password'],
            database=self.credentials['database'])
        self.cursor = self.db.cursor()
        self.cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')

    def execute(self, query: str, tokens: tuple) -> tuple:
        """Dumb wrapper for MySQLdb.cursor.execute."""
        try:
            with self.lock:
                redlog(f'executing query {query}')
                self.cursor.execute(query, tokens)
                return self.cursor.fetchall()
        except MySQLdb.OperationalError as _e:
            if _e.args[0] == 2006:
                redlog('Lost database connection, attempting reconnect.')
                self.connect()
                return self.execute(query, tokens)
            raise

    def get_all_posts_sidebar(self):
        """Get short-form dict of every post (with cache)."""
        now = datetime.now()
        if now - self.cache['all_posts_req'] > TWO_HOUR_DELTA:
            self.cache['all_posts_req'] = now
            self.cache['all_posts'] = {
                row[2]: {
                    'title': row[0],
                    'description': row[1],
                    'alt': row[3],
                    'published': row[4],
                    'modified': row[5]
                }
                for row in self.execute(
                    'SELECT title, description, filename, image, published, modified FROM Post ORDER BY filename DESC',  # pylint: disable=line-too-long
                    tuple())}
        return self.cache['all_posts']

    def generate_archive_dict(self):
        """Split flat dictionary of posts into one sorted by year and then month."""
        posts = self.get_all_posts_sidebar()
        res = {}
        for year in range(datetime.now().year, 2019, -1):
            year = str(year)
            y_posts = {}
            for month in range(1, 13):
                month = str(month).zfill(2)
                m_posts = {
                    _id[6:]: post
                    for _id, post in posts.items()
                    if _id[0:4] == year and _id[4:6] == month }
                if m_posts:
                    y_posts[month] = m_posts
            if y_posts:
                res[year] = y_posts
        return res

    def get_top_tags(self):
        """Get most common post tags (with cache)."""
        now = datetime.now()
        if now - self.cache['top_tags_req'] > TWO_HOUR_DELTA:
            self.cache['top_tags_req'] = now
            self.cache['top_tags'] = [row[0] for row in context.execute("""
                SELECT Tag.name, COUNT(DISTINCT PostTag.post_id) AS post_count
                FROM PostTag
                JOIN Tag on PostTag.tag_id = Tag.tag_id
                GROUP BY Tag.name
                ORDER BY post_count DESC
                LIMIT 15""",
                tuple())]
        return self.cache['top_tags']

    def get_user(self, user_id):
        """Retrieve the name of the user with given ID."""
        if user_id not in self.cache['users']:
            self.cache['users'][user_id] = self.execute(
                'SELECT name FROM User WHERE user_id = %s;',
                (user_id,))[0][0]
        return self.cache['users'][user_id]

    def get_post_count(self):
        """Get total number of blog posts."""
        now = datetime.now()
        if now - self.cache['post_count_req'] > TWO_HOUR_DELTA:
            self.cache['post_count_req'] = now
            self.cache['post_count'] = self.execute('SELECT COUNT(*) FROM Post;', tuple())[0][0]
        return self.cache['post_count']

# For Flask
app = Flask(__name__)
context = DBContextManager()

def redlog(msg):
    """Print red text to log (easily distinguished from Flask logging)."""
    print(f'\x1b[31m{msg}\x1b[0m')

use_csp = environ.get('USE_CSP').lower() == 'true'
http500_db_metadata = {
    'csp': use_csp,
    'base': '',
    'canonical': ''
}
http404_post_metadata = {
    'csp' : use_csp,
    'base': '',
    'canonical': 'post/',
    #'popular': [
    #    {
    #        'id': id,
    #        'image': f'/static/{id}.webp',
    #        'image_alt': all_posts[id]['alt'],
    #        'title': all_posts[id]['title'],
    #        'description': all_posts[id]['description']
    #    }
    #    for id in popular_posts],
    #'tags': [row[0] for row in tags_sql],
    'filter': '',
    #'archive': context.generate_archive_dict(),
    #'month_names': {
    #    '01': 'January',
    #    '02': 'February',
    #    '03': 'March',
    #    '04': 'April',
    #    '05': 'May',
    #    '06': 'June',
    #    '07': 'July',
    #    '08': 'August',
    #    '09': 'September',
    #    '10': 'October',
    #    '11': 'November',
    #    '12': 'December'
    #},
    'title': 'Uh Oh!',
    'description': 'Did you mistype the link?',
    'author': 'Matthew Rease',
    'image': {
        'url': '/static/badID.webp',
        'width': 1280,
        'height': 800,
        'alt': 'macintosh computer with frown and X for eyes'
    },
    'preview': 'Unfortunately the post ID you have provided in the URL could not be found. Please check the URL and try again.',  # pylint: disable=line-too-long
    'published': {
        'date': '20200202',
        'time': '00:00:00'
    },
    'modified': {
        'date': '20200202',
        'time': '00:00:00'
    },
    'content': markdown.markdown('If you think this is an error, then feel free to contact me about it.')  # pylint: disable=line-too-long
}
popular_posts = {
    'last_check': datetime.now() - TWO_HOUR_DELTA,
    'data': []
}

def get_top_tags(tag_filter: str) -> list[str]:
    """Generate list of the most used tags, including the current filter and an empty tag."""
    top_tags = list(context.get_top_tags())
    if tag_filter in top_tags:
        top_tags.remove(tag_filter)
    if tag_filter != '':
        top_tags.insert(0, tag_filter)
    top_tags.insert(0, '')
    return top_tags

def get_popular_posts() -> list[str]:
    """Generate list of popular posts from log, and cache."""
    now = datetime.now()
    if now - popular_posts['last_check'] > TWO_HOUR_DELTA:
        popular_posts['last_check'] = now
        try:
            with open('uwsgi.log', 'r', encoding='utf-8') as log:
                new_data = Counter()
                for line in log.read().splitlines():
                    if '] GET /post/' in line:
                        new_data[line.split('] GET /post/')[1].split()[0]] += 1
                popular_posts['data'] = [key for key, _ in new_data.most_common(3)]
        except FileNotFoundError as _e:
            print(_e)
            redlog("Please create a log file, even if you won't use it, to minimize work on the server!")  # pylint: disable=line-too-long
        #print(new_data)
    #print(popular_posts)
    return popular_posts['data'] or [] # [ '202002101957', '202002261145', '202004161413' ]

# Handle Pages
@app.route('/')
@app.route('/filter/<tag_filter>')
@app.route('/page/<int:page>')
@app.route('/filter/<tag_filter>/page/<int:page>')
def index(tag_filter='', page=0):
    """Generate main page, showing most recent posts (paginated)."""
    try:
        # Prereqs for Jinja metadata.
        all_posts = context.get_all_posts_sidebar()
        top_tags = get_top_tags(tag_filter)
        last_page = (context.get_post_count() - 1) // 5 if tag_filter == '' else (context.execute(
            """
            SELECT COUNT(DISTINCT PostTag.post_id)
            FROM PostTag
            JOIN Tag ON Tag.tag_id = PostTag.tag_id
            WHERE LOWER(Tag.name) LIKE %s;""",
            (f'%{tag_filter.lower()}%',))[0][0] - 1) // 5
        main_posts = [
            {
                'id': row[6],
                'image': f'/static/{row[6]}.webp',
                'image_alt': row[7],
                'title': row[1],
                'description': row[2],
                'preview': row[3],
                'author': row[0],
                'published': row[4].astimezone().replace(microsecond=0).isoformat(),
                'modified': row[5].astimezone().replace(microsecond=0).isoformat(),
                'datestr': row[4].strftime('%b %d, %Y')
            }
            for row in context.execute(
                f"""
                SELECT User.name, Post.title, Post.description, Post.preview, Post.published, Post.modified, Post.filename, Post.image
                FROM Post
                JOIN User ON Post.user_id = User.user_id {'''
                WHERE Post.post_id IN (
                    SELECT PostTag.post_id
                    FROM PostTag
                    JOIN Tag ON Tag.tag_id = PostTag.tag_id
                    WHERE LOWER(Tag.name) LIKE %s)''' if tag_filter != '' else ''}
                ORDER BY filename DESC
                LIMIT 5
                OFFSET %s;""",
                (f'%{tag_filter.lower()}%', page * 5) if tag_filter != '' else (page * 5,))]

        # All relevant data for Jinja template.
        metadata = {
            'csp': use_csp,
            'base': '',
            'canonical': '',
            'popular': [
                {
                    'id': id,
                    'image': f'/static/{id}.webp',
                    'image_alt': all_posts[id]['alt'],
                    'title': all_posts[id]['title'],
                    'description': all_posts[id]['description']
                }
                for id in get_popular_posts()],
            'tags': top_tags,
            'filter': tag_filter,
            'archive': context.generate_archive_dict(),
            'month_names': {
                '01': 'January',
                '02': 'February',
                '03': 'March',
                '04': 'April',
                '05': 'May',
                '06': 'June',
                '07': 'July',
                '08': 'August',
                '09': 'September',
                '10': 'October',
                '11': 'November',
                '12': 'December'
            },
            'page': page,
            'last': last_page,
            'posts': main_posts,
            'pages': list(range(max(0, page - 3), min(last_page + 1, page + 4)))
        }
        return render_template('index.html', metadata=metadata)

    except MySQLdb.OperationalError as _e:
        if _e.args[0] == 2002:
            redlog('Could not connect to database!')
            return render_template('500_db.html', metadata=http500_db_metadata), 500
        raise

@app.route('/post/<int:post_id>')
def show_post(post_id):
    """Show a post from the database."""
    try:
        # Prereqs for Jinja metadata.
        res = context.execute(
            # pylint: disable=line-too-long
            """
            SELECT post_id, user_id, title, description, preview, content, published, modified, filename, image
            FROM Post
            WHERE filename = %s;""",
            (post_id,))
        if not res:  # Post does not exist
            return render_template('404_post.html', metadata=http404_post_metadata), 404
        res = res[0]
        all_posts = context.get_all_posts_sidebar()
        # Alternate idea to get both tags_sql and the post in one query:
        #
        # SELECT Post.post_id, Post.title, ..., Tag.name
        # FROM Post
        # LEFT JOIN PostTag ON Post.post_id = PostTag.post_id
        # LEFT JOIN Tag ON PostTag.tag_id = Tag.tag_id
        # WHERE Post.filename = %s;
        #
        # Which creates something like the table below.
        #
        # +---------+------------------------------------+--------------+
        # | post_id | title                              | name         |
        # +---------+------------------------------------+--------------+
        # |      19 | Confidentiality in the Digital Age | learning     |
        # |      19 | Confidentiality in the Digital Age | cryptography |
        # |      19 | Confidentiality in the Digital Age | privacy      |
        # +---------+------------------------------------+--------------+
        tags_sql = context.execute(f"""
            SELECT Tag.name
            FROM PostTag
            JOIN Tag ON PostTag.tag_id = Tag.tag_id
            WHERE PostTag.post_id = {res[0]};""",  # Not explicitly optimized
            tuple())                               # Should do the WHERE first...
        author = context.get_user(res[1])
        image = Image.open(f'static/{res[8]}.webp')
        md_body = markdown.markdown(
            res[5],
            extensions=["fenced_code", HeadingShiftExtension(), HeadingLinkExtension()])

        # All relevant data for Jinja template.
        metadata = {
            'csp': use_csp,
            'base': f'post/{res[8]}',
            'canonical': f'post/{res[8]}',
            'popular': [
                {
                    'id': id,
                    'image': f'/static/{id}.webp',
                    'image_alt': all_posts[id]['alt'],
                    'title': all_posts[id]['title'],
                    'description': all_posts[id]['description']
                }
                for id in get_popular_posts()],
            'tags': [row[0] for row in tags_sql],
            'filter': '',
            'archive': context.generate_archive_dict(),
            'month_names': {
                '01': 'January',
                '02': 'February',
                '03': 'March',
                '04': 'April',
                '05': 'May',
                '06': 'June',
                '07': 'July',
                '08': 'August',
                '09': 'September',
                '10': 'October',
                '11': 'November',
                '12': 'December'
            },
            'title': res[2],
            'description': res[3],
            'author': author,
            'image': {
                'url': f'/static/{res[8]}.webp',
                'width': image.size[0],
                'height': image.size[1],
                'alt': res[9]
            },
            'preview': res[4],
            'published': res[6].astimezone().replace(microsecond=0).isoformat(),
            'modified': res[7].astimezone().replace(microsecond=0).isoformat(),
            'content': md_body
        }
        return render_template('post.html', metadata=metadata)

    except MySQLdb.OperationalError as _e:
        if _e.args[0] == 2002:
            redlog('Could not connect to database!')
            return render_template('500_db.html', metadata=http500_db_metadata), 500
        raise

@app.route('/rss')
def rss():
    """Generate RSS feed of blog posts."""
    posts = sorted(
        [
            {
                'title': post['title'],
                'id': id,
                'description': post['description'],
                'image': {
                    'url': f'/static/{id}.webp',
                    'size': 0
                },
                'published': post['published'].astimezone().replace(microsecond=0).isoformat(),
                'modified': post['modified'].astimezone().replace(microsecond=0).isoformat(),
                'raw_published': post['published'],
                'author': 'NOT SPECIFIED',
                'tags': []
            }
            for id, post in context.get_all_posts_sidebar().items()
        ],
        key=lambda x: x['id'],
        reverse=True)

    metadata = {
        'now': datetime.now().astimezone().strftime('%a, %d %h %Y %H:%M:%S %z'),
        'published': posts[0]['raw_published'].astimezone().strftime('%a, %d %h %Y %H:%M:%S %z'),
        'image': {
            'url': '/static/icon.webp'
        },
        'posts': posts
    }
    return Response(render_template('feed.rss', metadata=metadata), mimetype='application/rss+xml')

@app.route('/sitemap.xml')
def sitemap():
    """Generate RSS feed of blog posts."""
    posts = sorted(
        [
            {
                'id': id,
                'modified': post['modified'].astimezone().replace(microsecond=0).isoformat()
            }
            for id, post in context.get_all_posts_sidebar().items()
        ],
        key=lambda x: x['id'],
        reverse=True)

    return Response(render_template('sitemap.xml', posts=posts), mimetype='application/xml')

# For uWSGI
application = app
