"""Blog branding and personalization."""
# pylint: disable=line-too-long,invalid-name

blog_url: str = 'blog.matthewrease.net'
blog_title: str = 'Compressed Thoughts'
blog_author: str = 'Matthew Rease'
blog_description: str = 'Welcome to the thoughts of 1/7,762,000,000 of the world.'
blog_icon: dict[str, int | str] = { 'width': 548, 'height': 548, 'alt': 'Silhouette of a human head between a vise clamp.' }
blog_keywords: list[str] = [  # this list should NOT be empty
        'matthew', 'rease', 'blog', 'compressed', 'thoughts', 'old', 'forge', 'inn', 'oldforgeinn', 'post', 'technology', 'personal', 'life', 'blogging']

profile_image_url: str = 'https://cdn.matthewrease.net/images/me_young.jp2'
profile_image_alt: str = 'My Mom holding my arm, while I (a child) am trying to pet a bear cub at the zoo.'
profile_text: str = "Bedroom programmer, all-day nerd. I've been programming since I was in middle school, and I've always liked to entertain people, so I hope that will come across in my posts. If you want to learn more about me, see <a href=\"https://matthewrease.net/about/\"><strong>my profile</strong></a>."

post_license: str = 'CC BY-NC-SA 4.0'
post_license_url: str = 'https://creativecommons.org/licenses/by-nc-sa/4.0/'

# leave rss_description blank to use blog_description, and rss_license blank to use post_license
rss_description: str = 'Personal blog of Matthew Rease. Elsewhere called "the thoughts of 1/7,762,000,000 of the world."'
rss_license: str = 'the Creative Commons Attribution NonCommercial ShareAlike 4.0 International'

# Optional external link - leave URL empty to disable
external_url: str = 'https://matthewrease.net/'
external_text: str = 'Return to the Inn'

# CSP Additions
csp_img_src = 'cdn.matthewrease.net'
