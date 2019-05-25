import unittest
from qfilter import qfilter


class QFilterTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_filter_eq(self):
        exp = qfilter(dict(field1__eq=2))
        self.assertEqual('where "field1" = :field1__eq', exp.where)
        self.assertEqual({'field1__eq': 2}, exp.data)

    def test_filter_gt(self):
        exp = qfilter(dict(field1__gt=2))
        self.assertEqual('where "field1" > :field1__gt', exp.where)
        self.assertEqual({'field1__gt': 2}, exp.data)

    def test_filter_gte(self):
        exp = qfilter(dict(field1__gte=2))
        self.assertEqual('where "field1" >= :field1__gte', exp.where)
        self.assertEqual({'field1__gte': 2}, exp.data)

    def test_filter_lt(self):
        exp = qfilter(dict(field1__lt=2))
        self.assertEqual('where "field1" < :field1__lt', exp.where)
        self.assertEqual({'field1__lt': 2}, exp.data)

    def test_filter_lte(self):
        exp = qfilter(dict(field1__lte=2))
        self.assertEqual('where "field1" <= :field1__lte', exp.where)
        self.assertEqual({'field1__lte': 2}, exp.data)

    def test_filter_not(self):
        exp = qfilter(dict(field1__not=2))
        self.assertEqual('where "field1" <> :field1__not', exp.where)
        self.assertEqual({'field1__not': 2}, exp.data)

    def test_filter_any(self):
        exp = qfilter(dict(field1__any='2,3'))
        self.assertEqual('where "field1" in :field1__any', exp.where)
        self.assertEqual({'field1__any': ('2', '3')}, exp.data)

    def test_filter_starts(self):
        exp = qfilter(dict(field1__starts=2))
        self.assertEqual('where "field1" like :field1__starts', exp.where)
        self.assertEqual({'field1__starts': '2%'}, exp.data)

    def test_filter_istarts(self):
        exp = qfilter(dict(field1__istarts='a'))
        self.assertEqual(
            'where upper("field1") like upper(:field1__istarts)', exp.where)
        self.assertEqual({'field1__istarts': 'a%'}, exp.data)

    def test_filter_ends(self):
        exp = qfilter(dict(field1__ends='abc'))
        self.assertEqual('where "field1" like :field1__ends', exp.where)
        self.assertEqual({'field1__ends': '%abc'}, exp.data)

    def test_filter_iends(self):
        exp = qfilter(dict(field1__iends='abc'))
        self.assertEqual(
            'where upper("field1") like upper(:field1__iends)', exp.where)
        self.assertEqual({'field1__iends': '%abc'}, exp.data)

    def test_filter_cont(self):
        exp = qfilter(dict(field1__cont='abc'))
        self.assertEqual('where "field1" like :field1__cont', exp.where)
        self.assertEqual({'field1__cont': '%abc%'}, exp.data)

    def test_filter_icont(self):
        exp = qfilter(dict(field1__icont='abc'))
        self.assertEqual(
            'where upper("field1") like upper(:field1__icont)', exp.where)
        self.assertEqual({'field1__icont': '%abc%'}, exp.data)

    def test_filter_default(self):
        exp = qfilter(dict(field1='abc'))
        self.assertEqual('where "field1" = :field1', exp.where)
        self.assertEqual({'field1': 'abc'}, exp.data)

    def test_conditions(self):
        exp = qfilter(dict(field1='abc', field2__any='x,y', field3__gte=7))
        self.assertIn('"field1" = :field1', exp.sql)
        self.assertIn('"field2" in :field2__any', exp.sql)
        self.assertIn('"field3" >= :field3__gte', exp.sql)
        self.assertEqual({'field3__gte': 7, 'field1': 'abc',
                          'field2__any': ('x', 'y')}, exp.data)

    def test_and_space_between_condition(self):
        exp = qfilter(dict(field1='abc', field2_any='x,y', field3_gte=7))
        self.assertRegex(exp.sql, r'\sand\s')

    def test_clause_from(self):
        exp = qfilter(dict(_from='table1'))
        self.assertEqual('select * from "table1"', exp.sql)
        self.assertEqual({}, exp.data)
        self.assertEqual('from "table1"', exp.from_)


    def test_clause_from_without_sanitize(self):
        exp = qfilter(dict(_from='table1'), sanitize_from=False)
        self.assertEqual('select * from table1', exp.sql)
        self.assertEqual('from table1', exp.from_)

    def test_without_quote_fields(self):
        self.maxDiff = None
        param = dict(_order='-field', _select='field',_from='table1',
                     field__eq=123, field__gt=123, field__gte=123,
                     field__lt=123, field__lte=123, field__not=123,
                     field__any=123, field__starts=123, field__ends=123,
                     field__istarts=123, field__iends=123, field__cont=123,
                     field__icont=123)
        exp = qfilter(param, quote_fields=False)
        result = 'select field from table1 where field = :field__eq and field > :field__gt and field >= :field__gte and field < :field__lt and field <= :field__lte and field <> :field__not and field in :field__any and field like :field__starts and field like :field__ends and upper(field) like upper(:field__istarts) and upper(field) like upper(:field__iends) and field like :field__cont and upper(field) like upper(:field__icont) order by field desc'
        self.assertEqual(result, exp.sql)
        self.assertEqual('from table1', exp.from_)

    def test_clause_select(self):
        exp = qfilter(dict(_select='a,b,c', _from='table1'))
        self.assertEqual('select "a", "b", "c" from "table1"', exp.sql)
        self.assertEqual({}, exp.data)
        self.assertEqual('select "a", "b", "c"', exp.select)

    def test_clause_order(self):
        exp = qfilter(dict(_select='a,b,c', _from='table1', _order='a,-b'))
        self.assertEqual(
            'select "a", "b", "c" from "table1" order by "a" asc, "b" desc', exp.sql)
        self.assertEqual({}, exp.data)
        self.assertEqual('order by "a" asc, "b" desc', exp.order)

    def test_sql(self):
        exp = qfilter(
            dict(_select='a,b,c', _from='table1', _order='a,-b', a__eq=1))
        self.assertEqual(
            'select "a", "b", "c" from "table1" where "a" = :a__eq order by "a" asc, "b" desc', exp.sql)
        self.assertEqual({'a__eq': 1}, exp.data)
        self.assertEqual('order by "a" asc, "b" desc', exp.order)

    def test_sanitized_select(self):
        exp = qfilter(dict(_select='trim(a)::bigint as show,b,c'))
        self.assertEqual('select "trimabigintasshow", "b", "c"', exp.select)

    def test_filter_with_empty_value(self):
        exp = qfilter(dict(field1__cont=''))
        self.assertEqual('', exp.where)
        self.assertEqual({}, exp.data)

    def test_filter_with_prefix(self):
        exp = qfilter({'q.field1__eq': 2}, prefix='q')
        self.assertEqual('where "field1" = :field1__eq', exp.where)
        self.assertEqual({'field1__eq': 2}, exp.data)
        exp = qfilter({'filter.field1__eq': 2}, prefix='filter')
        self.assertEqual('where "field1" = :field1__eq', exp.where)


if __name__ == '__main__':
    unittest.main()
