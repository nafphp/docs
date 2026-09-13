#!/usr/bin/env python3
"""Exercise the actual file-titled Markdown examples against published Composer packages.

No example PHP is duplicated here. Each fixture copies the documented files, then tests
observable behavior through a real PHP HTTP server. Servers and fixtures are cleaned up.
"""
import argparse
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
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

PAGES = Path(__file__).resolve().parent.parent / 'pages'
BLOCKS = re.compile(r'^```\w+ title="([^"]+)"\n(.*?)^```\s*$', re.M | re.S)
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
    (root / 'storage/mail').mkdir(parents=True, exist_ok=True)


def expect(condition, message):
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1


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
def server(root):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryFile(mode='w+') as log:
        process = subprocess.Popen([*PHP, '-S', f'127.0.0.1:{port}', '-t', str(root / 'public')],
                                   cwd=root, stdout=log, stderr=log)
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
        expect(json.loads(client.request('/api/articles')[2]) == {'data': []}, 'API starts empty')
        request = lambda body, path='/api/articles': client.request(path, 'POST', body.encode(), {'Content-Type': 'application/json'})
        for body, status in [('{', 400), ('[]', 422), ('null', 422), ('{}', 422), ('{"title":[],"body":"ok"}', 422)]:
            result = request(body)
            expect(result[0] == status and 'error' in json.loads(result[2]), f'API rejects {body}')
        expect(client.form('/api/articles', {'title': 'a', 'body': 'b'})[0] == 415, 'API rejects form media type')
        expect(request('{}', '/api/articles?title=a&body=b')[0] == 422, 'Query does not fill missing body fields')
        saved = request('{"title":"First article","body":"Hello from NAF."}')
        expect(saved[0] == 201 and json.loads(saved[2])['data']['title'] == 'First article', 'API saves article')
        location = saved[1]['Location']
        expect(json.loads(client.request(location)[2])['data']['body'] == 'Hello from NAF.', 'API reads article')
        unknown = client.request('/unknown')
        expect(unknown[0] == 404 and 'error' in json.loads(unknown[2]), 'Unknown API route returns JSON')
    with server(root) as client:
        expect(client.request(location)[0] == 200, 'Article survives a server restart')
        deleted = client.request(location, 'DELETE')
        expect(deleted[0] == 204 and deleted[2] == '', 'DELETE has an empty 204 body')
        expect(client.request(location)[0] == 404, 'Deleted article is missing')
        expect(client.request(location, 'DELETE')[0] == 404, 'Deleting missing article returns 404')
        # A real storage failure must still produce a sanitized JSON error.
        with sqlite3.connect(root / 'storage/articles.sqlite') as database:
            database.execute('DROP TABLE articles')
        failure = client.request('/api/articles')
        expect(failure[0] == 500 and json.loads(failure[2]) == {'error': 'Internal server error'}, 'Unexpected API exception sanitized')


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
            run([*COMPOSER, 'dump-autoload', '--no-interaction'], fixture)
            with server(fixture) as client:
                test_first(client)
                if feature == 'contact': test_contact(fixture, client)
                if feature == 'login': test_login(fixture, client)
            print(f'PASS {feature}', flush=True)
        core = root / 'core'
        core.mkdir()
        copy_examples('install.md', core)
        run([*COMPOSER, 'install', '--no-interaction', '--prefer-dist'], core)
        with server(core) as client:
            result = client.request('/')
            expect(result[0] == 200 and json.loads(result[2]) == {'ok': True}, 'Core-only install')
        print('PASS core-only install', flush=True)
        copy_examples('recipes/json-api.md', core)
        expect('Articles table ready.' in run([*PHP, 'bin/create-articles.php'], core), 'API schema setup')
        test_api(core)
        print('PASS JSON API', flush=True)
    print(f'PASS {checks} checks against copied documentation examples')


if __name__ == '__main__':
    main()
