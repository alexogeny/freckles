/**
 * alexogeny's firefox configuration
 *
 * ! please note that if you choose to use this, lots of stuff will break
 * ! namely: google meet, netflix, youtube, etc.
 * ! proceed with caution
 *
 * * personally I keep a separate browser just for google meet
 *
 * most of my commonly used sites seem to still work
 * (reddit, youtube, hacker news, google, stackoverflow)
 *
 * ! there's also some dangerous stuff in here, but as long as you're not the kind
 * ! of person to go actively looking for malware then it'll be fine
 *
 * recommended extensions:
 * - ublock origin
 *   - all fitlers on and updated
 * - localcdn
 * - multi account containers
 */

function config () {
  lockPref('browser.startup.homepage', 'https://home.alexogeny.dev');
  lockPref('browser.startup.homepage_override.mstone', 'ignore');
}
config()


function developer () {
  lockPref('view_source.editor.external', true);
  lockPref('view_source.editor.path', '/usr/bin/code');
}
developer()


function warnings () {
  lockPref('browser.aboutConfig.showWarning', false);
  lockPref('browser.showQuitWarning', false);
  lockPref('browser.tabs.warnOnClose', false);
  lockPref('browser.tabs.warnOnCloseOtherTabs', false);
  lockPref('browser.warnOnQuit', false);
}
warnings()


function networking () {
  /** esni: https://www.cloudflare.com/ssl/encrypted-sni/ */
  lockPref('browser.meta_refresh_when_inactive.disabled', true);
  lockPref('gfx.canvas.remote', false);
  lockPref('network.dns.disableIPv6', true);
  lockPref('network.dns.echconfig.enabled', true);
  lockPref('network.dns.use_https_rr_as_altsvc', true);
  lockPref('network.trr.mode', 2);
}
networking();


function behaviour () {
  lockPref('browser.download.panel.shown', true);
  lockPref('browser.formfill.enable', false);
  lockPref('browser.pagethumbnails.capturing_disabled', true);
  lockPref('browser.rights.3.shown', true);
  lockPref('browser.uitour.enabled', false);
  lockPref('browser.urlbar.trimURLs', false);
  lockPref('browser.zoom.full', false);
  lockPref('media.autoplay.enabled', false);
  lockPref('media.webspeech.synth.enabled', false);
  lockPref('narrate.enabled', false);
  lockPref('places.history.enabled', false);
  lockPref('trailhead.firstrun.didSeeAboutWelcome', true);
  lockPref('webgl.force-enabled', true);
}
behaviour();


function DOM () {
  lockPref('dom.battery.enabled', false);
  lockPref('dom.block_reload_from_resize_event_handler', true);
  lockPref('dom.delay.block_external_protocol_in_iframes.enabled', true);
  lockPref('dom.event.clipboardevents.enabled', false);
  lockPref('dom.event.contextmenu.enabled', false);
  lockPref('dom.gamepad.enabled', false);
  lockPref('dom.gamepad.extensions.enabled', false);
  lockPref('dom.push.enabled', false);
  lockPref('dom.security.https_only_mode_ever_enabled', true);
  lockPref('dom.security.https_only_mode.upgrade_local', true);
  lockPref('dom.security.https_only_mode', true);
  lockPref('dom.vibrator.enabled', false);
  lockPref('dom.vr.enabled', false);
  lockPref('dom.vr.oculus.enabled', false);
  lockPref('dom.webaudio.enabled', false);
}
DOM()


function extensions () {
  lockPref('browser.discovery.enabled', false);
  lockPref('extensions.blocklist.enabled', false);
  lockPref('extensions.pocket.enabled', false);
  lockPref('extensions.update.autoUpdateDefault', false);
  lockPref('xpinstall.signature.required', false);
}
extensions()


function studies () {
  lockPref('app.normandy.api_url', '');
  lockPref('app.normandy.enabled', false);
  lockPref('app.normandy.optoutstudies.enabled', false);
  lockPref('app.normandy.shieldLearnMoreUrl', '');
  lockPref('app.shield.optoutstudies.enabled', false);
  lockPref('messaging-system.rsexperimentloader.enabled', false);
}
studies();


function captivePortal () {
  lockPref('captivedetect.canonicalURL', '');
  lockPref('network.captive-portal-service.enabled', false);
  lockPref('network.connectivity-service.enabled', false);
}
captivePortal();


function caching () {
  lockPref('browser.cache.disk.parent_directory', '/run/user/1000/firefox');
  lockPref('browser.cache.memory.capacity', 512000);
}
caching()


