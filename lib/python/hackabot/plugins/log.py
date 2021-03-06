
from zope.interface import implements
from twisted.plugin import IPlugin

from hackabot.plugin import IHackabotPlugin
from hackabot import db

class DBLogger(object):
    """Log events to the database.

    This is a little ugly as the database has to use the same names
    while events are free to use names that make sense.
    """
    implements(IPlugin, IHackabotPlugin)

    def msg(self, conn, event):
        if event['sent_to'] == conn.nickname:
            event['channel'] = None
        else:
            event['channel'] = event['sent_to']
            event['sent_to'] = None

        event['count'] = None
        self._logger(conn, event)

    notice = msg

    def me(self, conn, event):
        event['type'] = 'action'
        self.msg(conn, event)

    def topic(self, conn, event):
        event['sent_by'] = event['user']
        event['sent_to'] = None
        event['count'] = None
        self._logger(conn, event)

    def join(self, conn, event):
        event['sent_by'] = event['user']
        event['sent_to'] = None
        event['text'] = None
        event['count'] = None
        self._logger(conn, event)

    def part(self, conn, event):
        event['sent_by'] = event['user']
        event['sent_to'] = None
        event['count'] = None
        self._logger(conn, event)

    def kick(self, conn, event):
        event['sent_by'] = event['kicker']
        event['sent_to'] = event['kickee']
        event['count'] = None
        self._logger(conn, event)

    def quit(self, conn, event):
        event['sent_by'] = event['user']
        event['sent_to'] = None
        event['channel'] = None
        event['count'] = None
        self._logger(conn, event)

    def rename(self, conn, event):
        # We abuse sent_to slightly here
        event['sent_by'] = event['old']
        event['sent_to'] = event['new']
        event['channel'] = None
        event['text'] = None
        event['count'] = None
        self._logger(conn, event)

    def names(self, conn, event):
        #TODO: change enum value from 'stats' to 'names'
        event['type'] = 'stats'
        event['sent_by'] = None
        event['sent_to'] = None
        event['count'] = len(event['users'])
        event['text'] = " ".join(event['users'])
        self._logger(conn, event)

    def _logger(self, conn, event):
        """Record an event to the log table"""

        dbpool = conn.manager.dbpool
        if not dbpool:
            return

        # These correspond to the type column's enum values
        assert event['type'] in ('msg', 'action', 'notice', 'join', 'part',
                'quit', 'stats', 'topic', 'kick', 'rename')

        # double check that everything is there
        for key in ('sent_by', 'sent_to', 'channel', 'text',
                'count', 'type', 'time'):
            assert key in event

        sql = ("INSERT INTO `log` "
            "(`sent_by`,`sent_to`,`channel`,`text`,`count`,`type`,`date`) "
            "VALUES (%(sent_by)s, %(sent_to)s, %(channel)s, %(text)s, "
            "%(count)s, %(type)s, FROM_UNIXTIME(%(time)s) )")

        try:
            dbpool.runOperation(sql, event)
        except db.ConnectionLost:
            dbpool.runOperation(sql, event)

logger = DBLogger()
