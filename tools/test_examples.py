#!/usr/bin/env python3
"""Exercise the actual file-titled Markdown examples against published Composer packages.

No example PHP is duplicated here. Each fixture copies the documented files, then tests
observable behavior through a real PHP HTTP server. Servers and fixtures are cleaned up.
"""
import argparse
import base64
from contextlib import contextmanager
import http.cookiejar
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

PAGES = Path(__file__).resolve().parent.parent / 'pages'
BLOCKS = re.compile(r'^```[\w+-]+ title="([^"]+)"\n(.*?)^```\s*$', re.M | re.S)
PHP = shlex.split(os.environ.get('PHP_COMMAND', 'php'))
COMPOSER = shlex.split(os.environ.get('COMPOSER_COMMAND', 'composer'))
checks = 0


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{shlex.join(command)} failed:\n{result.stdout}\n{result.stderr}')
    return result.stdout


def copy_examples(page, root):
    blocks = BLOCKS.findall((PAGES / page).read_text())
    if not blocks:
        raise RuntimeError(f'No complete file blocks in {page}')
    for name, content in blocks:
        target = (root / name).resolve()
        if not target.is_relative_to(root.resolve()):
            raise RuntimeError(f'Example path escapes fixture: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        if target.suffix in ('.php', '.phtml'):
            run([*PHP, '-l', str(target)], root)
        elif target.suffix == '.py':
            compile(content, str(target), 'exec')
    (root / 'storage/mail').mkdir(parents=True, exist_ok=True)


def expect(condition, message):
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1


def fragment(page, marker, language='php-inline'):
    """Extract a documented fragment following its exact introduction."""
    source = (PAGES / page).read_text().split(marker, 1)
    if len(source) != 2:
        raise RuntimeError(f'Missing example introduction in {page}: {marker}')
    block = re.search(r'^```' + re.escape(language) + r'\n(.*?)^```', source[1], re.M | re.S)
    if not block:
        raise RuntimeError(f'Missing example fragment in {page}')
    return block.group(1)


def bootstrap_include(root, name):
    bootstrap = root / 'bootstrap.php'
    source = bootstrap.read_text()
    bootstrap.write_text(source.replace('app()->run();', f"require_once BASE_PATH . '/{name}';\n\napp()->run();"))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, port):
        self.base = f'http://127.0.0.1:{port}'
        self.opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, path, method='GET', data=None, headers=None):
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        try:
            result = self.opener.open(req, timeout=5)
        except urllib.error.HTTPError as error:
            result = error
        with result:
            return result.status, result.headers, result.read().decode()

    def form(self, path, data):
        return self.request(path, 'POST', urllib.parse.urlencode(data).encode(),
                            {'Content-Type': 'application/x-www-form-urlencoded'})


def csrf(result):
    match = re.search(r'name="_csrf" value="([^"]+)"', result[2])
    preview = re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', re.sub(r'<style>.*?</style>', '', result[2], flags=re.S)))[:2500]
    expect(bool(match), f'CSRF field missing (status {result[0]}): {preview}')
    return match[1]


@contextmanager
def server(root, router=None, environment=None):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryFile(mode='w+') as log:
        command = [*PHP, '-S', f'127.0.0.1:{port}', '-t', str(root / 'public')]
        if router:
            command.append(str(root / router))
        process = subprocess.Popen(command,
                                   cwd=root, stdout=log, stderr=log,
                                   env={**os.environ, **(environment or {})})
        try:
            client = Client(port)
            for attempt in range(100):
                try:
                    client.request('/')
                    break
                except urllib.error.URLError:
                    if process.poll() is not None:
                        raise RuntimeError('PHP server failed to start')
                    time.sleep(.05)
            else:
                raise RuntimeError('PHP server readiness timed out')
            yield client
        except Exception:
            log.seek(0)
            print(log.read()[-6000:])
            application_log = root / 'logs/app.log'
            if application_log.exists():
                print(application_log.read_text()[-4000:])
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def test_first(client):
    home = client.request('/')
    expect(home[0] == 200 and 'Hello, World!' in home[2], 'First app home page')
    result = client.request('/hello/Ada')
    expect(result[0] == 200 and json.loads(result[2]) == {'hello': 'Ada'}, 'First app JSON route')
    expect('application/json' in result[1]['Content-Type'], 'JSON content type')
    expect(client.request('/does-not-exist')[0] == 404, 'Unknown HTML route')


