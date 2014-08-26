# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Manager for quickmarks.

Note we violate our general QUrl rule by storing url strings in the marks
OrderedDict. This is because we read them from a file at start and write them
to a file on shutdown, so it makes semse to keep them as strings her.e
"""

import functools
import collections

from PyQt5.QtCore import QStandardPaths, QUrl

from qutebrowser.utils import message, usertypes, utils
from qutebrowser.utils import qt as qtutils
from qutebrowser.commands import utils as cmdutils
from qutebrowser.commands import exceptions as cmdexc
from qutebrowser.config import lineparser


marks = collections.OrderedDict()
linecp = None


def init():
    """Read quickmarks from the config file."""
    global linecp
    confdir = utils.get_standard_dir(QStandardPaths.ConfigLocation)
    linecp = lineparser.LineConfigParser(confdir, 'quickmarks')
    for line in linecp:
        try:
            key, url = line.split(maxsplit=1)
        except ValueError:
            message.error("Invalid quickmark '{}'".format(line))
        else:
            marks[key] = url


def save():
    """Save the quickmarks to disk."""
    linecp.data = [' '.join(tpl) for tpl in marks.items()]
    linecp.save()


def prompt_save(url):
    """Prompt for a new quickmark name to be added and add it.

    Args:
        url: The quickmark url as a QUrl.
    """
    qtutils.ensure_valid(url)
    urlstr = url.toString(QUrl.RemovePassword | QUrl.FullyEncoded)
    message.ask_async("Add quickmark:", usertypes.PromptMode.text,
                      functools.partial(quickmark_add, urlstr))


@cmdutils.register()
def quickmark_add(urlstr, name):
    """Add a new quickmark.

    Args:
        urlstr: The url to add as quickmark, as string.
        name: The name for the new quickmark.
    """
    if not name:
        raise cmdexc.CommandError("Can't set mark with empty name!")
    if not urlstr:
        raise cmdexc.CommandError("Can't set mark with empty URL!")

    def set_mark():
        """Really set the quickmark."""
        marks[name] = urlstr

    if name in marks:
        message.confirm_async("Override existing quickmark?", set_mark,
                              default=True)
    else:
        set_mark()


def get(name):
    """Get the URL of the quickmark named name as a QUrl."""
    if name not in marks:
        raise cmdexc.CommandError(
            "Quickmark '{}' does not exist!".format(name))
    urlstr = marks[name]
    url = QUrl(urlstr)
    if not url.isValid():
        raise cmdexc.CommandError(
            "Invalid URL for quickmark {}: {} ({})".format(name, urlstr,
                                                           url.errorString()))
    return url
