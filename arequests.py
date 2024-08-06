import gc
import uasyncio as asyncio
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc()) # sets threshold to 1/4 of heap size
gc.enable()


__version__ = "0.1.0"
HTTP__version__ = "1.0"


class TimeoutError(Exception):
    pass


class ConnectionError(Exception):
    pass


class Response:

    def __init__(self, reader, chunked, charset, h, length):
        self.raw = reader
        self.chunked = chunked
        self.encoder = charset
        self.h = h
        self.content_length = length
        self.chunk_size = 0
    
    async def read(self, sz=-1):
        content = b''
        # keep reading chunked data
        if self.chunked:
            sz = 4*1024
            while 1:
                if self.chunk_size == 0:
                    l = await self.raw.readline() # get Hex size
                    l = l.split(b";", 1)[0]
                    self.chunk_size = int(l, 16) # convert to int
                    if self.chunk_size == 0: # end of message
                        sep = await self.raw.read(2)
                        assert sep == b"\r\n"
                        break
                data = await self.raw.read(min(sz, self.chunk_size))
                self.chunk_size -= len(data)
                content += data
                if self.chunk_size == 0:
                    sep = await self.raw.read(2)
                    assert sep == b"\r\n"
                    break
        # non chunked data
        else:
            data = await self.raw.read(min(self.content_length,4096))
            content += data
            residual = self.content_length - len(data)
            while residual > 0:
                data = await self.raw.read(residual)
                residual -= len(data)
                content += data
        return content
    
    @property
    def text(self):
        return str(self.content, self.encoder)
    
    @property
    def headers(self):
        result = {}
        for i in self.h:
             h = i.decode(self.encoder).strip().split(":", 1)
             result[h[0]] = h[-1].strip()
        return result

    def json(self):
        import ujson
        return ujson.loads(self.content)
    
    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
    
    def __repr__(self):
        return "<Response [%d]>" % (self.status_code)


async def open_connection(host, port, ssl):
    '''
    replaces asyncio.open_connect in order to add ssl support
    SSL will block
    '''
    from uasyncio import core
    from uasyncio.stream import Stream
    from uerrno import EINPROGRESS
    import usocket as socket
    gc.collect()

    ai = socket.getaddrinfo(host, port)[0]
    s = socket.socket(ai[0], ai[1], ai[2])
    s.setblocking(False)
    try:
        s.connect(ai[-1])
    except OSError as er:
        if er.args[0] != EINPROGRESS:
            raise er
    yield core._io_queue.queue_write(s)
    if ssl:
        import ussl
        s = ussl.wrap_socket(s, server_hostname=host) # WARNING, this blocks for a long time
    yield core._io_queue.queue_write(s)
    ss = Stream(s)
    return ss, ss


async def _request_raw(method, url, headers, data, json):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    try:
        host, port = host.split(":")
        if proto == "https:":
            ssl = True
        elif proto == "http:":
            ssl = False
        else:
            raise ValueError("Unsupported protocol: %s" % (proto))
    except ValueError:
        if proto == "http:":
            port = 80
            ssl = False
        elif proto == "https:":
            port = 443
            ssl = True
        else:
            raise ValueError("Unsupported protocol: %s" % (proto))
    # using new open_connection rather than uasyncio.open_connection to add ssl support
    reader, writer = await open_connection(host, port, ssl)
    query = "%s /%s HTTP/%s\r\nHost: %s\r\nConnection: close\r\n%s" % (method, path, HTTP__version__, host, headers)
    if "User-Agent:" not in query:
        query += "User-Agent: compat\r\n"
    if json is not None:
        assert data is None
        import ujson
        data = ujson.dumps(json)
        if "Content-Type:" not in query:
            query += "Content-Type: application/json\r\n"
    if data:
        if "Content-Length:" not in query:
            query += "Content-Length: %d\r\n" % len(data)
    query += "\r\n"
    if data:
        query += data
    await writer.awrite(query.encode())
    return reader


async def _requests(method, url, params={}, data=None, headers={}, cookies=None, \
                    files=None, auth=None, timeout=None, allow_redirects=True, \
                    proxies=None, hooks=None, stream=None, verify=None, cert=None, json=None):
    try:
        #headers support
        h = ""
        for k in headers:
            h += "{}: {}\r\n".format(k, headers[k])
        # params support
        if params:
            url = url.rstrip("?")
            url += "?"
            for p in params:
                url += "{}={}&".format(p, params[p])
            url = url[0:len(url)-1]
    except Exception as e:
        raise e
    try:
        # build in redirect support
        redir_cnt = 0
        redir_url = None
        while redir_cnt < 2:
            reader = await _request_raw(method=method, url=url, headers=h, data=data, json=json)
            sline = await reader.readline()
            sline = sline.split(None, 2)
            status_code = int(sline[1])
            if len(sline) > 1:
                reason = sline[2].decode().rstrip()
            chunked = False
            json = None
            headers = []
            charset = 'utf-8'
            content_length = -1
            # read headers
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break
                headers.append(line)
                if line.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in line:
                        chunked = True
                elif line.startswith(b"Location:"):
                    url = line.rstrip().split(None, 1)[1].decode()
                elif line.startswith(b"Content-Length:"):
                    if not chunked:
                        try:
                            content_length = int(line.rstrip().split(None, 1)[1].decode())
                        except:
                            pass
                elif line.startswith(b"Content-Type:"):
                    if b"application/json" in line:
                        json = True
                    if b"charset" in line:
                        # get decoder
                        charset = line.rstrip().decode().split(None, 2)[-1].split("=")[-1]
            #look for redirects
            if allow_redirects is False:
                break
            if 301 <= status_code <= 303:
                redir_cnt += 1
                await reader.wait_closed()
                continue
            break

        resp = Response(reader, chunked, charset, headers, content_length)
        resp.content = await resp.read()
        resp.status_code = status_code
        resp.reason = reason
        resp.url = url
        return resp
    
    except Exception as e:
        raise ConnectionError(e)
    finally:
        try:
            await reader.wait_closed()
        except NameError:
            pass
        gc.collect()

async def get(url, timeout=30, **kwargs):
    try:
        return await asyncio.wait_for(_requests("GET", url, **kwargs), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(e)
    

async def head(url, timeout=30, **kwargs):
    try:
        return await asyncio.wait_for(_requests("HEAD", url, **kwargs), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(e)


async def post(url, timeout=30, **kwargs):
    try:
        return await asyncio.wait_for(_requests("POST", url, **kwargs), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(e)


async def put(url, timeout=30, **kwargs):
    try:
        return await asyncio.wait_for(_requests("PUT", url, **kwargs), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(e)


async def delete(url, timeout=30, **kwargs):
    try:
        return await asyncio.wait_for(_requests("DELETE", url, **kwargs), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(e)


# Makes it usable synchronously, but cannot use this class asynchronously because it was lockup the coro.
class urequests:

    @staticmethod
    def get(url, **kwargs):
        return asyncio.run(get(url, **kwargs))
    
    @staticmethod
    def head(url, **kwargs):
        return asyncio.run(head(url, **kwargs))

    @staticmethod
    def post(url, **kwargs):
        return asyncio.run(post(url, **kwargs))
        
    @staticmethod
    def put(url, **kwargs):
        return asyncio.run(put(url, **kwargs))

    @staticmethod
    def delete(url, **kwargs):
        return asyncio.run(delete(url, **kwargs))