def test_small_website(root):
    with server(root) as client:
        home = client.request('/')
        expect(home[0] == 200 and 'Hello, visitor!' in home[2], 'Small website default greeting')
        expect('text/html' in home[1]['Content-Type'], 'Small website HTML response type')
        expect(home[1]['X-Content-Type-Options'] == 'nosniff', 'Small website prevents MIME sniffing')
        policy = home[1]['Content-Security-Policy']
        expect("default-src 'none'" in policy and "style-src 'self'" in policy
               and "frame-ancestors 'none'" in policy, 'Small website CSP allows local CSS and blocks framing')
        expect(home[1]['Referrer-Policy'] == 'strict-origin-when-cross-origin', 'Small website referrer policy')
        about = client.request('/about')
        for result in (home, about):
            expect(result[0] == 200 and 'aria-label="Main navigation"' in result[2]
                   and 'href="/about"' in result[2] and 'href="/css/site.css"' in result[2]
                   and 'Built with NAF and ordinary PHP.' in result[2], 'Both website pages use the shared layout')
        expect('About this site' in about[2] and '<title>About · Small NAF site</title>' in about[2],
               'Small website About content and title')
        css = client.request('/css/site.css')
        expect(css[0] == 200 and 'text/css' in css[1]['Content-Type'], 'Local stylesheet is served')
        expect('Set-Cookie' not in home[1], 'Small website needs no session cookie')
        for name in ('Ada', 'Zoë', 'a' * 80):
            greeting = client.request('/?name=' + urllib.parse.quote(name))
            expect(greeting[0] == 200 and f'Hello, {name}!' in greeting[2], 'Website accepts valid names at the byte limit')
        blank = client.request('/?name=%20%20')
        expect(blank[0] == 200 and 'Hello, visitor!' in blank[2], 'Blank name uses the default greeting')
        injection = client.request('/?name=' + urllib.parse.quote('\"><script>alert(1)</script>'))
        expect(injection[0] == 200 and '<script>' not in injection[2]
               and '&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;' in injection[2],
               'Website escapes HTML text and quoted attribute injection')
        for query in ('name%5B%5D=Ada', 'name=' + 'a' * 81, 'name=' + urllib.parse.quote('ë' * 41), 'name=%FF'):
            expect(client.request('/?' + query)[0] == 400, 'Website rejects arrays, oversized names and invalid UTF-8')
        unknown = client.request('/missing')
        expect(unknown[0] == 404 and unknown[1]['X-Content-Type-Options'] == 'nosniff',
               'Website unknown route retains response headers')
    # A missing trusted template is an actual application failure; production must hide its details.
    template = root / 'app/views/about.phtml'
    original = template.read_text()
    template.unlink()
    try:
        with server(root, environment={'APP_ENV': 'prod'}) as client:
            failure = client.request('/about')
            expect(failure[0] == 500 and 'View about not found' not in failure[2]
                   and str(root) not in failure[2], 'Production website hides template exception details')
    finally:
        template.write_text(original)


def test_simple_api(root):
    with server(root) as client:
        listing = client.request('/api/products')
        data = json.loads(listing[2])
        expect(listing[0] == 200 and data['currency'] == 'EUR'
               and [product['id'] for product in data['data']] == ['notebook', 'pencil'], 'Storage-free API returns the public catalog')
        expect('application/json' in listing[1]['Content-Type']
               and listing[1]['X-Content-Type-Options'] == 'nosniff', 'Storage-free API JSON response headers')
        expect('Set-Cookie' not in listing[1], 'Storage-free API needs no session cookie')
        first = json.loads(client.request('/api/products?limit=1')[2])
        expect(first['data'] == [data['data'][0]], 'API limit bounds the returned list')
        maximum = client.request('/api/products?limit=100')
        expect(maximum[0] == 200 and json.loads(maximum[2]) == data, 'API accepts its maximum limit')
        for identifier, product in zip(('notebook', 'pencil'), data['data']):
            detail = client.request('/api/products/' + identifier)
            expect(detail[0] == 200 and json.loads(detail[2]) == {'data': product, 'currency': 'EUR'},
                   'API resolves a named route parameter and injected catalog service')
        for query in ('limit=0', 'limit=-1', 'limit=101', 'limit=text', 'limit=1.5',
                      'limit%5B%5D=1', 'limit=', 'limit=' + '9' * 100):
            invalid = client.request('/api/products?' + query)
            expect(invalid[0] == 400 and json.loads(invalid[2]) == {'error': 'limit must be an integer from 1 to 100.'},
                   'API rejects invalid limit types and values')
        missing = client.request('/api/products/missing')
        expect(missing[0] == 404 and json.loads(missing[2]) == {'error': 'Product not found.'}, 'API product lookup is exact')
        unknown = client.request('/unknown')
        expect(unknown[0] == 404 and json.loads(unknown[2]) == {'error': 'Request refused'}
               and unknown[1]['X-Content-Type-Options'] == 'nosniff', 'API unknown-route errors are JSON with response headers')
        refused = client.request('/api/products', 'POST', b'{}', {'Content-Type': 'application/json'})
        expect(400 <= refused[0] < 500 and 'error' in json.loads(refused[2]), 'Read-only API offers no write endpoint')
        expect(json.loads(client.request('/api/products')[2]) == data, 'Refused write leaves the catalog unchanged')
    catalog = root / 'app/Services/ProductCatalog.php'
    original = catalog.read_text()
    catalog.write_text(original.replace('return [', "throw new \\RuntimeException('Catalog source unavailable: private-service-token');\n        return [", 1))
    try:
        with server(root) as client:
            failure = client.request('/api/products')
            expect(failure[0] == 500 and json.loads(failure[2]) == {'error': 'Internal server error'},
                   'Unexpected catalog failure returns sanitized JSON even in development')
            expect('application/json' in failure[1]['Content-Type']
                   and failure[1]['X-Content-Type-Options'] == 'nosniff', 'API failure retains JSON response headers')
        logs = '\n'.join(path.read_text() for path in (root / 'logs').rglob('*.log'))
        expect('private-service-token' in logs, 'API exception details are logged for the operator')
    finally:
        catalog.write_text(original)


