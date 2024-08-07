# arequests
async http-client on micropython for esp32 based on urequests

**Desciption:**
<br>Requires uasyncio V3 or later.
<br>Has optional urequests class to make usable synchronously.


**Use import:**
<br>Synchronously: - ```from aurequests import urequests as requests```
<br>**or**
<br>Asynchronously: - ```import arequests as requests```

**Notes:**
<br>**Default HTTP version** - 1.1
<br>**HTTP methods:** - GET, HEAD, POST, PUT, DELETE.
<br>**Returns response with the following properties:** - content, status_code, reason, url, text, headers, encoder.
<br>**json from response by calling json() method:** - ```response.json()```

<br>**Supported**
<li>supports headers</li>
<li>supports params</li>
<li>supports HTTP & HTTPS</li>
<li>supports сhunked data</li>
<li>supports redirects</li>
<li>supports timeout, default - 30 seconds</li>
<li>supports custom ports</li>

<br>**Issues:**
> not supports large  response due to lack of memory - will raise a ConnectionError.
