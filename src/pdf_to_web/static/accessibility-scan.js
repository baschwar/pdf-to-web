'use strict';
(() => {
  const start = async () => {
    const frame = document.getElementById('axe-preview');
    const status = document.getElementById('axe-status');
    const output = document.getElementById('axe-results');
    if (!frame) return;
    try {
      if (frame.contentDocument?.readyState !== 'complete') {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('The HTML preview did not load.')), 15000);
          frame.addEventListener('load', () => { clearTimeout(timer); resolve(); }, {once: true});
        });
      }
      const preview = frame.contentDocument;
      if (!preview?.querySelector('main')) throw new Error('The HTML preview is unavailable.');
      const engine = frame.contentWindow.axe;
      if (!engine) throw new Error('The local axe-core engine is unavailable.');
      const results = await engine.run(preview, {
        runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']},
        iframes: false
      });
      const add = (parent, tag, text) => {
        const element = document.createElement(tag);
        element.textContent = text;
        parent.append(element);
        return element;
      };
      const resultGroups = [['violations', 'Detected issues'], ['incomplete', 'Needs human review'], ['passes', 'Passed'], ['inapplicable', 'Not applicable']];
      output.replaceChildren();
      const summary = document.createElement('table');
      summary.className = 'result-table';
      add(summary, 'caption', 'Automated HTML check results');
      const head = document.createElement('thead'), headRow = document.createElement('tr');
      for (const label of ['Result', 'Rules', 'Affected elements']) add(headRow, 'th', label).scope = 'col';
      head.append(headRow); summary.append(head);
      const body = document.createElement('tbody');
      for (const [key, title] of resultGroups) {
        const row = document.createElement('tr');
        add(row, 'th', title).scope = 'row';
        add(row, 'td', String(results[key].length)).className = 'result-count';
        add(row, 'td', String(results[key].reduce((count, finding) => count + finding.nodes.length, 0))).className = 'result-count';
        body.append(row);
      }
      summary.append(body); output.append(summary);
      const viewRules = add(output, 'button', 'View tested rules');
      viewRules.type = 'button'; viewRules.className = 'secondary compact-action';
      viewRules.setAttribute('aria-haspopup', 'dialog');
      viewRules.setAttribute('aria-controls', 'axe-rules-dialog');
      const dialog = document.createElement('dialog');
      dialog.id = 'axe-rules-dialog'; dialog.className = 'axe-rules-dialog';
      dialog.setAttribute('aria-labelledby', 'axe-rules-title');
      const article = document.createElement('article'), header = document.createElement('header');
      add(header, 'h2', 'Tested HTML rules').id = 'axe-rules-title';
      const close = add(header, 'button', 'Close');
      close.type = 'button'; close.className = 'secondary compact-action'; close.autofocus = true;
      close.addEventListener('click', () => dialog.close());
      article.append(header);
      const content = document.createElement('div'); content.className = 'axe-rules-content';
      add(content, 'p', `axe-core ${results.testEngine.version} · WCAG 2.0, 2.1 and 2.2 A/AA rules selected for this scan. Results reflect the document when this screen opened.`);
      add(content, 'p', 'Passed counts rules with passing elements, not WCAG success criteria. Not applicable means no matching content was found. A rule can have different results for different elements. Automated checks do not replace human accessibility review.');
      const label = add(content, 'label', 'Show results'); label.htmlFor = 'axe-rules-filter';
      const filter = document.createElement('select'); filter.id = 'axe-rules-filter';
      add(filter, 'option', 'All results').value = 'all';
      for (const [key, title] of resultGroups) add(filter, 'option', `${title} (${results[key].length})`).value = key;
      filter.value = results.passes.length ? 'passes' : 'all'; content.append(filter);
      const count = add(content, 'p', ''); count.id = 'axe-rules-count'; count.setAttribute('role', 'status');
      const list = document.createElement('ul'); list.className = 'axe-rules-list'; content.append(list);
      const renderRules = () => {
        list.replaceChildren();
        for (const [key, title] of resultGroups) {
          if (filter.value !== 'all' && filter.value !== key) continue;
          for (const finding of [...results[key]].sort((a, b) => a.help.localeCompare(b.help))) {
            const item = document.createElement('li'); item.dataset.ruleId = finding.id; item.dataset.result = key;
            add(item, 'h3', finding.help);
            add(item, 'p', `${title} · ${finding.nodes.length} ${key === 'inapplicable' ? 'matching' : 'affected'} elements`);
            add(item, 'p', finding.description);
            const identity = add(item, 'p', 'Rule ID: '); add(identity, 'code', finding.id);
            const criteria = finding.tags.filter(tag => /^wcag\d{3,4}$/.test(tag)).map(tag => {
              const digits = tag.slice(4); return `${digits[0]}.${digits[1]}.${digits.slice(2)}`;
            });
            if (criteria.length) add(item, 'p', `WCAG criteria: ${criteria.join(', ')}`);
            if (finding.helpUrl.startsWith('https://')) {
              const help = add(item, 'a', 'Rule guidance'); help.href = finding.helpUrl;
              help.target = '_blank'; help.rel = 'noopener'; help.setAttribute('aria-label', `Rule guidance: ${finding.help}`);
            }
            list.append(item);
          }
        }
        count.textContent = list.children.length ? `${list.children.length} rule results shown.` : 'No rule results in this category.';
        content.scrollTop = 0;
      };
      filter.addEventListener('change', renderRules); renderRules();
      article.append(content); dialog.append(article); output.append(dialog);
      viewRules.addEventListener('click', () => dialog.showModal());
      dialog.addEventListener('close', () => viewRules.focus());
      for (const [key, title] of [['violations', 'Detected issues'], ['incomplete', 'Needs human review']]) {
        if (!results[key].length) continue;
        const section = document.createElement('section');
        add(section, 'h3', title);
        const tableWrap = document.createElement('div'); tableWrap.className = 'result-table-wrap';
        const table = document.createElement('table'); table.className = 'result-table';
        const tableHead = document.createElement('thead'), headers = document.createElement('tr');
        for (const label of ['Rule', 'Impact', 'Elements', 'Affected content']) add(headers, 'th', label).scope = 'col';
        tableHead.append(headers); table.append(tableHead);
        const findingsBody = document.createElement('tbody');
        for (const finding of results[key]) {
          const card = document.createElement('tr'); card.className = 'axe-finding';
          const rule = add(card, 'th', finding.help); rule.scope = 'row';
          add(rule, 'br', '');
          const help = add(rule, 'a', 'Rule guidance');
          if (finding.helpUrl.startsWith('https://')) { help.href = finding.helpUrl; help.target = '_blank'; help.rel = 'noopener'; }
          add(card, 'td', finding.impact || 'Review');
          add(card, 'td', String(finding.nodes.length)).className = 'result-count';
          const content = document.createElement('td'), details = document.createElement('details');
          add(details, 'summary', `View ${finding.nodes.length} affected elements`);
          const list = document.createElement('ul');
          for (const node of finding.nodes) {
            const row = document.createElement('li');
            const selector = node.target.find(value => typeof value === 'string');
            let element;
            try { element = selector ? preview.querySelector(selector) : null; } catch (_) { /* Show context when mapping is unavailable. */ }
            const block = element?.closest('[data-pdf-block-id]');
            if (block?.dataset.pdfBlockId) {
              const link = add(row, 'a', `Open block ${block.dataset.pdfBlockId}`);
              link.href = `/structure?return_to=accessibility&finding=${encodeURIComponent('axe:' + finding.id)}#block-${encodeURIComponent(block.dataset.pdfBlockId)}`;
              link.setAttribute('role', 'button');
              link.className = 'secondary compact-action';
            } else add(row, 'p', 'Document-level finding');
            add(row, 'p', node.failureSummary || finding.description);
            add(row, 'pre', node.html);
            list.append(row);
          }
          details.append(list); content.append(details); card.append(content); findingsBody.append(card);
        }
        table.append(findingsBody); tableWrap.append(table); section.append(tableWrap); output.append(section);
      }
      status.textContent = `Check complete · axe-core ${results.testEngine.version}. Results apply to this document when the screen opened.`;
      const completion = document.getElementById('accessibility-complete');
      if (completion) completion.hidden = !(completion.dataset.documentReady === 'true' && results.violations.length === 0 && results.incomplete.length === 0);

    } catch (error) {
      status.textContent = `Automated check unavailable: ${error.message} Document review remains available below.`;
    }
  };
  if (document.readyState === 'complete') start();
  else window.addEventListener('load', start, {once: true});
})();