def test_flow(root, client):
    full = client.request('/flow-example')
    expect(full[0] == 200 and '3 results' in full[2], 'Flow full page renders the catalog')
    expect(full[2].count('src="/_flow/flow.js"') == 1, 'Flow runtime asset is rendered once')
    expect(full[2].count('src="/js/flow-example.js"') == 1, 'Flow application module is rendered once')
    expect("script-src 'self'" in full[1]['Content-Security-Policy'], 'Flow example uses strict CSP')
    filtered = client.request('/flow-example?q=view')
    expect(filtered[0] == 200 and '1 results' in filtered[2]
           and '<!doctype html>' in filtered[2], 'Flow GET fallback renders a full page')
    expect(filtered[2].count('value="view"') == 2, 'Flow server query initializes both store consumers')
    fragment = client.request('/flow-example?q=queue', headers={'X-Flow': 'fragment'})
    expect(fragment[0] == 200 and 'Queues and workers' in fragment[2]
           and '1 results' in fragment[2], 'Flow fragment renders filtered results')
    expect(fragment[1]['X-Flow'] == 'fragment' and 'X-Flow' in fragment[1]['Vary'],
           'Flow fragment has its response and cache variation headers')
    expect('<html' not in fragment[2] and '<script' not in fragment[2], 'Flow returns only the selected fragment')
    expect(client.request('/flow-example?q%5B%5D=view')[0] == 400, 'Flow rejects array queries')
    expect(client.request('/flow-example?q=' + 'a' * 81)[0] == 400, 'Flow rejects long queries')
    escaped = client.request('/flow-example?q=' + urllib.parse.quote('<svg onload="alert(1)">'))
    expect(escaped[0] == 200 and '<svg' not in escaped[2]
           and '&lt;svg' in escaped[2] and '&quot;' in escaped[2], 'Flow escapes query attributes')
    runtime = client.request('/_flow/flow.js')
    bundle = root / 'vendor/naf/flow/src/Resources/public/flow.min.js'
    expect(runtime[0] == 200 and runtime[2] == bundle.read_text(), 'Flow serves the published prebuilt bundle')
    expect(client.request('/_flow/flow.js', headers={'If-None-Match': runtime[1]['ETag']})[0] == 304,
           'Flow validates its runtime ETag')
    for module in (root / 'public/js').rglob('*.js'):
        path = '/' + module.relative_to(root / 'public').as_posix()
        expect(client.request(path)[0] == 200, f'Flow documented module is served: {path}')


def test_starter(client):
    """Check create-project before any command can replace its locked dependencies."""
    home = client.request('/')
    expect(home[0] == 200 and 'Welcome to your new App!' in home[2], 'Untouched starter home')
    expect(client.request('/css/naf.css')[0] == 200, 'Untouched starter CSS')
    contact = client.request('/contact')
    expect(contact[0] == 200, 'Untouched starter contact page')
    invalid = client.form('/contact', {'_csrf': csrf(contact), 'firstname': 'Ada',
                                      'lastname': 'Lovelace', 'message': 'short'})
    expect(invalid[0] == 200 and 'At least 10' in invalid[2], 'Untouched starter form validation')
    valid = client.form('/contact', {'_csrf': csrf(client.request('/contact')), 'firstname': 'Ada',
                                    'lastname': 'Lovelace', 'message': 'A local starter test.'})
    expect(valid[0] == 302 and valid[1]['Location'] == '/contact', 'Untouched starter redirect')
    expect(client.form('/api', {'name': 'Ada'})[0] == 400, 'Untouched starter CSRF guard')
    invalid = client.form('/api', {'_csrf': csrf(client.request('/contact')), 'name': ''})
    expect(invalid[0] == 422 and 'name' in json.loads(invalid[2])['fields'], 'Untouched starter API validation')
    valid = client.form('/api', {'_csrf': csrf(client.request('/contact')), 'name': 'Ada'})
    expect(valid[0] == 200 and json.loads(valid[2]) == {'data': {'hello': 'Ada'}}, 'Untouched starter API JSON')


def test_contact(root, client):
    token = csrf(client.request('/contact'))
    expect(client.form('/contact', {'name': 'Ada'})[0] == 400, 'Missing CSRF rejected')
    invalid = client.form('/contact', {'_csrf': token, 'name': '<script>alert(1)</script>',
                                      'email': 'invalid', 'message': 'short'})
    expect(invalid[0] == 422 and 'error-msg' in invalid[2], 'Contact validation errors')
    expect('&lt;script&gt;' in invalid[2] and '<script>alert(1)' not in invalid[2], 'Escaped form memory')
    expect(not list((root / 'storage/mail').glob('*.json')), 'Invalid contact sends nothing')
    token = csrf(invalid)
    valid = client.form('/contact', {'_csrf': token, 'name': 'Ada', 'email': 'ada@example.com',
                                    'message': 'A local test message.'})
    expect(valid[0] == 302 and valid[1]['Location'] == '/contact', 'Contact redirects')
    files = list((root / 'storage/mail').glob('*.json'))
    expect(len(files) == 1, 'Exactly one local mail preview')
    mail = json.loads(files[0].read_text())
    expect(mail['replyTo'] == 'ada@example.com' and 'A local test message.' in mail['content']
           and mail['isHtml'] is False, 'Mail contents and plain-text flag')
    expect('Thank you' in client.request('/contact')[2], 'Flash message after redirect')
    expect('Thank you' not in client.request('/contact')[2], 'Flash consumed once')


