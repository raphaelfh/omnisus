class FaultyConnection:
    def __init__(self, connection, *, before=None, after=None):
        self.connection = connection
        self.before = dict(before or {})
        self.after = dict(after or {})

    def _fail(self, rules, sql):
        normalized = sql.strip().upper()
        for prefix in tuple(rules):
            if normalized.startswith(prefix):
                raise rules.pop(prefix)

    def execute(self, sql, parameters=None):
        self._fail(self.before, sql)
        result = self.connection.execute(sql, parameters)
        self._fail(self.after, sql)
        return result

    def executemany(self, sql, parameters):
        self._fail(self.before, sql)
        result = self.connection.executemany(sql, parameters)
        self._fail(self.after, sql)
        return result

    def __getattr__(self, name):
        return getattr(self.connection, name)
