"""Safe, read-only display of the shared export renderer's saved block markup."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from .exporters.html import render_block


class _PreviewMarkup(HTMLParser):
    tags = {'a', 'blockquote', 'br', 'caption', 'div', 'em', 'figcaption', 'figure',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'li', 'ol', 'p',
            'section', 'span', 'strong', 'sup', 'table', 'tbody', 'td', 'th', 'tr', 'ul'}
    void = {'br', 'hr', 'img'}
    attributes = {'id', 'aria-label', 'aria-labelledby'}
    per_tag = {'ol': {'start', 'type'}, 'td': {'colspan', 'rowspan'},
               'th': {'colspan', 'rowspan', 'scope'}, 'img': {'alt'}}

    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.ids = set()
        self.collecting = True
        self.feed(markup)
        self.reset()
        self.collecting = False
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        if tag not in self.tags:
            return
        attrs = dict(attributes)
        if self.collecting:
            if attrs.get('id'):
                self.ids.add(attrs['id'])
            return
        allowed = self.attributes | self.per_tag.get(tag, set())
        safe = {key: value for key, value in attrs.items() if key in allowed and value is not None}
        if tag == 'a':
            href = attrs.get('href', '')
            if href.startswith('#') and href[1:] in self.ids:
                # srcdoc inherits the embedding page's base URL. An explicit
                # same-document URL keeps note navigation inside this frame.
                safe['href'] = 'about:srcdoc' + href
            else:
                # Review links visually without navigating the app or loading
                # external pages. Recognized in-fragment note links stay usable.
                safe['aria-disabled'] = 'true'
                if re.match(r'^(https?|mailto|tel):', href, re.IGNORECASE):
                    safe['title'] = 'Link destination: ' + href
        if tag == 'img':
            src = attrs.get('src', '')
            if not src.startswith(('/api/preview/images/', '/api/image-drafts/asset?path=')):
                self.output.append('<p>Image unavailable in this saved-content preview.</p>')
                return
            safe['src'] = src
        attributes = ''.join(f' {key}="{html.escape(value, quote=True)}"' for key, value in safe.items())
        self.output.append(f'<{tag}{attributes}>')

    def handle_endtag(self, tag):
        if not self.collecting and tag in self.tags and tag not in self.void:
            self.output.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.collecting:
            self.output.append(html.escape(data))


def saved_block_preview(block, document):
    """Return an isolated preview document; neither input is changed."""
    markup = render_block(block, document=document)
    if not markup:
        markup = '<p>This block is omitted from exports.</p>'
    elif not str(block.get('content', '')).strip() and not block.get('runs') and not block.get('children'):
        markup = '<p>No saved text.</p>'
    safe = ''.join(_PreviewMarkup(markup).output)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
            'img-src \'self\'; style-src \'self\'; base-uri \'none\'; form-action \'none\'">'
            '<title>Saved content preview</title>'
            '<link rel="stylesheet" href="/static/block-preview.css">'
            '</head><body><main>' + safe + '</main></body></html>')