def test_login(root, client):
    expect(client.request('/account')[0] == 401, 'Guests cannot open account')
    token = csrf(client.request('/login'))
    expect(client.form('/login', {'username': 'demo', 'password': 'local-demo-password'})[0] == 400,
           'Login without CSRF rejected')
    failed = client.form('/login', {'_csrf': token, 'username': 'demo', 'password': 'wrong-password'})
    expect(failed[0] == 422 and 'did not match an account' in failed[2], 'Wrong password rejected')
    expect('value="demo"' in failed[2] and 'wrong-password' not in failed[2], 'Username retained, password omitted')
    success = client.form('/login', {'_csrf': csrf(failed), 'username': 'demo', 'password': 'local-demo-password'})
    expect(success[0] == 302 and success[1]['Location'] == '/account', 'Successful login redirects')
    account = client.request('/account')
    expect(account[0] == 200 and 'Signed in as demo' in account[2], 'Login persists into next request')
    expect(client.form('/logout', {})[0] == 400, 'Logout without CSRF rejected')
    expect(client.form('/logout', {'_csrf': csrf(account)})[0] == 302, 'Logout redirects')
    expect(client.request('/account')[0] == 401, 'Logout removes access')
    client.form('/login', {'_csrf': csrf(client.request('/login')), 'username': 'demo', 'password': 'local-demo-password'})
    with sqlite3.connect(root / 'storage/app.sqlite') as database:
        database.execute('UPDATE users SET suspended = 1 WHERE username = ?', ('demo',))
    expect(client.request('/account')[0] == 401, 'Suspension invalidates an existing session')


def test_api(root):
    with server(root) as client:
        initial = client.request('/api/articles')
        expect(initial[0] == 200 and json.loads(initial[2]) == {'data': []}, 'API starts empty')
        expect('application/json' in initial[1]['Content-Type'], 'API JSON content type')
        request = lambda body, path='/api/articles': client.request(path, 'POST', body.encode(), {'Content-Type': 'application/json'})
        for body, status in [('{', 400), ('[]', 422), ('null', 422), ('{}', 422), ('{"title":[],"body":"ok"}', 422)]:
            result = request(body)
            expect(result[0] == status and 'error' in json.loads(result[2]), f'API rejects {body}')
        expect(client.form('/api/articles', {'title': 'a', 'body': 'b'})[0] == 415, 'API rejects form media type')
        expect(request('{}', '/api/articles?title=a&body=b')[0] == 422, 'Query does not fill missing body fields')
        for article in [{'title': ' ', 'body': 'ok'}, {'title': 'a' * 201, 'body': 'ok'},
                        {'title': 'ok', 'body': 'b' * 10001}]:
            invalid = request(json.dumps(article))
            expect(invalid[0] == 422 and 'fields' in json.loads(invalid[2]), 'API validates article field limits')
        saved = request('{"title":"First article","body":"Hello from NAF."}')
        article = {'id': 1, 'title': 'First article', 'body': 'Hello from NAF.'}
        expect(saved[0] == 201 and json.loads(saved[2]) == {'data': article}, 'API saves article with associative PDO rows')
        location = saved[1]['Location']
        expect(location == '/api/articles/1', 'API Location points to the named article route')
        expect(json.loads(client.request(location)[2])['data']['body'] == 'Hello from NAF.', 'API reads article')
        expect('0 migration(s) successfully executed.' in run([*PHP, 'vendor/bin/naf', 'db:migrate', 'up'], root),
               'Repeating migration skips the applied schema')
        expect(json.loads(client.request('/api/articles')[2]) == {'data': [article]}, 'Repeating migration preserves articles')
        with sqlite3.connect(root / 'storage/articles.sqlite') as database:
            migrations = database.execute('SELECT name FROM migrations').fetchall()
        expect(migrations == [('App\\Migrations\\CreateArticlesTable',)], 'Database plugin tracks one application migration')
        quoted_title = "An article'); DROP TABLE articles; --"
        quoted = client.request('/api/articles', 'POST',
                                json.dumps({'id': 999, 'title': quoted_title, 'body': 'Stored as text.'}).encode(),
                                {'Content-Type': 'Application/JSON; charset=utf-8'})
        quoted_article = json.loads(quoted[2])['data']
        expect(quoted[0] == 201 and quoted_article == {'id': 2, 'title': quoted_title, 'body': 'Stored as text.'},
               'Prepared values stay literal, media type parameters work and extra fields are ignored')
        expect(client.request('/api/articles/1%20OR%201=1', 'DELETE')[0] == 404, 'Bound article ID cannot alter the delete query')
        expect(client.request(quoted[1]['Location'], 'DELETE')[0] == 204, 'Quoted article can be deleted normally')
        unknown = client.request('/unknown')
        expect(unknown[0] == 404 and 'error' in json.loads(unknown[2]), 'Unknown API route returns JSON')
    with server(root) as client:
        expect(client.request(location)[0] == 200, 'Article survives a server restart')
        deleted = client.request(location, 'DELETE')
        expect(deleted[0] == 204 and deleted[2] == '', 'DELETE has an empty 204 body')
        expect(client.request(location)[0] == 404, 'Deleted article is missing')
        expect(client.request(location, 'DELETE')[0] == 404, 'Deleting missing article returns 404')
        request = client.request('/api/articles', 'POST', b'{"title":"Before rollback","body":"Temporary."}',
                                 {'Content-Type': 'application/json'})
        expect(request[0] == 201, 'Article exists before migration rollback')
        expect('1 migration(s) successfully executed.' in run(
            [*PHP, 'vendor/bin/naf', 'db:migrate', 'down', '--name=CreateArticlesTable'], root),
            'Named migration rolls back through the CLI')
        with sqlite3.connect(root / 'storage/articles.sqlite') as database:
            expect(database.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'articles'").fetchone() is None,
                   'Rollback removes the article table')
            expect(database.execute('SELECT COUNT(*) FROM migrations').fetchone()[0] == 0, 'Rollback removes migration history')
        expect('1 migration(s) successfully executed.' in run([*PHP, 'vendor/bin/naf', 'db:migrate', 'up'], root),
               'Migration can be applied after rollback')
        recreated = client.request('/api/articles')
        expect(recreated[0] == 200 and json.loads(recreated[2]) == {'data': []}, 'Reapplied migration creates an empty usable schema')
        # A real storage failure must still produce a sanitized JSON error.
        with sqlite3.connect(root / 'storage/articles.sqlite') as database:
            database.execute('DROP TABLE articles')
        failure = client.request('/api/articles')
        expect(failure[0] == 500 and json.loads(failure[2]) == {'error': 'Internal server error'}, 'Unexpected API exception sanitized')
        expect('no such table: articles' in (root / 'logs/app.log').read_text(), 'Persistent API logs the actual database failure')


