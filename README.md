# Brutaldon

Brutaldon is a [brutalist][0], [Web 1.0][0.5] web interface for [Mastodon][1]. It is not a Mastodon-compatible social networking server; rather, it is just a client, like the Android or iOS client for Mastodon you may already be using, but it runs in a web server, and is accessed through a web browser. The web browser that brutaldon targets is [Lynx][2]. Of course, you can use it in a more heavy-weight graphical browser, as well as other text browsers such as [w3m][3] or [elinks][4].

[0]:http://brutalistwebsites.com/
[0.5]: https://en.wikipedia.org/wiki/Web_2.0#%22Web_1.0%22
[1]: https://joinmastodon.org/
[2]: https://lynx.browser.org/
[3]: https://w3m.sourceforge.net/
[4]: http://elinks.or.cz/

Brutaldon is ready for day to day use, but is still missing many features.
Please see the issues tracker.

## Screenshots

People love screenshots, whatever the project, so here we are.

![Brutaldon in Lynx](/docs/screenshots/screenshot-lynx.png?raw=true "Brutaldon in Lynx")
![Brutaldon in Firefox](/docs/screenshots/screenshot-firefox.png?raw=true "Brutaldon in Firefox")
![Brutaldon in Firefox (2)](/docs/screenshots/screenshot-firefox-2.png?raw=true "Brutaldon in Firefox (2)")
![Brutaldon in Firefox - Full Brutalism](/docs/screenshots/screenshot-firefox-brutalist.png?raw=true "Brutaldon in Firefox - Full Brutalism")
![Brutaldon in Firefox - Full Brutalism (2)](/docs/screenshots/screenshot-firefox-brutalist-2.png?raw=true "Brutaldon in Firefox - Full Brutalism (2)")





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
* [ ] Add support for following, blocking, and muting users.

## Aesthetic

No automatic page updates: refresh the page to see new toots. No endless scroll: there's a "next page" link. No autocompletion of anything: use another lynx process in another screen window to look things up. UTF8 clean.
