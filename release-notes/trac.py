#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2022 Chris Johns (chris@contemporary.software)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import pickle
import os
import urllib.request


class cache(object):

    def __init__(self, milestone, path, force):
        self.milestone = milestone
        self.path = path
        self.force = force
        self.checked = False
        self.cache_valid = False

    @staticmethod
    def _milestone(url):
        path, options = url.split('?', 1)
        opts = options.split('&')
        for o in opts:
            if 'milestone' in o:
                label, milestone = o.split('=', 1)
                return milestone
        raise RuntimeError('milestone not found: ' + url)

    def _tickets_path(self):
        return os.path.join(self.path,
                            'tickets-%s' % (self.milestone) + '.ppk')

    def _ticket_path(self, url):
        path, options = url.split('?', 1)
        opts = options.split('&')
        fmt = None
        for o in opts:
            if 'format' in o:
                label, fmt = o.split('=', 1)
        if not fmt:
            raise RuntimeError('ticket format not found: ' + url)
        if '/' in path:
            ticket_id = path[path.rfind('/') + 1:]
            return os.path.join(self.path, '%s.%s' % (ticket_id, fmt))
        raise RuntimeError('ticket id not found: ' + url)

    def _query_path(self):
        return os.path.join(self.path, 'query-%s' % (self.milestone) + '.csv')

    def check(self):
        if not self.checked:
            self.checked = True
            if self.path:
                if os.path.exists(self.path):
                    if not os.path.isdir(self.path):
                        raise RuntimeError('cache is not a directory:' +
                                           self.path)
                else:
                    os.mkdir(self.path)
                self.cache_valid = True
        return self.cache_valid

    def open_page(self, url):
        url_path = None
        if self.check():
            if 'query' in url:
                url_path = self._query_path()
            else:
                url_path = self._ticket_path(url)
            if not self.force and os.path.exists(url_path):
                return open(url_path, 'rb')
        # Open the URL
        delay = 1
        tries = 6
        backoff = 2
        while tries > 0:
            try:
                page = urllib.request.urlopen(url)
                if url_path:
                    with open(url_path, 'wb') as f:
                        f.write(page.read())
                    return open(url_path, 'rb')
                return page
            except OSError:
                tries -= 1
                time.sleep(delay)
                delay *= backoff
        raise RuntimeError('cannot open url:' + url)

    def load(self):
        if self.check():
            ticket_cache = self._tickets_path()
            if os.path.exists(ticket_cache):
                if not self.force:
                    try:
                        with open(ticket_cache, 'rb') as f:
                            tickets = pickle.load(f)
                            print('%d tickets loaded from cache: %s' %
                                  (len(tickets['tickets']), ticket_cache))
                            return tickets
                    except:
                        print('cache corrupted: ' + ticket_cache)
                os.remove(ticket_cache)
        return None

    def unload(self, tickets):
        if self.check():
            ticket_cache = self._tickets_path()
            with open(ticket_cache, 'wb') as f:
                pickle.dump(tickets, f)
