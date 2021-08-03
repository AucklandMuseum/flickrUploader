# Upload images to a Flickr account

This script reads JPEG files in a directory and uploads them to Flickr.
 - JPEGs are expected to have a Vernon ID before the underscore, i.e. `70152_001.jpg`
 - Uses the [Auckland Museum API](https://api.aucklandmuseum.com) to get record data, using the ID from the filename.
 - Logs to `flickrUpload.log`

## Libraries 
This project uses @[alexis-mignon](//github.com/alexis-mignon)'s [`python-flickr-api` library](//github.com/alexis-mignon/python-flickr-api), an interface to [the Flickr API](//www.flickr.com/services/developer/api/).

## Setup
Install pip dependencies:
```
pip install -r requirements.txt
```
### Obtain credentials
[Set up a Flickr App](https://www.flickr.com/services/api/keys), and copy the key and secret into a `.env` file. The script will look here to obtain the credentials.

Your `.env` file should look like this, with `<key>` and `<secret>` replaced by the actual values:
```
FLICKR_KEY = "<key>"
FLICKR_SECRET = "<secret>"
```

## Run the script
```
python flickrUpload.py
```

