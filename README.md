# song-to-anki

I like to learn languages by listening to music in foreign languages, and this server-side project supports web and mobile clients that help me do that!

Code in this repo is deployed to Herkou in a Docker container and services requests from a custom `Anki-Android` fork as well as a chrome extension for learning languages through music.

Pushes to this branch are automatically deployed to heroku. This branch just contains code for the API, as well as config files. I made this a separate branch because heroku needs to see the configs in the root directory. Checkout `main` for a branch that includes code for the chrome extension, but beware that the server code on that branch has fallen behind.
