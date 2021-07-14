# Upload images to a Flickr account

## Libraries 
This project uses @[alexis-mignon](//github.com/alexis-mignon)'s [`python-flickr-api` library](//github.com/alexis-mignon/python-flickr-api), which you can install by running the following command:
```bash
pip install flickr_api
```

It also uses the [builtin `logging` module](//docs.python.org/3/library/logging.html).

## Obtain credentials
[Set up a Flickr App](https://www.flickr.com/services/api/keys), and copy the key and secret into a `.env` file. The script will look here to obtain the credentials.
