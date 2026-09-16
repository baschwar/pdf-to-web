'use strict';

const sanitizeHtml = require('sanitize-html');
const converter = require('wp-block-to-html');

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function canonicalName(serializedName) {
  return serializedName.includes('/') ? serializedName : `core/${serializedName}`;
}

function parseGutenbergMarkup(markup) {
  const comment = /<!--\s*(\/?)wp:([a-z0-9_-]+(?:\/[a-z0-9_-]+)?)([\s\S]*?)-->/gi;
  const roots = [];
  const stack = [];
  let match;

  while ((match = comment.exec(markup)) !== null) {
    const closing = match[1] === '/';
    const blockName = canonicalName(match[2]);
    let serializedAttributes = match[3].trim();
    const selfClosing = serializedAttributes.endsWith('/');
    if (selfClosing) serializedAttributes = serializedAttributes.slice(0, -1).trim();
    if (closing) {
      const entry = stack.pop();
      if (!entry || entry.block.blockName !== blockName) {
        throw new Error(`Mismatched Gutenberg closing block: ${blockName}`);
      }
      entry.block.innerHTML = markup.slice(entry.contentStart, match.index);
      entry.block.innerContent = [entry.block.innerHTML];
      continue;
    }

    let attrs = {};
    if (serializedAttributes) {
      try {
        attrs = JSON.parse(serializedAttributes);
      } catch (error) {
        throw new Error(`Invalid attributes for ${blockName}: ${error.message}`);
      }
    }
    const block = { blockName, attrs, innerBlocks: [], innerContent: [], innerHTML: '' };
    const siblings = stack.length ? stack[stack.length - 1].block.innerBlocks : roots;
    siblings.push(block);
    if (!selfClosing) stack.push({ block, contentStart: comment.lastIndex });
  }
  if (stack.length) throw new Error(`Unclosed Gutenberg block: ${stack.at(-1).block.blockName}`);
  return roots;
}

function renderNested(block, options) {
  return String(converter.convertBlocks(block.innerBlocks || [], options));
}

converter.registerBlockHandler('core/table', {
  transform(block) {
    return block.innerHTML || block.innerContent.join('');
  }
});

converter.registerBlockHandler('wsuwp/hero', {
  transform(block) {
    const attrs = block.attrs || {};
    const headingTag = /^h[1-6]$/.test(attrs.headingTag) ? attrs.headingTag : 'h1';
    const classes = ['wsu-preview-hero', attrs.className].filter(Boolean).join(' ');
    const image = attrs.imageSrc
      ? `<img src="${escapeHtml(attrs.imageSrc)}" alt="">`
      : '';
    const caption = attrs.caption ? `<p class="wsu-preview-hero-caption">${escapeHtml(attrs.caption)}</p>` : '';
    return `<section class="${escapeHtml(classes)}" data-background-type="${escapeHtml(attrs.backgroundType)}">${image}<${headingTag}>${escapeHtml(attrs.title)}</${headingTag}>${caption}</section>`;
  }
});

converter.registerBlockHandler('wsuwp/section', {
  transform(block, options) {
    const attrs = block.attrs || {};
    const classes = ['wsu-preview-section', attrs.className].filter(Boolean).join(' ');
    const id = attrs.id ? ` id="${escapeHtml(attrs.id)}"` : '';
    return `<section${id} class="${escapeHtml(classes)}">${renderNested(block, options)}</section>`;
  }
});

function registerUnsupportedHandlers(blocks, unsupported) {
  for (const block of blocks) {
    if (block.blockName && !converter.hasBlockHandler(block.blockName)) {
      const blockName = block.blockName;
      unsupported.add(blockName);
      converter.registerBlockHandler(blockName, {
        transform() {
          return `<div class="unsupported-block" data-block-name="${escapeHtml(blockName)}"><strong>WordPress block: ${escapeHtml(blockName)}</strong><br>Preview handler not implemented</div>`;
        }
      });
    }
    registerUnsupportedHandlers(block.innerBlocks || [], unsupported);
  }
}

function sanitizePreview(fragment) {
  return sanitizeHtml(fragment, {
    allowedTags: [
      'a', 'blockquote', 'br', 'caption', 'code', 'div', 'em', 'figcaption',
      'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'li', 'ol',
      'p', 'pre', 'section', 'span', 'strong', 'table', 'tbody', 'td', 'tfoot',
      'th', 'thead', 'tr', 'ul'
    ],
    allowedAttributes: {
      '*': ['class', 'id', 'data-*'],
      a: ['href', 'title'],
      img: ['src', 'alt', 'width', 'height', 'loading'],
      td: ['colspan', 'rowspan'],
      th: ['colspan', 'rowspan', 'scope']
    },
    allowedSchemes: ['http', 'https', 'mailto', 'tel'],
    allowedSchemesByTag: { img: ['http', 'https', 'data'] },
    allowProtocolRelative: false
  });
}

function convert(markup) {
  const blocks = parseGutenbergMarkup(markup);
  const unsupported = new Set();
  registerUnsupportedHandlers(blocks, unsupported);
  const html = converter.convertBlocks(blocks, {
    cssFramework: 'none',
    contentHandling: 'rendered'
  });
  return {
    html: sanitizePreview(String(html)),
    blockTypes: [...new Set(blocks.flatMap(function walk(block) {
      return [block.blockName, ...(block.innerBlocks || []).flatMap(walk)];
    }))].filter(Boolean),
    unsupportedBlocks: [...unsupported].sort()
  };
}

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const payload = JSON.parse(input);
    if (typeof payload.markup !== 'string') throw new Error('Gutenberg markup is required');
    process.stdout.write(`${JSON.stringify(convert(payload.markup))}\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
});
