# arequests
async http-client on micropython for esp32 based on urequests

**Desciption:**
Requires uasyncio V3 or later.
Has optional urequests class to make usable synchronously.


**Use import:**<br>
Synchronously: - ```from aurequests import urequests as requests```

or
<br>Asynchronously: - ```import arequests as requests```

**Notes:**
**Default HTTP version** - 1.1
**HTTP methods:** - GET, HEAD, POST, PUT, DELETE.

**Returns response with the following properties:** - content, status_code, reason, url, text, headers, encoder.
**json from response by calling json() method:** - ```response.json()```

**Supported**
supports headers
supports params
supports HTTP & HTTPS
supports сhunked data
supports redirects
supports timeout, default - 30 seconds
supports custom ports


**Issues:**
not supports large  response due to lack of memory - will raise a ConnectionError.
