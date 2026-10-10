#!/usr/bin/env python3
"""Capture the documentation's screenshots and console output from the documented examples.

The fixtures are built exactly like test_examples.py builds them: from the published
starter and packages, with the file-titled blocks copied from the pages. Playwright drives
the running applications; nothing is drawn or edited by hand. Images are written to
pages/assets/screenshots/ and console output to snippets/output/, which the pages include
with `--8<--`. Run this after releases that change a visible page or a command's output.

    pip install -r requirements-screenshots.txt
    python -m playwright install chromium
    python tools/capture_screenshots.py
"""
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_examples as ex  # noqa: E402  (shares fixtures, servers and Composer settings)

from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ASSETS = ex.PAGES / 'assets'
SHOTS = ASSETS / 'screenshots'
OUTPUT = ex.PAGES.parent / 'snippets' / 'output'
ANSI = re.compile(r'\x1b\[[0-9;]*m')


@contextmanager
def browser_page(playwright, width, height):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(viewport={'width': width, 'height': height},
                                device_scale_factor=2, color_scheme='light')
        yield page
    finally:
        browser.close()


def shot(page, name, selector=None):
    """Capture the viewport, or one element cropped to its box, as a compact WebP image."""
    png = (page.locator(selector).first.screenshot() if selector else page.screenshot())
    path = SHOTS / f'{name}.webp'
    with tempfile.NamedTemporaryFile(suffix='.png') as raw:
        raw.write(png)
        raw.flush()
        Image.open(raw.name).save(path, 'WEBP', quality=88, method=6)
    print(f'  wrote {path.relative_to(ex.PAGES.parent)}', flush=True)


def submit(page, selector='button[type="submit"]'):
    """Submit a form to the server, skipping the browser's own validation, and wait for the reply."""
    page.evaluate("document.querySelectorAll('form').forEach(form => form.noValidate = true)")
    with page.expect_navigation():
        page.click(selector)


def console(root, name, *arguments):
    text = ANSI.sub('', ex.run([*ex.PHP, 'vendor/bin/naf', *arguments], root))
    path = OUTPUT / f'{name}.txt'
    path.write_text('\n'.join(line.rstrip() for line in text.strip('\n').splitlines()) + '\n')
    print(f'  wrote {path.relative_to(ex.PAGES.parent)}', flush=True)


def first_app(starter, root):
    shutil.copytree(starter, root)
    ex.copy_examples('first-app.md', root)
    for name in ('app/Controllers/WebsiteController.php', 'app/Service/QuoteService.php',
                 'app/views/welcome.phtml', 'app/views/contact.phtml', 'app/Jobs/SendMailJob.php',
                 'app/views/partials/contact-form.phtml', 'public/js/demo.js'):
        (root / name).unlink(missing_ok=True)
    ex.run([*ex.COMPOSER, 'dump-autoload', '--no-interaction'], root)


def capture_starter(playwright, starter):
    with ex.server(starter) as client, browser_page(playwright, 1200, 760) as page:
        page.goto(client.base + '/')
        page.wait_for_load_state('networkidle')
        shot(page, 'starter-welcome')
        page.locator('#demos').scroll_into_view_if_needed()
        page.locator('form[data-demo="api"] button[type="submit"]').click()
        page.wait_for_timeout(800)
        shot(page, 'starter-demos', selector='#demos')


def capture_first_app(playwright, starter, tmp):
    root = tmp / 'first-app'
    first_app(starter, root)
    with ex.server(root) as client, browser_page(playwright, 640, 400) as page:
        page.goto(client.base + '/')
        shot(page, 'first-app-home', selector='body')
    return root


