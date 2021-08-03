""" Reads JPEG files in a directory and uploads them to Flickr.
 - JPEGs are expected to have a Vernon ID before the underscore, i.e. 70152_001.jpg
 - Uses the Auckland Museum API to get record data.
 - Logs to ./flickrUpload.log
"""

import glob
import json
import logging
import os
import sys

import flickr_api
import requests
from decouple import config

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logfile_format = logging.Formatter(
    '%(asctime)s: %(name)s (%(funcName)s): %(message)s')
logfile = logging.FileHandler(filename='flickrUpload.log')
logfile.setFormatter(logfile_format)
logfile.setLevel(logging.DEBUG)

log.addHandler(stream_handler)
log.addHandler(logfile)

authDataFile = "flickrAuthData.txt"
flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')

flickr_api.set_keys(api_key=flickrKey,
                    api_secret=flickrSecret)


def get_keepers(url, http_headers):
    """Gets \"keepers\" (i.e., departments) from the AM API and returns a
    space-delimited string for Flickr's \'tags\' field."""
    keepers = []
    keepers_response = requests.request("GET", url, headers=http_headers)
    if keepers_response.status_code == 200:
        jsonData = json.loads(keepers_response.text)
        for key in jsonData['rdf:value']:
            keepers.append(key['value'])
            keepers = [keeper.replace(' ', '-').lower() for keeper in keepers]
        tags = " ".join(list(map(str, keepers)))
    return tags


def get_JSON():
    """Reads filenames, extracts IDs and retrieves title, description, and
    credit line from the AM API. Adds departments as tags."""
    if glob.glob('*.jpg'):
        log.info("Found {0} JPEG files".format(len(glob.glob('*.jpg'))))
        print("")
        for file in glob.iglob('*.jpg'):
            print("----\n")
            log.info("File: {0}".format(file))
            # We only want the Vernon ID, so split off the rest of the filename
            id = file.split('_')[0]
            url = ("http://api.aucklandmuseum.com/id/humanhistory/object/" + id)
            http_headers = {'Accept': 'application/json'}

            response = requests.request("GET", url, headers=http_headers)

            if response.status_code == 200:
                log.info("Loaded {0}; response {1}.".format(
                    url, response.status_code))
                jsonData = json.loads(response.text)
                log.debug("Response JSON: {0}".format(jsonData))

                title = jsonData['dc:title'][0]['value'].capitalize()
                desc = jsonData['dc:description'][0]['value']
                credit = jsonData['am:creditLine'][0]['value']
                weburl = (
                    'https://www.aucklandmuseum.com/collection/object/am_humanhistory-object-' + id)

                keepers_url = jsonData['ecrm:P50_has_current_keeper'][0]['value']
                tags = ""
                tags = get_keepers(keepers_url, http_headers)

                flickrDesc = ("Title: {0}\nDescription: {1}\nCredit: {2}\n{3}".format(
                    title, desc, credit, weburl))
                upload_photo(file, title, flickrDesc, tags)

            else:
                log.info("Response code {0} on {1}".format(
                    response.status_code, id))
                pass
    else:
        log.exception("No JPEGs in current directory. Exiting.")
        sys.exit()


def get_credentials():
    """Authorise with Flickr."""
    flickrAuthHandler = flickr_api.auth.AuthHandler()
    permissions = 'write'
    url = flickrAuthHandler.get_authorization_url(permissions)

    log.info('Authorisation URL: {0}'.format(url))
    print("Open this URL in a web browser, authorise this script, and you should see an XML file.")
    verification_code = input(
        "Paste the contents of the oauth_verifier tag here: ")
    log.info("Verification code: {0}".format(verification_code))
    flickrAuthHandler.set_verifier(verification_code)
    flickr_api.set_auth_handler(flickrAuthHandler)

    # Save authorisation data to a local file for easy re-use.
    flickrAuthHandler.save('flickrAuthData.txt')
    log.info("Authenticated. Details saved to flickrAuthData.txt.")
    login()


def login():
    """Login to Flickr and report some basic user info."""
    flickr_api.set_auth_handler(authDataFile)
    user = flickr_api.test.login()
    log.info("Logged in as " + (user.username) + " (" + (user.id) + ")")
    log.info("Flickr photo count: {0}".format(user.upload_count))
    get_JSON()


def auth_check():
    """Check flickrAuthData.txt exists and isn't blank,
    then assume it contains valid verification data and begin login process."""
    if os.path.exists(authDataFile) and os.path.getsize(authDataFile) > 0:
        login()
    else:
        get_credentials()


def upload_photo(file, title, desc, tags):
    """Upload the JPEG to Flickr, with title, description, and tags."""
    log.info("Title: \"{0}\"".format(title))
    log.info("Description: \"{0}\"".format(desc))
    log.info("Tag(s): \"{0}\"".format(tags))
    log.info("Uploading {0}".format(file))
    flickr_api.upload(photo_file=file, title=title, description=desc, tags=tags,
                      safety_level=1,
                      content_type=1,
                      #   Comment-out private declaration -- doesn't seem to work
                      #   in any case.
                      #   is_public=0,
                      asynchronous=0)
    print("\n")
    pass


if __name__ == "__main__":
    auth_check()