def test_integrations(root):
    for page in ('first-app.md', 'testing.md', 'http-client.md', 'file-downloads.md',
                 'queues.md', 'scheduling.md', 'mcp.md', 'console.md'):
        copy_examples(page, root)
    plugin = root.parent / 'hello-plugin'
    plugin.mkdir()
    copy_examples('plugins.md', plugin)
    run([*COMPOSER, 'config', 'repositories.docs-plugin', 'path', str(plugin)], root)
    run([*COMPOSER, 'require', 'example/naf-hello:@dev', '--no-interaction', '--prefer-dist'], root)
    bootstrap_include(root, 'app/schedule.php')
    command = fragment('console.md', '## Register a command')
    (root / 'app/commands.php').write_text('<?php\n\n' + command)
    bootstrap_include(root, 'app/commands.php')
    registration = fragment('mcp.md', 'Register the tool in root `bootstrap.php`')
    (root / 'app/mcp.php').write_text('<?php\n\n' + registration)
    bootstrap_include(root, 'app/mcp.php')
    routes = fragment('file-downloads.md', 'Add this fragment to the existing `app/routes.php`:')
    (root / 'app/download-routes.php').write_text('<?php\n\n' + routes)
    with (root / 'app/routes.php').open('a') as file:
        file.write("\nrequire __DIR__ . '/download-routes.php';\n")
    (root / 'storage/files').mkdir(parents=True)
    (root / 'storage/files/example.txt').write_text('Example download\n')
    reports = root / 'storage/reports'
    reports.mkdir(parents=True)
    (reports / 'report.txt').write_text('Report\n')
    (reports / 'nested').mkdir()
    (reports / 'nested/second.txt').write_text('Second\n')
    (reports / 'outside.txt').symlink_to(root / 'composer.json')
    run([*COMPOSER, 'dump-autoload', '--no-interaction'], root)

    expect('OK (2 tests, 2 assertions)' in run(
        [*PHP, 'vendor/bin/phpunit', '--bootstrap', 'vendor/autoload.php', 'tests/GreetingTest.php'], root),
        'Documented PHPUnit service tests')
    expect('HTTP transport test passed.' in run([*PHP, 'bin/http-client-demo.php'], root),
           'Fake transport retries without network delivery')
    expect('Hello, World!' in run([*PHP, 'vendor/bin/naf', 'hello:say', 'World'], root),
           'Application command is registered and runs through the CLI')
    missing_name = subprocess.run([*PHP, 'vendor/bin/naf', 'hello:say'], cwd=root, capture_output=True)
    expect(missing_name.returncode != 0, 'Application command rejects a missing required argument')
    expect('Job queued.' in run([*PHP, 'bin/enqueue-demo.php'], root), 'Queue producer runs through application bootstrap')
    expect('Recorded signup for user 42' in run([*PHP, 'vendor/bin/naf', 'queue:consume', '--once'], root),
           'Queue worker constructs and executes the documented job')
    producer = root / 'bin/enqueue-demo.php'
    producer.write_text(producer.read_text().replace("'user_id' => 42", "'user_id' => 0"))
    run([*PHP, 'bin/enqueue-demo.php'], root)
    for attempt in range(3):
        failed = subprocess.run([*PHP, 'vendor/bin/naf', 'queue:consume', '--once', '--verbose'],
                                cwd=root, capture_output=True, text=True)
        expect(failed.returncode != 0 and 'positive user_id' in failed.stdout + failed.stderr,
               f'Invalid job payload fails worker attempt {attempt + 1}')
    deadletters = list((root / 'storage/queue/deadletter').rglob('*.job'))
    expect(len(deadletters) == 1, 'Failed job is retained in the documented deadletter directory')
    run([*PHP, 'vendor/bin/naf', 'queue:retry-failed', '--keep'], root)
    expect(deadletters[0].is_file(), 'Retry with --keep retains the original failure')
    for attempt in range(3):
        retried = subprocess.run([*PHP, 'vendor/bin/naf', 'queue:consume', '--once', '--verbose'],
                                 cwd=root, capture_output=True, text=True)
        expect(retried.returncode != 0 and 'positive user_id' in retried.stdout + retried.stderr,
               f'Retried job reaches worker attempt {attempt + 1}')
    run([*PHP, 'vendor/bin/naf', 'schedule:ticker', '--once'], root)
    expect((root / 'storage/schedule-state.json').is_file(), 'Scheduler writes application-specific state')
    expect('Scheduled heartbeat executed.' in run([*PHP, 'vendor/bin/naf', 'queue:consume', '--once'], root),
           'Ticker and worker execute the documented scheduled job')

    def token(scope):
        output = run([*PHP, 'vendor/bin/naf', 'mcp:token:create', 'Documentation test', '--scope', scope], root)
        plain = re.sub(r'\x1b\[[0-9;]*m', '', output)
        match = re.search(r'Token:\s+(mcp_\S+)', plain)
        expect(bool(match), 'MCP CLI creates a scoped bearer token')
        return match.group(1)

    allowed = token('folders:read')
    denied = token('articles:read')
    with server(root) as client:
        plugin_response = client.request('/plugin-hello')
        expect(plugin_response[0] == 200 and json.loads(plugin_response[2]) == {'message': 'Hello from the plugin'},
               'Composer discovers the documented plugin and loads its route and controller')
        expect('HTTP smoke tests passed.' in run([sys.executable, 'tests/http_smoke.py', client.base], root),
               'Documented HTTP smoke test runs against a live application')
        download = client.request('/downloads/example')
        expect(download[0] == 200 and download[2] == 'Example download\n', 'Download stream emits file contents')
        expect(download[1]['Content-Disposition'] == 'attachment; filename="example.txt"', 'Controlled download filename')
        expect(client.request('/downloads/unknown')[0] == 404, 'Unknown download identifier is rejected')
        expect(client.request('/mcp', 'POST', b'{}', {'Content-Type': 'application/json'})[0] == 401,
               'The named route exemption lets MCP reject an unauthenticated POST')
        expect(client.request('/mcp', 'POST', b'{}',
                              {'Content-Type': 'application/json', 'Authorization': 'Bearer invalid'})[0] == 401,
               'MCP rejects an invalid bearer token after the named route CSRF exemption')

        def rpc(method, args=None, bearer=allowed, status=200):
            message = {'jsonrpc': '2.0', 'id': 1, 'method': method}
            if args is not None:
                message['params'] = {'name': 'get_folder_size', 'arguments': args}
            result = client.request('/mcp', 'POST', json.dumps(message).encode(),
                                    {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + bearer,
                                     'Accept': 'application/json, text/event-stream',
                                     'MCP-Protocol-Version': '2025-11-25'})
            expect(result[0] == status, f'MCP {method} returns HTTP {status}')
            envelope = json.loads(result[2])
            return envelope.get('result', envelope)

        definitions = rpc('tools/list')['tools']
        expect([tool['name'] for tool in definitions] == ['get_folder_size'], 'Scoped MCP tool is advertised')
        expect(definitions[0]['inputSchema']['additionalProperties'] is False, 'MCP advertises the bounded input schema')
        result = rpc('tools/call', {'folder': 'reports'})
        expect(result['isError'] is False and json.loads(result['content'][0]['text']) == {'folder': 'reports', 'bytes': 14},
               'MCP tool counts nested application files and excludes symlinks')
        expect(result['structuredContent'] == {'folder': 'reports', 'bytes': 14}, 'MCP also returns structured content')
        expect(rpc('tools/call', {'folder': '../'})['error']['code'] == -32602, 'MCP validates the folder enum')
        expect(rpc('tools/call', {'folder': 'reports', 'path': '/tmp'})['error']['code'] == -32602,
               'MCP rejects extra arguments against the closed input schema')
        expect(rpc('tools/list', bearer=denied)['tools'] == [], 'MCP hides tools outside token scopes')
        expect(rpc('tools/call', {'folder': 'reports'}, bearer=denied, status=403)['error']['code'] == -32001,
               'MCP refuses direct calls outside token scopes')


