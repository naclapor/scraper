# scraper
A tool to record a website by visiting it. It will just replay the requests recorded during the "record" phase.

## Usage
First of all, you need to prepare the virtualenv:
``` bash
$ ./bin/prepare_venv.sh
```

### Record
Launch the proxy server giving a name for the database:
``` bash
$ ./bin/run_scraper.sh database_name
```

Configure your browser to use the proxy at `127.0.0.1:8080` (you should also install the CA certificate in `~/.mitmproxy/`) and use it to navigate the website.

### Replay
To replay the website offline, launch the replay server using the following command:
``` bash
$ ./bin/run_replayer database_name
```

Then, you can configure your browser to use the same proxy at `127.0.0.1:8080` and enjoy the website offline.

## Random Notes
Requests are saved in a sqlite database using the following quadriplet as key: (HOSTNAME, HTTP_REQ_METHOD, HTTP_REQ_PATH, HTTP_REQ_BODY). If the client performs a request with the same quadriplet two times, the recorder will _not_ overwrite the old request, discarding the new one.

Due to this behavior, we advise to navigate the website *after* logging in, so that the saved requests refers to the logged user. Furthermore, beware of cached requests, they won't be saved into the database.

Thus, a typical use of the tool could be the following:
- log into the website;
- delete all cached resources *but* cookies;
- run the website through the proxy;
- replay the requests.

Notice that if you open the database multiple times, the requests are added to the existing database, so the deleting the cached resources could be done only the first time the database is created.

The recorder records only the following headers from the server: "content-type", "location".
