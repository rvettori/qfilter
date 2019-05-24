import re
import collections


def qfilter(params, custom_filters={}, sanitize_from=True, prefix=None):
    """ Parameters:
    Args:
        params: dictionary of filters, ex: {field__eq: '1'}
        custom_filters: dictionary with callable filters ex:
            ```
                def custom_filter(field, data):
                    return ('and field = :field', {'field': data[field]})
            ```
        sanitize_from: Quote table of from when true, ex: select * from "table"
        prefix: if used, extract only fields with prefix, ex:
            prefix= 'filter'
            param= {'filter.a':1 'field':'abc'}
            result= {'a':1}. Only this will be filtered
    """
    SPLITTER = '__'

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
        sval = __sanitize(value) if sanitize_from else value
        return "from {}".format(sval)

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
        return ('and "{}" = :{}'.format(field, field), {field: data[field]})

    def filter__eq(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" = :{}'.format(where, field), {field: data[field]})

    def filter__gt(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" > :{}'.format(where, field), {field: data[field]})

    def filter__gte(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" >= :{}'.format(where, field), {field: data[field]})

    def filter__lt(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" < :{}'.format(where, field), {field: data[field]})

    def filter__lte(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" <= :{}'.format(where, field), {field: data[field]})

    def filter__not(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        return ('and "{}" <> :{}'.format(where, field), {field: data[field]})

    def filter__any(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = tuple(str(data[field]).split(','))
        return ('and "{}" in :{}'.format(where, field), {field: data[field]})

    def filter__starts(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '{}%'.format(data[field])
        return ('and "{}" like :{}'.format(where, field), {field: data[field]})

    def filter__istarts(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '{}%'.format(data[field])
        return ('and upper("{}") like upper(:{})'.format(where, field), {field: data[field]})

    def filter__ends(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}'.format(data[field])
        return ('and "{}" like :{}'.format(where, field), {field: data[field]})

    def filter__iends(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}'.format(data[field])
        return ('and upper("{}") like upper(:{})'.format(where, field), {field: data[field]})

    def filter__cont(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}%'.format(data[field])
        return ('and "{}" like :{}'.format(where, field), {field: data[field]})

    def filter__icont(field, data):
        parts = field.split(SPLITTER)
        parts.pop()
        where = ''.join(parts)
        data[field] = '%{}%'.format(data[field])
        return ('and upper("{}") like upper(:{})'.format(where, field), {field: data[field]})

    if prefix:
        q = {re.sub('^%s[.]' % prefix, '', it[0]): it[1] for it in params.items() if it[0].startswith(prefix)}
    else:
        q = params.copy()

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
    fn.update(custom_filters)

    # Should pop before where
    s_select = _select(q.pop('_select', '*'))
    s_from = _from(q.pop('_from', ''))
    s_order = _order(q.pop('_order', ''))

    data = {}
    where = []
    for field in q:
        predicate = field.split('_').pop()
        callback = fn.get('filter__%s' % predicate)

        if str(q[field])=='':
            continue

        sql, param = callback(field, q) if callback else filter__default(field, q)
        where.append(sql)
        data.update(param)

    s_where = re.sub(r'^and', 'where', ' '.join(where))

    sql = ' '.join([s for s in [s_select, s_from, s_where, s_order] if s])

    QFilter = collections.namedtuple(
        'QFilter', 'select from_ where order sql data')
    return QFilter(select=s_select, from_=s_from, where=s_where,
                   order=s_order, sql=sql, data=data)
