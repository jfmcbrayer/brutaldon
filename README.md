# Brutaldon

Note: If you are seeing this on Github, this repo is a mirror that may not be up-to-date. Please go to https://git.carcosa.net/jmcbray/brutaldon for the latest code.

Brutaldon is a [brutalist][0], [Web 1.0][0.5] web interface for [Mastodon][1] and [Pleroma][p]. It is not a Mastodon-compatible social networking server; rather, it is just a client, like the Android or iOS client for Mastodon you may already be using, but it runs in a web server, and is accessed through a web browser. It works great in text-mode browsers such as [Lynx][2], [w3m][3], or [elinks][4], and also in more heavy-weight graphical browsers, such as Firefox. It works completely without JavaScript, but if JavaScript is available and enabled, it will be used to unobtrusively enhance the user experience.

[0]:http://brutalistwebsites.com/
[0.5]: https://en.wikipedia.org/wiki/Web_2.0#%22Web_1.0%22
[1]: https://joinmastodon.org/
[2]: https://lynx.browser.org/
[3]: https://w3m.sourceforge.net/
[4]: http://elinks.or.cz/
[p]: https://pleroma.social/

There is a hosted instance at [brutaldon.online][hosted] which you can use to log in to any instance. However, you are also encouraged to run your own, either locally or on a public server. 

[hosted]: https://brutaldon.online/

Brutaldon is ready for day to day use, and is my main way of interacting with the fediverse. It is still missing some features you might want, like lists, filters, and editing your own profile.
Please see the issues tracker.

## Screenshots

People love screenshots, whatever the project, so here we are. These screenshots are relatively old.

<table>
 <tr>
   <td>
     <img alt="Brutaldon in Lynx" src="/docs/screenshots/screenshot-lynx.png?raw=true" title="Brutaldon in Lynx" width="256" />
   </td>
   <td>
     <img alt="Brutaldon in Firefox" src="/docs/screenshots/screenshot-firefox.png?raw=true" title="Brutaldon in Firefox" width="256" />
   </td>
  </tr>
  <tr>
    <td>
      <img alt="Brutaldon in Firefox (2)" src="/docs/screenshots/screenshot-firefox-2.png?raw=true" title="Brutaldon in Firefox (2)" width="256" />
    </td>
    <td>
      <img alt="Brutaldon in Firefox - Full Brutalism" src="/docs/screenshots/screenshot-firefox-brutalist.png?raw=true" title="Brutaldon in Firefox - Full Brutalism" width="256" />
    </td>
    <td>
      <img alt="Brutaldon in Firefox - Full Brutalism (2)" src="/docs/screenshots/screenshot-firefox-brutalist-2.png?raw=true" title="Brutaldon in Firefox - Full Brutalism (2)" width="256" />
    </td>
  </tr>
</table>






## Roadmap

* [X] Single user read-only access; log in and read home timeline
* [X] Fix edge cases of toot display (CW, media, boosts)
* [X] Multi-user, multi-instance support
* [X] Add support for reading local and federated timelines, notifications, favorites, threads
* [X] Add support for tag timelines
* [X] Add support for viewing profiles
* [X] Add support for posting.
* [X] Add support for posting media.
* [X] Add support for favoriting and boosting toots.
* [X] Add support for following, blocking, and muting users.

## Aesthetic

No automatic page updates: refresh the page to see new toots. No endless scroll: there's a "next page" link. No autocompletion of anything: use another lynx process in another screen window to look things up. UTF8 clean.

## Tip Jar

You can buy me a coffee to give me energy to work on this, but only if you have it to spare.
[![ko-fi](https://www.ko-fi.com/img/donate_sm.png)](https://ko-fi.com/D1D7QBZC)
