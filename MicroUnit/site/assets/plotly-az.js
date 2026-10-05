/* plotly-az.js — Azerbaijani locale for Plotly's own toolbar and number/date formats.
   This file is a translation table (English keys by design) and is the only place where Plotly's
   built-in English strings appear; site.js sets config.locale = 'az' for every chart. */
(function () {
  'use strict';
  if (!window.Plotly || !window.Plotly.register) return;
  window.Plotly.register({
    moduleType: 'locale',
    name: 'az',
    dictionary: {
      'Autoscale': 'Avtomatik miqyas',
      'Box Select': 'Düzbucaqlı ilə seç',
      'Click to enter Plot title': 'Qrafikin başlığını yazın',
      'Click to enter X axis title': 'X oxunun başlığını yazın',
      'Click to enter Y axis title': 'Y oxunun başlığını yazın',
      'Compare data on hover': 'Üzərinə gələndə dəyərləri müqayisə et',
      'Double-click on legend to isolate one trace': 'Bir sıranı ayırmaq üçün legendə iki dəfə klikləyin',
      'Double-click to zoom back out': 'Geri qayıtmaq üçün iki dəfə klikləyin',
      'Download plot': 'Qrafiki endir',
      'Download plot as a png': 'Qrafiki PNG kimi endir',
      'Lasso Select': 'Sərbəst seçim',
      'Orbital rotation': 'Orbital fırlanma',
      'Pan': 'Sürüşdür',
      'Produced with Plotly.js': 'Plotly.js ilə hazırlanıb',
      'Reset': 'Sıfırla',
      'Reset axes': 'Oxları sıfırla',
      'Reset camera to default': 'Kameranı sıfırla',
      'Reset view': 'Görünüşü sıfırla',
      'Show closest data on hover': 'Üzərinə gələndə ən yaxın dəyəri göstər',
      'Snapshot succeeded': 'Şəkil hazırdır',
      'Sorry, there was a problem downloading your snapshot!': 'Şəkli endirmək alınmadı',
      'Taking snapshot - this may take a few seconds': 'Şəkil hazırlanır — bir neçə saniyə çəkə bilər',
      'Toggle Spike Lines': 'Köməkçi xətləri göstər/gizlət',
      'Toggle show closest data on hover': 'Ən yaxın dəyəri göstər/gizlət',
      'Turntable rotation': 'Fırlanan masa',
      'Zoom': 'Böyüt',
      'Zoom in': 'Yaxınlaşdır',
      'Zoom out': 'Uzaqlaşdır'
    },
    format: {
      days: ['Bazar', 'Bazar ertəsi', 'Çərşənbə axşamı', 'Çərşənbə', 'Cümə axşamı', 'Cümə', 'Şənbə'],
      shortDays: ['B.', 'B.e.', 'Ç.a.', 'Ç.', 'C.a.', 'C.', 'Ş.'],
      months: ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'İyun', 'İyul', 'Avqust', 'Sentyabr', 'Oktyabr',
               'Noyabr', 'Dekabr'],
      shortMonths: ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'İyn', 'İyl', 'Avq', 'Sen', 'Okt', 'Noy', 'Dek'],
      date: '%d.%m.%Y',
      decimal: ',',
      thousands: ' '
    }
  });
})();
