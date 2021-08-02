# Upload images to a Flickr account

## Libraries 
This project uses @[alexis-mignon](//github.com/alexis-mignon)'s [`python-flickr-api` library](//github.com/alexis-mignon/python-flickr-api), an interface to [the Flickr API](https://www.flickr.com/services/developer/api/).

Install it using pip:
```bash
pip install flickr_api
```

It also uses the [builtin `logging` module](//docs.python.org/3/library/logging.html) to log to a file called `flickrUpload.log`.

## Obtain credentials
[Set up a Flickr App](https://www.flickr.com/services/api/keys), and copy the key and secret into a `.env` file. The script will look here to obtain the credentials.

Your `.env` file should look like this, with `<key>` and `<secret>` replaced by the actual values:
```
FLICKR_KEY = "<key>"
FLICKR_SECRET = "<secret>"
```