function newTab () {
  lockPref('browser.newtab.preload', false);
  lockPref('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons', false);
  lockPref('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features', false);
  lockPref('browser.newtabpage.activity-stream.discoverystream.enabled', false);
  lockPref('browser.newtabpage.activity-stream.feeds.discoverystreamfeed', false);
  lockPref('browser.newtabpage.activity-stream.feeds.section.topstories', false);
  lockPref('browser.newtabpage.activity-stream.feeds.telemetry', false);
  lockPref('browser.newtabpage.activity-stream.feeds.topsites', false);
  lockPref('browser.newtabpage.activity-stream.section.highlights.includePocket', false);
  lockPref('browser.newtabpage.activity-stream.showSponsored', false);
  lockPref('browser.newtabpage.activity-stream.showSponsoredTopSites', false);
  lockPref('browser.newtabpage.activity-stream.telemetry', false);
}
newTab()


function search () {
  lockPref('browser.search.geoip.url', '');
  lockPref('browser.search.region', 'US');
  lockPref('browser.search.suggest.enabled', false);
  lockPref('browser.urlbar.merino.enabled', false);
  lockPref('browser.urlbar.merino.endpointURL', '');
}
search()


function session () {
  lockPref('browser.sessionstore.interval', 900000);
  lockPref('browser.sessionstore.max_tabs_undo', 3);
  lockPref('browser.sessionstore.privacy_level', 1);
  lockPref('browser.sessionstore.restore_on_demand', false);
  lockPref('browser.sessionstore.restore_tabs_lazily', false);
  lockPref('browser.sessionstore.resume_from_crash', false);
}
session()


function browserUpdates () {
  lockPref('app.update.auto', false);
  lockPref('app.update.enabled', false);
  lockPref('app.update.mode', 0);
  lockPref('app.update.service.enabled', false);
}
browserUpdates()


function defaultBrowser () {
  lockPref('browser.defaultbrowser.notificationbar', false);
  lockPref('browser.shell.checkDefaultBrowser', false);
  lockPref('browser.shell.skipDefaultBrowserCheck', true);
}
defaultBrowser()


function omnibar () {
  lockPref('browser.urlbar.speculativeConnect.enabled', false);
  lockPref('browser.urlbar.sponsoredTopSites', false);
  lockPref('browser.urlbar.suggest.engines', false);
  lockPref('browser.urlbar.suggest.history', false);
  lockPref('browser.urlbar.suggest.searches', false);
  lockPref('browser.urlbar.suggest.topsites', false);
}
omnibar();


function security () {
  lockPref('device.sensors.enabled', false);
  lockPref('devtools.remote.wifi.scan', false);
  lockPref('fission.autostart', true);
  lockPref('network.IDN_show_punycode', true);
  lockPref('plugins.enumerable_names', '');
  lockPref('security.insecure_connection_text.enabled', true);
}
security()


function geolocation () {
  lockPref('browser.region.network.url', '');
  lockPref('browser.region.update.enabled', false);
  lockPref('geo.enabled', false);
  lockPref('geo.provider.ms-windows-location', false);
  lockPref('geo.use_corelocation', false);
  lockPref('geo.use_gpsd', false);
  lockPref('geo.wifi.uri', '');
  lockPref('intl.accept_languages', 'en-US, en');
  lockPref('javascript.use_us_english_locale', true);
}
geolocation()


function mediaPlayback () {
  lockPref('media.eme.enabled', false);
  lockPref('media.gmp-widevinecdm.enabled', false);
  lockPref('media.gmp-widevinecdm.visible', false);
  lockPref('media.navigator.enabled', false);
  lockPref('media.videocontrols.picture-in-picture.video-toggle.enabled', false);
}
mediaPlayback()


function peerToPeer () {
  lockPref('media.peerconnection.enabled', false);
  lockPref('media.peerconnection.identity.enabled', false);
  lockPref('media.peerconnection.simulcast', false);
  lockPref('media.peerconnection.turn.disable', true);
  lockPref('media.peerconnection.use_document_iceservers', false);
  lockPref('media.peerconnection.video.enabled', false);
}
peerToPeer()


function prefetching () {
  lockPref('network.dns.disablePrefetch', true);
  lockPref('network.dns.offline-localhost', false);
  lockPref('network.predictor.enabled', false);
  lockPref('network.prefetch-next', false);
  lockPref('network.stricttransportsecurity.preloadlist', false);
}
prefetching()


function fingerPrinting () {
  lockPref('network.http.referer.sendRefererHeader', 1);
  lockPref('network.http.referer.trimmingPolicy', 1);
  lockPref('network.http.referer.XOriginPolicy', 1);
  lockPref('network.http.speculative-parallel-limit', 0);
  lockPref('privacy.donottrackheader.enabled', true);
  lockPref('privacy.resistFingerprinting', true);
  lockPref('privacy.trackingprotection.enabled', true);
}
fingerPrinting()


