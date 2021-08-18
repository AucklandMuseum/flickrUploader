
from __future__ import unicode_literals
import csv
import logging
import sys
import xml.etree.ElementTree as ET

import flickrapi
from decouple import config
from progress.bar import Bar

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logfile_format = logging.Formatter(
    '%(asctime)s: %(name)s (%(funcName)s): %(message)s')
logfile = logging.FileHandler(filename='flickrDownload.log', encoding='utf8')
logfile.setFormatter(logfile_format)
logfile.setLevel(logging.DEBUG)

log.addHandler(stream_handler)
log.addHandler(logfile)

flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')

# Create flickr object from the FlickrAPI constructor. Get parsed JSON,
# and save the token in a folder relative to this script. Use caching.
# On Windows, set the location to ".\\.flickr"
flickr = flickrapi.FlickrAPI(
    api_key=flickrKey, secret=flickrSecret,
    cache=True, token_cache_location="./.flickr")


def login():
    """Login to Flickr and report some basic user info."""
    current_user = flickr.test.login()
    username = current_user.find('user')[0].text
    id = current_user.find('user').attrib['id']
    log.info("Logged in as {0} ({1})".format(username, id))

    user_info = flickr.people.getInfo(user_id=id)
    upload_count = int(user_info.find('.//count').text)
    views = user_info.find('.//views').text
    log.info("{0} photos; {1} views".format(upload_count, views))

    get_data(user_identifier=id, total_photos=upload_count)


def auth_check():
    """Check if a token exists (in .flickr), otherwise obtain one."""
    permissions = 'write'
    if not flickr.token_valid(perms=permissions):
        log.info("No valid token stored. Getting a new one.")
        flickr.get_request_token(oauth_callback='oob')

        # Print the Authorisation URL, and ask the user to open it.
        authorisation_url = flickr.auth_url(perms=permissions)
        log.info("Authorisation URL:\n{0}\n".format(authorisation_url))
        print("Open this URL in a web browser, authorise this app, and you should see a verifier code in the format nnn-nnn-nnn.")

        # Get the verifier code from the user.
        verification_code = str(input(
            "Paste the code here: "))

        # Trade the request token for an access token
        flickr.get_access_token(verification_code)
    login()


def get_data(user_identifier: str, total_photos: int):
    walker = flickr.walk_user(user_id=user_identifier,
                              extras="description, tags, machine_tags, url_o")
    with open("flickrResults.csv", mode='a', newline='', encoding='utf-8') as output:
        write = csv.writer(output)
        with Bar('Downloading metadata...', max=total_photos) as pbar:
            for count, photo in enumerate(walker):
                attr = photo.attrib
                id = attr['id']
                title = attr['title']
                tags = attr['tags']
                mach_tags = attr['machine_tags']
                url_o = attr['url_o']
                # Replaces new lines (\n) in the Description field so as to not break the csv
                xml_desc = photo.find('description').text
                description = xml_desc.replace('\n', '\\n')
                write.writerow(
                    [id, title, description, tags, mach_tags, url_o])
                log.debug("Wrote record {0}".format(id))
                pbar.next()
        print("Complete.")
        print(80 * "=")
        sys.exit()


if __name__ == "__main__":
    print("\nFlickr downloader.")

    with open("flickrResults.csv", mode='w', newline='', encoding='utf-8') as output:
        # Write headers to CSV file
        headers = ["flickr_id", "title", "desc",
                   "tags", "machine_tags", "flickr_url"]
        write = csv.writer(output)
        write.writerow(headers)
        output.close()

    print(80 * "=")
    auth_check()
