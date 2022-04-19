/**
 * alexogeny's firefox configuration
 *
 * ! please note that if you choose to use this, lots of stuff will break
 * ! namely: google meet, netflix, etc.
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
 *
 * TODO: add more config settings. I know there are a heap more that I'm missing
 *       gonna leave this here until I've explored further
*/

/** set my homepage */
lockPref('browser.startup.homepage', 'https://home.alexogeny.dev');
lockPref('browser.startup.homepage_override.mstone', 'ignore');

/** open page source in vscode */
lockPref('view_source.editor.external', true);
lockPref('view_source.editor.path', '/usr/bin/code');

/** if I wanted a beta browser I would have downloaded a beta browser */
lockPref('app.normandy.enabled', false);
lockPref('app.normandy.optoutstudies.enabled', false);

/** give me back context menus */
lockPref('dom.event.contextmenu.enabled', false);

/** prevent clipboard spying */
lockPref('dom.event.clipboardevents.enabled', false);

/** stop people from reading plugin list */
lockPref('plugins.enumerable_names', '');

/** esni: https://www.cloudflare.com/ssl/encrypted-sni/ */
lockPref('network.security.esni.enabled', true);

/** don't recommend me things */
lockPref('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons', false);
lockPref('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features', false);
lockPref('browser.newtabpage.activity-stream.feeds.topsites', false);

/** et phone... home? */
lockPref('beacon.enabled', false);

/** move the cache into a ramdisk */
lockPref('browser.cache.disk.parent_directory', '/run/user/1000/firefox');
lockPref('browser.cache.memory.capacity', 512000);

/** hiding the download panel was stupid but I never used it anyway */
lockPref('browser.download.panel.shown', true);

/** use a password manager for filling forms */
lockPref('browser.formfill.enable', false);

/** this shits me on ios to no end */
lockPref('browser.meta_refresh_when_inactive.disabled', true);

/** new tab stuff is gross */
lockPref('browser.newtab.preload', false);
lockPref('browser.newtabpage.activity-stream.discoverystream.enabled', false);
lockPref('browser.newtabpage.activity-stream.feeds.discoverystreamfeed', false);
lockPref('browser.newtabpage.activity-stream.feeds.section.topstories', false);
lockPref('browser.newtabpage.activity-stream.feeds.telemetry', false);
lockPref('browser.newtabpage.activity-stream.section.highlights.includePocket', false);
lockPref('browser.newtabpage.activity-stream.showSponsored', false);
lockPref('browser.newtabpage.activity-stream.showSponsoredTopSites', false);
lockPref('browser.newtabpage.activity-stream.telemetry', false);

/** my care factor for AU search results is zero */
lockPref('browser.search.suggest.enabled', false);
lockPref('browser.search.region', 'US');
lockPref('browser.search.geoip.url', '');

/** prevent autoplay */
lockPref('media.autoplay.enabled', false);

/** do not collapse urls */
lockPref('browser.urlbar.trimURLs', false);

/** just no. */
lockPref('browser.send_pings.require_same_host', true);
lockPref('browser.send_pings', false);

/** make session store stuff a little less aggressive */
lockPref('browser.sessionstore.interval', 900000);
lockPref('browser.sessionstore.max_tabs_undo', 3);
lockPref('browser.sessionstore.privacy_level', 1);
lockPref('browser.sessionstore.resume_from_crash', false);

/** make restore more imperative */
lockPref('browser.sessionstore.restore_on_demand', false);
lockPref('browser.sessionstore.restore_tabs_lazily', false);

/** let me install any extension */
lockPref('xpinstall.signature.required', false);

/** do not autoupdate my extensions */
lockPref('extensions.update.autoUpdateDefault', false);

/** disable the updater service */
lockPref('app.update.enabled', false);
lockPref('app.update.auto', false);
lockPref('app.update.mode', 0);
lockPref('app.update.service.enabled', false);

/** just let me close the damn tab already */
lockPref('browser.showQuitWarning', false);
lockPref('browser.warnOnQuit', false);
lockPref('browser.tabs.warnOnClose', false);
lockPref('browser.tabs.warnOnCloseOtherTabs', false);

/** firefox should always be the default */
lockPref('browser.defaultbrowser.notificationbar', false);
lockPref('browser.shell.checkDefaultBrowser', false);
lockPref('browser.shell.skipDefaultBrowserCheck', true);

/** Don't do web stuff when I am typing into the url bar... pretty please? */
lockPref('browser.urlbar.speculativeConnect.enabled', false);
lockPref('browser.urlbar.sponsoredTopSites', false);
lockPref('browser.urlbar.suggest.engines', false);
lockPref('browser.urlbar.suggest.history', false);
lockPref('browser.urlbar.suggest.searches', false);
lockPref('browser.urlbar.suggest.topsites', false);

/** Instead of zooming the full page, just zoom the text. */
lockPref('browser.zoom.full', false);

/** Don't need this junk. */
lockPref('device.sensors.enabled', false);

/** Prevent devtools from doing any wifi scans. This sounds icky. */
lockPref('devtools.remote.wifi.scan', false);
lockPref('dom.block_reload_from_resize_event_handler', true);
lockPref('dom.delay.block_external_protocol_in_iframes.enabled', true);