function telemetry () {
  lockPref('beacon.enabled', false);
  lockPref('breakpad.reportURL', '');
  lockPref('browser.send_pings.require_same_host', true);
  lockPref('browser.send_pings', false);
  lockPref('datareporting.healthreport.service.enabled', false);
  lockPref('datareporting.policy.dataSubmissionEnabled', false);
  lockPref('toolkit.crashreporter.enabled', false);
  lockPref('toolkit.telemetry.archive.enabled', false);
  lockPref('toolkit.telemetry.bhrPing.enabled', false);
  lockPref('toolkit.telemetry.enabled', false);
  lockPref('toolkit.telemetry.firstShutdownPing.enabled', false);
  lockPref('toolkit.telemetry.newProfilePing.enabled', false);
  lockPref('toolkit.telemetry.pioneer-new-studies-available', false);
  lockPref('toolkit.telemetry.server', '');
  lockPref('toolkit.telemetry.shutdownPingSender.enabled', false);
  lockPref('toolkit.telemetry.unified', false);
  lockPref('toolkit.telemetry.updatePing.enabled', false);
}
telemetry()


function safeBrowsing () {
  lockPref('browser.safebrowsing.enabled', false);
  lockPref('browser.safebrowsing.phishing.enabled', false);
  lockPref('browser.safebrowsing.malware.enabled', false);
  lockPref('browser.safebrowsing.downloads.enabled', false);
  lockPref('browser.safebrowsing.provider.google4.dataSharing.enabled', false);
  lockPref('browser.safebrowsing.provider.google4.dataSharing', '');
  lockPref('browser.safebrowsing.provider.google4.updateURL', '');
  lockPref('browser.safebrowsing.provider.google4.reportURL', '');
  lockPref('browser.safebrowsing.provider.google4.reportPhishMistakeURL', '');
  lockPref('browser.safebrowsing.provider.google4.reportMalwareMistakeURL', '');
  lockPref('browser.safebrowsing.provider.google4.lists', '');
  lockPref('browser.safebrowsing.provider.google4.gethashURL', '');
  lockPref('browser.safebrowsing.provider.google4.dataSharingURL', '');
  lockPref('browser.safebrowsing.provider.google4.advisoryURL', '');
  lockPref('browser.safebrowsing.provider.google4.advisoryName', '');
  lockPref('browser.safebrowsing.provider.google.updateURL', '');
  lockPref('browser.safebrowsing.provider.google.reportURL', '');
  lockPref('browser.safebrowsing.provider.google.reportPhishMistakeURL', '');
  lockPref('browser.safebrowsing.provider.google.reportMalwareMistakeURL', '');
  lockPref('browser.safebrowsing.provider.google.pver', '');
  lockPref('browser.safebrowsing.provider.google.lists', '');
  lockPref('browser.safebrowsing.provider.google.gethashURL', '');
  lockPref('browser.safebrowsing.provider.google.advisoryURL', '');
  lockPref('browser.safebrowsing.downloads.remote.url', '');
  lockPref('browser.safebrowsing.provider.mozilla.updateURL', '');
  lockPref('browser.safebrowsing.reportPhishURL', '');
  lockPref('browser.safebrowsing.provider.mozilla.gethashURL', '');
}
safeBrowsing();


function contentBlocking () {
  lockPref('browser.contentblocking.report.cookie.url', '');
  lockPref('browser.contentblocking.report.cryptominer.url', '');
  lockPref('browser.contentblocking.report.endpoint_url', '');
  lockPref('browser.contentblocking.report.fingerprinter.url', '');
  lockPref('browser.contentblocking.report.lockwise.how_it_works.url', '');
  lockPref('browser.contentblocking.report.manage_devices.url', '');
  lockPref('browser.contentblocking.report.mobile-android.url', '');
  lockPref('browser.contentblocking.report.mobile-ios.url', '');
  lockPref('browser.contentblocking.report.monitor.home_page_url', '');
  lockPref('browser.contentblocking.report.monitor.how_it_works.url', '');
  lockPref('browser.contentblocking.report.monitor.preferences_url', '');
  lockPref('browser.contentblocking.report.monitor.sign_in_url', '');
  lockPref('browser.contentblocking.report.monitor.url', '');
  lockPref('browser.contentblocking.report.proxy_extension.url', '');
  lockPref('browser.contentblocking.report.social.url', '');
  lockPref('browser.contentblocking.report.tracker.url', '');
  lockPref('browser.contentblocking.report.vpn-android.url', '');
  lockPref('browser.contentblocking.report.vpn-ios.url', '');
  lockPref('browser.contentblocking.report.vpn-promo.url', '');
  lockPref('browser.contentblocking.report.vpn.url', '');
  lockPref('browser.contentblocking.reportBreakage.url', '');
}
contentBlocking()