def capture_errors(playwright, first, tmp):
    # The diagnostic page prints file paths; a neutral, stable location keeps random
    # temporary directory names out of the image.
    root = Path('/tmp/my-app')
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(first, root)
    try:
        capture_error_pages(playwright, root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def capture_error_pages(playwright, root):
    routes = root / 'app/routes.php'
    routes.write_text(routes.read_text() + "\nroute()->add('GET', '/broken', static function () {\n"
                      "    throw new \\RuntimeException('Example failure in a controller.');\n}, 'broken');\n")
    for environment in ('dev', 'prod'):
        (root / '.env').write_text(f'APP_ENV={environment}\n')
        with ex.server(root, environment={'APP_ENV': environment}) as client, \
                browser_page(playwright, 1200, 700) as page:
            page.goto(client.base + '/broken')
            shot(page, f'error-page-{environment}')


def capture_contact(playwright, starter, tmp):
    root = tmp / 'contact'
    first_app(starter, root)
    ex.run([*ex.COMPOSER, 'require', 'naf/mail', '--no-interaction', '--prefer-dist'], root)
    ex.copy_examples('recipes/contact-form.md', root)
    ex.run([*ex.COMPOSER, 'dump-autoload', '--no-interaction'], root)
    with ex.server(root) as client, browser_page(playwright, 640, 400) as page:
        page.goto(client.base + '/contact')
        page.fill('#name', 'Ada')
        page.fill('#email', 'not-an-address')
        page.fill('#message', 'Too short')
        submit(page)
        shot(page, 'contact-form-errors', selector='body')
        page.fill('#email', 'ada@example.com')
        page.fill('#message', 'A message that is long enough.')
        submit(page)
        shot(page, 'contact-form-sent', selector='body')


def capture_small_website(playwright, tmp):
    root = tmp / 'small-website'
    root.mkdir()
    ex.copy_examples('recipes/small-website.md', root)
    ex.run([*ex.COMPOSER, 'install', '--no-interaction', '--prefer-dist'], root)
    with ex.server(root) as client, browser_page(playwright, 960, 600) as page:
        page.goto(client.base + '/?name=Ada')
        shot(page, 'small-website-home')


def capture_flow(playwright, starter, tmp):
    root = tmp / 'flow'
    shutil.copytree(starter, root)
    ex.run([*ex.COMPOSER, 'require', 'naf/flow:^0.1', '--with-all-dependencies',
            '--no-interaction', '--prefer-dist'], root)
    ex.copy_examples('flow.md', root)
    route = re.search(r'Add this route to the existing `app/routes.php`:\n\n```php-inline\n(.*?)^```',
                      (ex.PAGES / 'flow.md').read_text(), re.M | re.S)
    (root / 'app/routes.php').write_text('<?php\n\n' + route.group(1))
    with ex.server(root, 'router.php') as client:
        with browser_page(playwright, 640, 400) as page:
            page.goto(client.base + '/flow-example')
            page.wait_for_load_state('networkidle')
            page.locator('input').first.fill('view')
            page.wait_for_timeout(1200)
            shot(page, 'flow-search', selector='body')
        record_flow(playwright, client.base)


def record_flow(playwright, base):
    """A few seconds of typing, so readers see both fields and the results follow along."""
    with tempfile.TemporaryDirectory() as videos:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={'width': 640, 'height': 360}, color_scheme='light',
                                      record_video_dir=videos, record_video_size={'width': 640, 'height': 360})
        page = context.new_page()
        page.goto(base + '/flow-example')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(600)
        page.locator('input').first.press_sequentially('view', delay=260)
        page.wait_for_timeout(1200)
        page.locator('input').nth(1).fill('')
        page.locator('input').nth(1).press_sequentially('queue', delay=260)
        page.wait_for_timeout(1500)
        video = page.video.path()
        context.close()
        browser.close()
        target = SHOTS / 'flow-search.webm'
        shutil.copyfile(video, target)
        print(f'  wrote {target.relative_to(ex.PAGES.parent)}', flush=True)


def capture_console(first, tmp):
    root = tmp / 'console'
    shutil.copytree(first, root)
    ex.run([*ex.COMPOSER, 'require', 'naf/cli', '--with-all-dependencies', '--no-interaction', '--prefer-dist'], root)
    ex.copy_examples('console.md', root)
    command = ex.fragment('console.md', '## Register a command')
    (root / 'app/commands.php').write_text('<?php\n\n' + command)
    ex.bootstrap_include(root, 'app/commands.php')
    ex.run([*ex.COMPOSER, 'dump-autoload', '--no-interaction'], root)
    console(root, 'command-list', 'command:list')
    console(root, 'route-debug', 'route:debug')
    console(root, 'plugins-debug', 'plugins:debug')
    console(root, 'hello-say', 'hello:say', 'World')
    console(root, 'hello-help', 'hello:say', '--help')


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='naf-docs-screens-') as directory, sync_playwright() as playwright:
        tmp = Path(directory)
        starter = tmp / 'starter'
        ex.run([*ex.COMPOSER, 'create-project', 'naf/app', str(starter), '--no-interaction', '--prefer-dist'], tmp)
        print('Starter', flush=True)
        capture_starter(playwright, starter)
        print('First application and error pages', flush=True)
        first = capture_first_app(playwright, starter, tmp)
        capture_errors(playwright, first, tmp)
        print('Contact form', flush=True)
        capture_contact(playwright, starter, tmp)
        print('Small website', flush=True)
        capture_small_website(playwright, tmp)
        print('Flow', flush=True)
        capture_flow(playwright, starter, tmp)
        print('Console output', flush=True)
        capture_console(first, tmp)


if __name__ == '__main__':
    main()