def test_alexa(root):
    copy_examples('install.md', root)
    run([*COMPOSER, 'require', 'naf/alexa:^0.1', '--no-interaction', '--prefer-dist'], root)
    copy_examples('alexa.md', root)
    environment = fragment('alexa.md', 'Set these application environment values', 'ini')
    (root / '.env').write_text('APP_ENV=test\n' + environment)
    registration = fragment('alexa.md', "Add this registration in the application's root `bootstrap.php`")
    (root / 'app/alexa.php').write_text('<?php\n\n' + registration)
    bootstrap_include(root, 'app/alexa.php')
    run([*COMPOSER, 'dump-autoload', '--no-interaction'], root)
    setup = run([*PHP, 'vendor/bin/naf', 'alexa:setup', '--migrate'], root)
    plain = re.sub(r'\x1b\[[0-9;]*m', '', setup)
    client_id = re.search(r'client_id: ([A-Za-z0-9_-]+)', plain)
    secret = re.search(r'shown once\): ([A-Za-z0-9_-]+)', plain)
    expect(bool(client_id and secret), 'Alexa setup prints a service client and one-time secret')
    repeated = run([*PHP, 'vendor/bin/naf', 'alexa:setup'], root)
    expect('Existing registration retained.' in repeated and 'shown once' not in repeated,
           'Alexa setup reuses its client without exposing or rotating the secret')
    doctor = run([*PHP, 'vendor/bin/naf', 'alexa:doctor', '--server-only'], root)
    expect('OK protocol routes' in doctor and 'OK tools and account-linking scopes' in doctor,
           'Alexa doctor validates the documented host and tool')
    resource = 'https://tools.example.com/mcp'
    basic = 'Basic ' + base64.b64encode((client_id[1] + ':' + secret[1]).encode()).decode()
    with server(root) as client:
        for path in ('/.well-known/oauth-protected-resource', '/.well-known/oauth-protected-resource/mcp'):
            result = client.request(path)
            metadata = json.loads(result[2])
            expect(result[0] == 200 and metadata['resource'] == resource,
                   'Alexa exposes canonical protected-resource metadata')
        result = client.request('/.well-known/oauth-authorization-server')
        metadata = json.loads(result[2])
        expect(result[0] == 200 and metadata['code_challenge_methods_supported'] == ['S256']
               and 'client_credentials' in metadata['grant_types_supported'],
               'OAuth-only discovery works without signing keys')
        fields = {'grant_type': 'client_credentials', 'scope': 'mcp:service', 'resource': resource}
        result = client.request('/oauth/token', 'POST', urllib.parse.urlencode(fields).encode(),
                                {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': basic})
        credentials = json.loads(result[2])
        expect(result[0] == 200 and 'refresh_token' not in credentials,
               'Alexa service client obtains a token without a refresh token')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                   'Authorization': 'Bearer ' + credentials['access_token'], 'MCP-Protocol-Version': '2025-11-25'}

        def rpc(message, expected=200):
            result = client.request('/mcp', 'POST', json.dumps(message).encode(), headers)
            expect(result[0] == expected, f'Alexa {message["method"]} returns HTTP {expected}')
            return result

        unauthenticated = client.request('/mcp', 'POST', b'{}', {'Content-Type': 'application/json'})
        expect(unauthenticated[0] == 401 and 'WWW-Authenticate' not in unauthenticated[1],
               'Alexa rejects missing credentials without WWW-Authenticate')
        result = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                      'params': {'protocolVersion': '2025-11-25', 'capabilities': {},
                                 'clientInfo': {'name': 'Example test', 'version': '1.0'}}})
        expect(json.loads(result[2])['result']['protocolVersion'] == '2025-11-25', 'Alexa negotiates the MCP version')
        expect(rpc({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, 202)[2] == '',
               'Alexa accepts the initialized notification with an empty response')
        result = rpc({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        expect([tool['name'] for tool in json.loads(result[2])['result']['tools']] == ['service_status'],
               'Alexa discovers the documented public tool')
        call = {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                'params': {'name': 'service_status', 'arguments': {}}}
        result = json.loads(rpc(call)[2])['result']
        expect(result['structuredContent'] == {'status': 'available'}
               and json.loads(result['content'][0]['text']) == {'status': 'available'},
               'Alexa service token calls the public tool with structured and text results')
        get = client.request('/mcp', headers=headers)
        expect(get[0] == 405 and get[1]['Allow'] == 'POST', 'Stateless Alexa transport has no persistent GET stream')
        config = root / 'app/config.php'
        config.write_text(config.read_text().replace("'streaming' => false", "'streaming' => true"))
        result = rpc(call)
        event = re.search(r'^data: (.+)$', result[2], re.M)
        expect('text/event-stream' in result[1]['Content-Type'] and event
               and json.loads(event[1])['result']['structuredContent'] == {'status': 'available'},
               'Enabling the documented setting switches Alexa responses to SSE')
        revoked = client.request('/oauth/revoke', 'POST',
                                 urllib.parse.urlencode({'token': credentials['access_token']}).encode(),
                                 {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': basic})
        expect(revoked[0] == 200, 'Alexa service token can be revoked')
        rpc(call, 401)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--starter', type=Path, help='Reuse installed starter dependencies; source is read-only')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='naf-docs-examples-') as tmp:
        root = Path(tmp)
        starter = root / 'starter'
        if args.starter:
            starter.mkdir()
            for name in ['composer.json', 'composer.lock']:
                shutil.copy2(args.starter / name, starter / name)
            shutil.copytree(args.starter / 'vendor', starter / 'vendor')
        else:
            run([*COMPOSER, 'create-project', 'naf/app', str(starter), '--no-interaction', '--prefer-dist'], root)
            with server(starter) as client:
                test_starter(client)
            print('PASS untouched published starter', flush=True)
            run([*COMPOSER, 'require', 'naf/auth', 'naf/orm', 'naf/mail', '--no-interaction', '--prefer-dist'], starter)
        if args.starter:
            # Reused older starters need the same upgrade documented in the installation guide.
            run([*COMPOSER, 'require', 'naf/framework:^0.2.2', 'naf/form:^0.2.1',
                 '--with-all-dependencies', '--no-interaction', '--prefer-dist'], starter)
        for feature in ('first-app', 'contact', 'login', 'orm'):
            fixture = root / feature
            shutil.copytree(starter, fixture)
            copy_examples('first-app.md', fixture)
            if feature == 'contact':
                copy_examples('recipes/contact-form.md', fixture)
            elif feature == 'login':
                copy_examples('auth.md', fixture)
                copy_examples('recipes/login-form.md', fixture)
                expect('Demo account ready.' in run([*PHP, 'bin/seed-demo.php'], fixture), 'Seed account')
            elif feature == 'orm':
                copy_examples('orm.md', fixture)
                for _ in range(2):
                    expect(run([*PHP, 'bin/products-demo.php'], fixture).strip() == 'NAF for Beginners', 'ORM save/find is repeatable')
            elif feature == 'first-app':
                # The tutorial replaces bootstrap/routes before removing the starter examples.
                for name in ('app/Controllers/WebsiteController.php', 'app/Service/QuoteService.php',
                             'app/views/welcome.phtml', 'app/views/contact.phtml', 'app/Jobs/SendMailJob.php'):
                    (fixture / name).unlink()
                for name in ('app/views/partials/contact-form.phtml', 'public/js/demo.js'):
                    (fixture / name).unlink(missing_ok=True)
            run([*COMPOSER, 'dump-autoload', '--no-interaction'], fixture)
            with server(fixture) as client:
                test_first(client)
                if feature == 'contact': test_contact(fixture, client)
                if feature == 'login': test_login(fixture, client)
            print(f'PASS {feature}', flush=True)
        flow = root / 'flow'
        shutil.copytree(starter, flow)
        run([*COMPOSER, 'require', 'naf/flow:^0.1', '--with-all-dependencies',
             '--no-interaction', '--prefer-dist'], flow)
        copy_examples('flow.md', flow)
        route = re.search(r'Add this route to the existing `app/routes.php`:\n\n```php-inline\n(.*?)^```',
                          (PAGES / 'flow.md').read_text(), re.M | re.S)
        if not route:
            raise RuntimeError('Flow route example is missing')
        (flow / 'app/routes.php').write_text('<?php\n\n' + route.group(1))
        with server(flow, 'router.php') as client:
            test_flow(flow, client)
        print('PASS Flow components and fragments', flush=True)
        integrations = root / 'integrations'
        shutil.copytree(starter, integrations)
        run([*COMPOSER, 'require', 'naf/client', 'naf/queue', 'naf/schedule', 'naf/mcp',
             '--with-all-dependencies', '--no-interaction', '--prefer-dist'], integrations)
        run([*COMPOSER, 'require', '--dev', 'phpunit/phpunit:^12.1',
             '--no-interaction', '--prefer-dist'], integrations)
        test_integrations(integrations)
        print('PASS service/HTTP tests, downloads, queue retry, schedule, HTTP fake and MCP scopes', flush=True)
        alexa = root / 'alexa'
        alexa.mkdir()
        test_alexa(alexa)
        print('PASS Alexa setup, doctor, OAuth discovery, service token, JSON/SSE tools and revocation', flush=True)
        core = root / 'core'
        core.mkdir()
        copy_examples('install.md', core)
        run([*COMPOSER, 'install', '--no-interaction', '--prefer-dist'], core)
        with server(core) as client:
            result = client.request('/')
            expect(result[0] == 200 and json.loads(result[2]) == {'ok': True}, 'Core-only install')
        print('PASS core-only install', flush=True)
        for scenario, test in (('small-website', test_small_website), ('simple-json-api', test_simple_api)):
            fixture = root / scenario
            fixture.mkdir()
            copy_examples(f'recipes/{scenario}.md', fixture)
            run([*COMPOSER, 'install', '--no-interaction', '--prefer-dist'], fixture)
            run([*COMPOSER, 'validate', '--strict'], fixture)
            packages = json.loads(run([*COMPOSER, 'show', '--format=json'], fixture))['installed']
            installed = {package['name'] for package in packages if package['name'].startswith('naf/')}
            expected = {'naf/framework', 'naf/view'} if scenario == 'small-website' else {'naf/framework'}
            expect(installed == expected, 'Scenario installs only its documented NAF packages')
            test(fixture)
            print(f'PASS {scenario}', flush=True)
        run([*COMPOSER, 'require', 'naf/database:^0.2.4', 'naf/cli:^0.2',
             '--no-interaction', '--prefer-dist'], core)
        copy_examples('recipes/json-api.md', core)
        run([*COMPOSER, 'dump-autoload', '--no-interaction'], core)
        expect('1 migration(s) successfully executed.' in run([*PHP, 'vendor/bin/naf', 'db:migrate', 'up'], core),
               'API schema setup uses the database migration command')
        test_api(core)
        print('PASS JSON API', flush=True)
    print(f'PASS {checks} checks against copied documentation examples')


if __name__ == '__main__':
    main()
