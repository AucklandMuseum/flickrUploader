""" Reads JPEG files in a directory and uploads them to Flickr.
 - JPEGs are expected to have a Vernon ID before the underscore, i.e. 70152_001.jpg
 - Uses the Auckland Museum API to get record data.
 - Logs to ./flickrUpload.log
"""


import csv
import glob
import json
import logging
import sys

import flickrapi
import requests
from decouple import config

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logfile_format = logging.Formatter(
    '%(asctime)s: %(name)s (%(funcName)s): %(message)s')
logfile = logging.FileHandler(filename='flickrUpload.log', encoding='utf8')
logfile.setFormatter(logfile_format)
logfile.setLevel(logging.DEBUG)

log.addHandler(stream_handler)
log.addHandler(logfile)

flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')

# Create flickr object from the FlickrAPI constructor. Get parsed JSON,
# and save the token in a folder relative to this script. Use caching.
flickr = flickrapi.FlickrAPI(
    api_key=flickrKey, secret=flickrSecret, format='parsed-json',
    cache=True, token_cache_location=".\\.flickr")


def two_decimals(number: float):
    """Return passed number to two decimal places if not an integer,
    otherwise return number as an integer,"""
    if (number - int(number) != 0):
        return "%.2f" % number
    else:
        return "%d" % number


def get_keepers(url, http_headers):
    """Gets \"keepers\" (i.e., departments) from the AM API and returns a
    space-delimited string for Flickr's \'tags\' field. Wraps departments
    containing spaces in double quote marks."""
    
    keepers = ''
    response = requests.request("GET", url, headers=http_headers)
    if response.status_code == 200:
        jsonData = json.loads(response.text)
        values = jsonData['rdf:value']

        for count, keeper in enumerate(values, start=1):
            dept = keeper['value']
            if ' ' in dept:
                dept = "\"{0}\"".format(dept)
            keepers += dept
            if count < len(values):
                keepers += " "

    return keepers.lower()


def get_OtherTitle(url, http_headers):
    """Gets the record's Other Title from the AM API and returns it"""
    response = requests.request("GET", url, headers=http_headers)
    if response.status_code == 200:
        jsonData = json.loads(response.text)
        try:
            return jsonData['rdf:value'][0]['value']
        except KeyError:
            return '[No description]'


def get_JSON():
    """Reads filenames, extracts IDs and retrieves title, description, and
    credit line from the AM API. Adds departments as tags."""
    num_files = len(glob.glob('*.jpg'))
    if num_files > 0:
        log.info("Found {0} JPEG files".format(num_files))
        print('\n')
        jpeg_files = glob.iglob('*.jpg')

        with open("file_list.csv", 'w', newline='', encoding='utf-8') as output:
            # Write headers to CSV file list
            header = ["number", "filename"]
            write = csv.writer(output)
            write.writerow(header)

            for count, filename in enumerate(jpeg_files, start=1):
                write.writerow([count, filename])
                print(8 * "-")
                print("\n")
                percent_complete = ((count * 100) / num_files)
                log.info("File: {0} ({1} of {2}; {3}%).".format(
                    filename,
                    count,
                    num_files,
                    two_decimals(percent_complete)))
                # We only want the Vernon ID, so split off the rest of the filename
                id = filename.split('_')[0]
                url = ("http://api.aucklandmuseum.com/id/humanhistory/object/" + id)
                http_headers = {'Accept': 'application/json'}

                response = requests.request("GET", url, headers=http_headers)
                if response.status_code == 200:
                    log.info("Loaded {0}; response {1}.".format(
                        url, response.status_code))
                    jsonData = json.loads(response.text)
                    log.debug("Response JSON: {0}".format(jsonData))

                    try:
                        title = jsonData['dc:title'][0]['value'].capitalize()
                    except KeyError:
                        title = '[No title]'

                    try:
                        desc = jsonData['dc:description'][0]['value']
                    except KeyError:
                        try:
                            otherTitleURL = jsonData['am:otherTitle'][0]['value']
                            desc = get_OtherTitle(otherTitleURL, http_headers)
                        except KeyError:
                            desc = '[No description]'
                    except KeyError:
                        desc = '[No description]'

                    try:
                        credit = jsonData['am:creditLine'][0]['value']
                    except KeyError:
                        credit = '[No credit line]'

                    weburl = (
                        'https://www.aucklandmuseum.com/collection/object/am_humanhistory-object-' + id)
                    keepers_url = jsonData['ecrm:P50_has_current_keeper'][0]['value']
                    tags = ""
                    tags = get_keepers(keepers_url, http_headers)

                    flickrDesc = ("Title: {0}\nDescription: {1}\nCredit: {2}\n{3}".format(
                        title, desc, credit, weburl))

                    upload_photo(filename, title, flickrDesc, tags)

                else:
                    log.info("Response code {0} on {1}".format(
                        response.status_code, id))
                    pass
        output.close()
        print(8 * "-")
        log.info("\nFinished!")
        sys.exit()
    else:
        log.info("No JPEGs in current directory. Exiting.")
        sys.exit()


def login():
    """Login to Flickr and report some basic user info."""
    current_user = flickr.test.login()
    username = current_user['user']['username']['_content']
    id = current_user['user']['id']
    log.info("Logged in as " + (username) + " (" + id + ")")
    
    user_info = flickr.people.getInfo(user_id=id)
    upload_count = user_info['person']['upload_count']
    views = user_info['person']['photos']['views']['_content']
    log.info("{0} photos; {1} views".format(upload_count, views))
    
    get_JSON()


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


def upload_photo(file, title, desc, tags):
    """Upload the JPEG to Flickr, with title, description, and tags."""
    log.info("Title: \"{0}\"".format(title))
    log.info("Description: \"{0}\"".format(desc))
    log.info("Tag(s): \"{0}\"".format(tags))
    log.info("Uploading {0}".format(file))

    # flickr.upload(photo_file=file, title=title, description=desc, tags=tags,
    #               safety_level=1,
    #               content_type=1,
    #               is_public=0,
    #               asynchronous=1)
    log.info("Done.\n")


if __name__ == "__main__":
    print("\nFlickr uploader.")
    print(80 * "=")
    auth_check()
