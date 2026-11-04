(function () {
  'use strict';
  const epoch = Date.UTC(1998, 5, 1);
  const dayMs = 86400000;
  const calendar = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit'
  });

  function update() {
    const parts = calendar.formatToParts(new Date());
    const get = type => Number(parts.find(part => part.type === type).value);
    const today = Math.max(epoch, Date.UTC(get('year'), get('month') - 1, get('day')));
    const date = new Date(today);
    const months = (date.getUTCFullYear() - 1998) * 12 + date.getUTCMonth() - 5;
    const values = {
      version: Math.floor(months / 120) + '.' + (months % 120 + 1) + '.' + date.getUTCDate(),
      days: Math.floor((today - epoch) / dayMs).toLocaleString('en-US') + ' 天',
      months: months.toLocaleString('en-US') + ' 个月',
      years: Math.floor(months / 12).toLocaleString('en-US') + ' 年'
    };
    document.querySelectorAll('[data-zisai-lifecycle]').forEach(root => {
      Object.entries(values).forEach(([key, value]) => {
        root.querySelector('[data-zisai-' + key + ']').textContent = value;
      });
    });
  }

  update();
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) update();
  });
  setInterval(update, 60000);
})();
