import re
import collections


def qfilter(q, filters={}):

    def __sanitize(field):
        if field == '*':
            return '*'
        return '"{}"'.format(re.sub(r'[\s()\-\:]', '', field))

    def _select(value):
        fields = value.split(',')
        cleaned = [__sanitize(f) for f in fields if __sanitize(f)]
        if not cleaned:
            cleaned = '*'
        return "select {}".format(', '.join(cleaned))

    def _from(value):
        return "from {}".format(__sanitize(value))

    def _order(value):
        if not value:
            return ''

        fields = value.split(',')
        exp = []
        for f in fields:
            fs = f.strip()
            if fs.startswith('-'):
                exp.append('"{}" desc'.format(fs[1:]))
            else:
                exp.append('"{}" asc'.format(fs))
        return "order by {}".format(', '.join(exp))

    def filter__default(field, data):
        return 'and "{}" = :{}'.format(field, field)

    def filter__eq(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" = :{}'.format(where, field)

    def filter__gt(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" > :{}'.format(where, field)

    def filter__gte(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" >= :{}'.format(where, field)

    def filter__lt(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" < :{}'.format(where, field)

    def filter__lte(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" <= :{}'.format(where, field)

    def filter__not(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        return 'and "{}" <> :{}'.format(where, field)

    def filter__any(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = tuple(str(data[field]).split(','))
        return 'and "{}" in :{}'.format(where, field)

    def filter__starts(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '{}%'.format(data[field])
        return 'and "{}" like :{}'.format(where, field)

    def filter__istarts(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '{}%'.format(data[field])
        return 'and upper("{}") like upper(:{})'.format(where, field)

    def filter__ends(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}'.format(data[field])
        return 'and "{}" like :{}'.format(where, field)

    def filter__iends(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}'.format(data[field])
        return 'and upper("{}") like upper(:{})'.format(where, field)

    def filter__cont(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}%'.format(data[field])
        return 'and "{}" like :{}'.format(where, field)

    def filter__icont(field, data):
        parts = field.split('_')
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}%'.format(data[field])
        return 'and upper("{}") like upper(:{})'.format(where, field)

    filters_ = dict(
        filter__eq=filter__eq,
        filter__gt=filter__gt,
        filter__gte=filter__gte,
        filter__lt=filter__lt,
        filter__lte=filter__lte,
        filter__not=filter__not,
        filter__any=filter__any,
        filter__starts=filter__starts,
        filter__istarts=filter__istarts,
        filter__ends=filter__ends,
        filter__iends=filter__iends,
        filter__cont=filter__cont,
        filter__icont=filter__icont,
    )
    fn = filters_.copy()
    fn.update(filters)

    # Should pop before where
    s_select = _select(q.pop('_select', '*'))
    s_from = _from(q.pop('_from', ''))
    s_order = _order(q.pop('_order', ''))

    where = []
    for field in q:
        predicate = field.split('_').pop()
        callback = fn.get('filter__%s' % predicate)
        sql = callback(field, q) if callback else filter__default(field, q)
        where.append(sql)

    s_where = re.sub(r'^and', 'where', ''.join(where))

    sql = ' '.join([s for s in [s_select, s_from, s_where, s_order] if s])

    QFilter = collections.namedtuple(
        'QFilter', 'select from_ where order sql data')
    return QFilter(select=s_select, from_=s_from, where=s_where,
                   order=s_order, sql=sql, data=q)
