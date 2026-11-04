const url = document.currentScript.dataset.url
const siteId = document.currentScript.dataset.siteId

var _paq = window._paq = window._paq || [];
_paq.push(['trackPageView']);
_paq.push(['enableLinkTracking']);
(function() {
    _paq.push(['setTrackerUrl', url+'piwik.php']);
    _paq.push(['setSiteId', siteId]);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=url+'piwik.js'; s.parentNode.insertBefore(g,s);
})();
