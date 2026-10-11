# Request authority behind port mappings

Publication gate: merge this into `pages/request-response.md` only after
`naf/framework` v0.2.11 is published and its Composer source revision is verified.

## Request URI and Host

`request()->getUri()` uses the authority sent in `Host`, including an explicit port.
An internal `SERVER_PORT` does not add a port when the browser's `Host` omits it.
For example, a request for `https://board.example.test/settings` remains on that
origin when the container listens on port 8443. An explicit
`Host: board.example.test:9443` preserves port 9443.

`request()->getHeader('Host')` contains one value. The request factory's synthesized
Host is replaced by the original header instead of being combined with it. The
request method, path, query, cookies and other headers remain intact.

This correction does not configure proxy trust or change scheme detection. Configure
HTTPS and any trusted proxy headers at the host boundary as before.
