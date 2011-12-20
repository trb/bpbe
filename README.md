BPBE, a fast and simple blog engine.
====

It's mainly intended as an example of my work, since most of what I've
developed so far is proprietary.

Goal
====
====
My goal was to handle over a billion requests to the index page on a small
VPS instance I've rented. A fairly arbitrary goal, but BPBE should on any
available server setup be fast enough to handle even substantial traffic
spikes.

Technologies
====
====
The technologies used are Redis for Caching/Data storage, Python+Pyramid for
the backend and jQuery/Compass for the frontend.

Interesting aspects
====
====
The most (and only, really) interesting aspect of this software would be the
Multiload cache class in hobonaut.models.cache. It makes it easy to cache
complex data structures while handling cache invalidation.
