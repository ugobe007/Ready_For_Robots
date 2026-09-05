import React from 'react';

/**
 * Strip HTML tags for safe plain-text display (RSS snippets, news HTML, etc.).
 */
export function stripHtml(s) {
  return String(s || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

const HTTP_URL_IN_PLAIN_TEXT = /\bhttps?:\/\/[^\s<>"']+/gi;

/** Peel trailing punctuation so `new URL()` accepts the href. */
function extractHrefAndSuffix(token) {
  let t = token;
  let suffix = '';
  for (let i = 0; i < 24 && t.length > 8; i++) {
    try {
      const u = new URL(t);
      if (u.protocol !== 'http:' && u.protocol !== 'https:') throw new Error('not http');
      return { href: t, suffix };
    } catch {
      suffix = t.slice(-1) + suffix;
      t = t.slice(0, -1);
    }
  }
  return { href: token, suffix: '' };
}

function segmentsFromPlainText(text) {
  const t = String(text || '');
  const segments = [];
  let last = 0;
  let m;
  const re = new RegExp(HTTP_URL_IN_PLAIN_TEXT.source, 'gi');
  while ((m = re.exec(t)) !== null) {
    if (m.index > last) segments.push({ type: 'text', text: t.slice(last, m.index) });
    const full = m[0];
    const { href, suffix } = extractHrefAndSuffix(full);
    segments.push({ type: 'link', href });
    if (suffix) segments.push({ type: 'text', text: suffix });
    last = m.index + full.length;
  }
  if (last < t.length) segments.push({ type: 'text', text: t.slice(last) });
  return segments;
}

const defaultLinkClass =
  'text-cyan-500 hover:text-cyan-300 underline underline-offset-2';

/**
 * Strip HTML, then render bare http(s) URLs as compact **Source** links (new tab).
 */
export function PlainTextWithSourceLinks({ text, className = '', linkClassName }) {
  const stripped = stripHtml(text);
  const segments = segmentsFromPlainText(stripped);
  const linkCls = linkClassName ?? defaultLinkClass;

  return (
    <span className={`${className} break-words [overflow-wrap:anywhere]`.trim()}>
      {segments.map((seg, i) =>
        seg.type === 'text' ? (
          <React.Fragment key={i}>{seg.text}</React.Fragment>
        ) : (
          <a
            key={i}
            href={seg.href}
            target="_blank"
            rel="noopener noreferrer"
            className={linkCls}
          >
            Source
          </a>
        ),
      )}
    </span>
  );
}
