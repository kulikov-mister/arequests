# :sunny: arequests :sunny:
async http-client on micropython for esp32 based on urequests

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/25423296/163456776-7f95b81a-f1ed-45f7-b7ab-8fa810d529fa.png">
  <source media="(prefers-color-scheme: light)" srcset="https://user-images.githubusercontent.com/25423296/163456779-a8556205-d0a5-45e2-ac17-42d089e3c3f8.png">
  <img alt="Shows an illustrated sun in light mode and a moon with stars in dark mode." src="https://user-images.githubusercontent.com/25423296/163456779-a8556205-d0a5-45e2-ac17-42d089e3c3f8.png">
</picture>

### Desciption:
<br>Requires uasyncio V3 or later.
<br>Has optional urequests class to make usable synchronously.


### Use import:
<br>Synchronously: - `from aurequests import urequests as requests`
<br>**or**
<br>Asynchronously: - `import arequests as requests`

### Notes:
<br>**Default HTTP version** - 1.1
<br>**HTTP methods:** GET, HEAD, POST, PUT, DELETE.
<br>**Returns response with the following properties:** content, status_code, reason, url, text, headers, encoder.
<br>**json from response by calling json() method:** ```response.json()```

### Supported
<li>supports headers</li>
<li>supports params</li>
<li>supports HTTP & HTTPS</li>
<li>supports сhunked data</li>
<li>supports redirects</li>
<li>supports timeout, default - 30 seconds</li>
<li>supports custom ports</li><br>

> [!WARNING]
> not supports large  response due to lack of memory - will raise a ConnectionError.