/** I don't play gamepad enabled games in the browser. */
lockPref('dom.gamepad.enabled', false);
lockPref('dom.gamepad.extensions.enabled', false);

/** make all the things HTTPS. */
lockPref('dom.security.https_only_mode_ever_enabled', true);
lockPref('dom.security.https_only_mode.upgrade_local', true);
lockPref('dom.security.https_only_mode', true);

/** didn't know you could attach a vibrator to firefox */
lockPref('dom.vibrator.enabled', false);
lockPref('dom.vr.enabled', false);
lockPref('dom.vr.oculus.enabled', false);
lockPref('dom.webaudio.enabled', false);
lockPref('dom.battery.enabled', false);

/** blocklists are just more web requests I don't need */
lockPref('extensions.blocklist.enabled', false);

/** why use pocket when you can just use bookmarks */
lockPref('extensions.pocket.enabled', false);

/** containerise all websites a la Facebook conatiner */
lockPref('fission.autostart', true);

/** isn't this what address fields are for */
lockPref('geo.enabled', false);
lockPref('geo.provider.ms-windows-location', false);
lockPref('geo.wifi.uri', '');

/** might break r/place in 5 years but who cares */
lockPref('gfx.canvas.remote', false);

/** will break netflix, but don't use it anyways */
lockPref('media.eme.enabled', false);
lockPref('media.gmp-widevinecdm.enabled', false);
lockPref('media.gmp-widevinecdm.visible', false);
lockPref('media.navigator.enabled', false);

/**
 * ! this will break meet software; keep a backup browser
 */
lockPref('media.peerconnection.enabled', false);
lockPref('media.peerconnection.identity.enabled', false);
lockPref('media.peerconnection.simulcast', false);
lockPref('media.peerconnection.turn.disable', true);
lockPref('media.peerconnection.use_document_iceservers', false);
lockPref('media.peerconnection.video.enabled', false);

/** most annoying thing ever */
lockPref('media.videocontrols.picture-in-picture.video-toggle.enabled', false);

/** what even does this do */
lockPref('media.webspeech.synth.enabled', false);

/** dunno what this does either */
lockPref('messaging-system.rsexperimentloader.enabled', false);

/** disabled since I have a habit of not looking up malware */
lockPref('network.captive-portal-service.enabled', false);
lockPref('network.connectivity-service.enabled', false);

/** nobody uses ipv6 anyways, right */
lockPref('network.dns.disableIPv6', true);

/** prefetching is yuck */
lockPref('network.dns.disablePrefetch', true);
lockPref('network.dns.offline-localhost', false);
lockPref('network.predictor.enabled', false);
lockPref('network.prefetch-next', false);
lockPref('network.stricttransportsecurity.preloadlist', false);

/**
 * ! tighten up some http screws
 */
lockPref('network.http.referer.sendRefererHeader', 1);
lockPref('network.http.referer.trimmingPolicy', 1);
lockPref('network.http.referer.XOriginPolicy', 1);
lockPref('network.http.speculative-parallel-limit', 0);
lockPref('privacy.donottrackheader.enabled', true);
lockPref('privacy.resistFingerprinting', true);
lockPref('privacy.trackingprotection.enabled', true);

/** obviously */
lockPref('network.IDN_show_punycode', true);
lockPref('security.insecure_connection_text.enabled', true);

/** opinion: save a bookmark if you find an important page */
lockPref('places.history.enabled', false);

/** like the idea of telemetry but hate it in practice */
lockPref('toolkit.telemetry.enabled', false);
lockPref('toolkit.telemetry.archive.enabled', false);
lockPref('toolkit.telemetry.firstShutdownPing.enabled', false);
lockPref('toolkit.telemetry.newProfilePing.enabled', false);
lockPref('toolkit.telemetry.pioneer-new-studies-available', false);
lockPref('toolkit.telemetry.shutdownPingSender.enabled', false);
lockPref('toolkit.telemetry.updatePing.enabled', false);
lockPref('toolkit.telemetry.unified', false);
lockPref('toolkit.telemetry.bhrPing.enabled', false);
lockPref('toolkit.telemetry.server', '');
lockPref('breakpad.reportUrl', '');

/** don't save thumbnails of pages */
lockPref('browser.pagethumbnails.capturing_disabled', true);

/** get rid of that silly welcome screen */
lockPref('trailhead.firstrun.didSeeAboutWelcome', true);

/** I know my rights */
lockPref('browser.rights.3.shown', true);

/** disable health report */
lockPref('datareporting.healthreport.service.enabled', false);
lockPref('datareporting.policy.dataSubmissionEnabled', false);

/** disable crash reporting */
lockPref('toolkit.crashreporter.enabled', false);

/**
 * ! dangerous stuff here (but only if you search for malware)
 */
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

/** forced ui tours are lame */
lockPref('browser.uitour.enabled', false);

/** as if I want notifications from the browser */
lockPref('dom.push.enabled', false);

/** what exactly is to be narrated */
lockPref('narrate.enabled', false);

/** force enable webgl */
lockPref('webgl.force-enabled', true);
