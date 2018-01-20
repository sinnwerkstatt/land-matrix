import re

from grid.forms.choices import intention_choices, get_choice_parent
from api.query_sets.sql_generation.join_functions import (
    join_attributes, join_expression,
)
from api.filters import FILTER_OPERATION_MAP
from landmatrix.models import InvestorVentureInvolvement


class WhereCondition:
    '''
    Try and take an OO approach here. This is just a starting point.
    WhereCondition objects build simple SQL strings, but there's a lot of
    logic around that.
    '''
    def __init__(self, table_name, column_name, operator, value):
        self.table_name = table_name
        self.column_name = column_name
        self.operator = operator
        self.operator_sql = FILTER_OPERATION_MAP[operator][0]
        self.value = value

    @property
    def is_value_numeric(self):
        return (
            isinstance(self.value, str) and
            self.value.isnumeric() and
            self.operator in ('lt', 'lte', 'gt', 'gte', 'is')
        )

    @property
    def is_id_column(self):
        return (
            self.column_name == 'id' or
            self.column_name == 'activity_identifier' or
            self.column_name.endswith('_id')
        )

    def quote_value(self, value):
        if value == 'on':
            # Boolean fields (like not_public)
            quoted_value = "'True'"
        elif self.operator in ('in', 'not_in') and isinstance(value, list):
            sanitized_values = [v.strip().replace("'", "\\'") for v in value]
            quoted_value = ",".join(
                ["'{}'".format(v) for v in sanitized_values])
        elif isinstance(value, str):
            sanitized_value = value.strip().replace("'", "\\'")
            if '##!##' in sanitized_value:
                sanitized_value = sanitized_value.split('##!##')[0]
            should_quote_string = False
            if 'contains' not in self.operator:
                if not (self.is_value_numeric or self.is_id_column):
                    should_quote_string = True
                elif self.column_name == 'date':
                    should_quote_string = True
            if should_quote_string:
                quoted_value = "'{}'".format(sanitized_value)
            else:
                quoted_value = sanitized_value
        else:
            quoted_value = value
        return quoted_value

    def __str__(self):
        if self.is_value_numeric and not self.is_id_column and not self.column_name == 'date' and not self.column_name == 'deal_size':
            column = "CAST(COALESCE(NULLIF({}.{}, ''), '0') AS FLOAT)".format(
                self.table_name, self.column_name)
        else:
            column = "{}.{}".format(self.table_name, self.column_name)

        value = self.quote_value(self.value)
        sql = self.operator_sql.format(
            variable=column,
            value=value
        )

        if self.operator == 'not_in':
            sql = '({} OR {} IS NULL)'.format(sql, column)

        return sql


class WhereConditions:
    '''
    Wraps multiple WhereCondition objects (or raw SQL strings, or other
    WhereConditions objects).
    '''

    def __init__(self, *conditions, conjunction='AND'):
        self.conditions = list(conditions)
        self.conjunction = conjunction

    def append(self, condition):
        self.conditions.append(condition)

    def __bool__(self):
        return bool(self.conditions)

    def __str__(self):
        joiner = ' {}\n'.format(self.conjunction)
        clause = joiner.join([str(cond) for cond in self.conditions])
        sql = '({})'.format(clause) if clause else ''

        return sql


class FilterToSQL:

    DEBUG = False
    OPERATION_MAP = FILTER_OPERATION_MAP

    count_offset = 1

    def __init__(self, filters, columns):
        FilterToSQL.count_offset += 10
        self.filters = filters
        self.columns = columns
        if self.DEBUG:
            print('FilterToSQL: filters', self.filters)
            print('FilterToSQL: columns', self.columns)

    def filter_from(self):
        from_activity = self._tables_activity()
        from_investor = self._tables_investor()
        if self.DEBUG:
            print('FilterToSQL:  tables', from_activity, "\n", from_investor)

        return "\n".join([from_activity, from_investor])

    def filter_where(self):
        where_activity = self._where_activity()
        where_investor = self.where_investor()
        if self.DEBUG:
            print('FilterToSQL:   where', where_activity, "\n", where_investor)
        return "\n".join(filter(None, [where_activity, where_investor]))

    def _where_activity(self, taggroup=None, start_index=0):
        # TODO: Split this beast up a bit better
        # TODO: lots of sql injection vulnerabilities here
        if taggroup:
            tags = taggroup
            where = WhereConditions(conjunction='OR')
        else:
            tags = self.filters.get("activity", {}).get("tags", {})
            where = WhereConditions(conjunction='AND')

        if self.filters.get("deal_scope") and self.filters["deal_scope"] != "all":
            condition = WhereCondition(
                'a', 'deal_scope', 'is', self.filters["deal_scope"])
            where.append(condition)

        for index, (tag, value) in enumerate(tags.items()):
            if not value and not tag.endswith('__is_empty'):
                continue

            i = start_index + index

            # Multiple rules?
            if isinstance(value, dict):
                if value:
                    sub_clauses = self._where_activity(
                        taggroup=value, start_index=i)
                    where.append(sub_clauses)
                    start_index += len(value) - 1
                continue

            try:
                variable, key, operation = tag.split("__")
            except ValueError:
                variable = tag
                key = 'value'
                operation = None

            table_name = 'attr_{}'.format(i)

            if variable == 'activity_identifier':
                condition = WhereCondition(
                    'a', 'activity_identifier', operation, value)
                where.append(condition)
            elif variable == 'target_region':
                table_name = 'ar{}'.format(i)
                condition = WhereCondition(
                    table_name, 'id', operation, value)
                where.append(condition)
            elif variable == 'deal_country':
                table_name = 'ac{}'.format(i)
                condition = WhereCondition(
                    table_name, key, operation, value)
                where.append(condition)
            elif variable == 'type' and 'data_source_type' in self.columns:
                # Special hack for weird results in data source filtering
                # This is results in a pretty broken query, but it's a
                # way to get the exclude media reports filter working
                # without major surgery. Works by lining up the
                # columns that we're joining twice :(
                conditions = WhereConditions(
                    WhereCondition(table_name, 'name', 'is', 'type'),
                    "{}.value = data_source_type.value".format(table_name))
                where.append(conditions)
            elif variable in ('current_negotiation_status', 'implementation_status', 'deal_size',
                              'deal_scope', 'init_date') and key == 'value':
                if variable == 'current_negotiation_status':
                    variable = 'negotiation_status'
                # Special cases in that we need to filter on the activity table
                # (as the most recent status is cached there)
                condition = WhereCondition('a', variable, operation, value)
                where.append(condition)
            elif variable == 'fully_updated':
                condition = WhereCondition('a', variable, operation, value)
                where.append(condition)
            elif operation not in ('in', 'not_in') and isinstance(value, list):
                for subvalue in value:
                    conditions = WhereConditions(
                        WhereCondition(table_name, key, operation, subvalue))
                    where.append(conditions)
            else:
                conditions = WhereConditions(
                    WhereCondition(table_name, key, operation, value))
                where.append(conditions)

            is_operation_limits = self._where_activity_filter_is_operator(
                variable, operation, value)
            if is_operation_limits:
                where.append(is_operation_limits)
        if taggroup:
            return where
        else:
            return 'AND {}'.format(where) if where else ''

    def _where_activity_deal_scope(self):
        where = []
        if self.filters.get("deal_scope") and self.filters.get("deal_scope") != "all":
            where.append("AND a.deal_scope = '%s' " % self.filters.get("deal_scope"))

        return where

    def _where_activity_filter_is_operator(self, variable, operation, value):
        if not isinstance(value, list):
            value = [value]

        where = ''
        # TODO: optimize SQL? This query seems painful, it could be
        # better as an array_agg possibly
        excluded_variables = (
            'deal_country', 'target_country', 'target_region',
            'investor_country', 'investor_region', 'negotiation_status',
            'implementation_status', 'not_public',
            'deal_scope', 'init_date'
        )
        if operation == 'is' and variable not in excluded_variables:
            # 'Is' operations requires that we exclude other values,
            # otherwise it's just the same as contains

            allowed_values = None
            if variable == 'intention':
                # intentions can be nested, for example all biofuels
                # deals are also agriculture (parent of biofuels)
                parent_value = get_choice_parent(value[-1], intention_choices)
                if parent_value:
                    allowed_values = (
                        parent_value,
                        value[-1].replace("'", "\\'"),
                    )

            if not allowed_values:
                allowed_values = (value[-1].replace("'", "\\'"),)

            # Exclude deals with given AND other values
            where = """
                a.id NOT IN (
                    SELECT fk_activity_id
                    FROM landmatrix_activityattribute
                    WHERE landmatrix_activityattribute.name = '%(variable)s'
                    AND landmatrix_activityattribute.value NOT IN ('%(value)s')
                )
                """ % {
                'variable': variable,
                'value': "', '".join([str(v) for v in allowed_values]),
            }

        return where

    def _tables_activity(self, taggroup=None, last_index=0):
        tables_from = []

        tags = taggroup or self.filters.get("activity").get("tags")
        for index, (tag, value) in enumerate(tags.items()):
            i = last_index + index
            # Multiple rules?
            if isinstance(value, dict):
                if value:
                    tables_from.append(
                        self._tables_activity(taggroup=value, last_index=i))
                    last_index += len(value) - 1
                continue
            variable_operation = tag.split("__")
            variable = variable_operation[0]
            key = variable_operation[1]

            no_join_required = (
                variable == 'activity_identifier' or (
                    variable in ('negotiation_status', 'implementation_status') and
                    key == 'value')
            )

            if no_join_required:
                continue
            elif variable in ('target_region', 'deal_country'):
                tables_from.append(
                    """
                    LEFT JOIN landmatrix_activityattribute AS attr_%(count)i
                    ON (a.id = attr_%(count)i.fk_activity_id AND attr_%(count)i.name = 'target_country')
                    """ % {
                        'count': i,
                    })
                tables_from.append(
                    """
                    LEFT JOIN landmatrix_country AS ac%(count)i
                    ON CAST(NULLIF(attr_%(count)i.value, '0') AS NUMERIC) = ac%(count)i.id
                    """ % {
                        'count': i,
                    })
                if variable == 'target_region':
                    tables_from.append(
                        """
                        LEFT JOIN landmatrix_region AS ar%(count)i
                        ON ar%(count)i.id = ac%(count)i.fk_region_id
                        """ % {
                            'count': i,
                        })
            elif variable.isdigit():
                tables_from.append(
                    "LEFT JOIN landmatrix_activityattribute AS attr_%(count)i\n" \
                    " ON (a.id = attr_%(count)i.fk_activity_id AND attr_%(count)i.key_id = '%(key)s')" % {
                        "count": i,
                        "key": variable
                    }
                )
            else:
                tables_from.append(join_attributes("attr_%(count)i" % {"count": i}, variable))
        return '\n'.join(tables_from)

    def where_investor(self):
        where_inv = ''
        tags = self.filters.get("investor", {}).get("tags", {})
        for index, (tag, value) in enumerate(tags.items()):
            i = index + FilterToSQL.count_offset

            if not value:
                continue

            try:
                variable, key, operation = tag.split("__")
            except ValueError:
                variable = tag
                key = 'value'
                operation = 'is'

            if operation == "is_empty" or not value or (value and not value[0]):
                where_inv += " AND operating_company_{count}.id IS NULL ".format(count)
            elif operation in ("in", "not_in"):
                value = value[0].split(",")
                in_values = ",".join(["'%s'" % v.strip().replace("'", "\\'") for v in value])
                op_sql = self.OPERATION_MAP[operation][0] % in_values
                if 'region' in variable:
                    where_inv += "AND investor_region_{count}.id {op}".format(count=i, op=op_sql)
                elif 'country' in 'variable':
                    where_inv += "AND investor_country_{count}.id {op}".format(count=i, op=op_sql)
                else:
                    where_inv += "AND operating_company_{count}.id {op}".format(count=i, op=op_sql)
            else:
                if not isinstance(value, list):
                    value = [value]

                for v in value:
                    operation_type = not v.isdigit() and 1 or 0
                    op_sql = self.OPERATION_MAP[operation][operation_type] % v.replace("'", "\\'")
                    #if self.DEBUG:
                    #    print('FilterToSQL.where_investor:', index, variable, operation, v, operation_type)

                    if 'region' in variable:
                        where_inv += "AND investor_region_{count}.id {op}".format(count=i, op=op_sql)
                    elif 'country' in variable:
                        where_inv += "AND investor_country_{count}.id {op}".format(count=i, op=op_sql)
                    elif variable == 'investor':
                        where_inv += ' AND sh.investor_identifier = {}'.format(v)
                    elif variable == 'operational_stakeholder' and 'contains' not in operation:
                        where_inv += " AND operational_stakeholder_%i.id %s" % (i, self.OPERATION_MAP[operation][operation_type] % v.replace("'", "\\'"))
                    elif 'operating_company_' in variable:
                        variable = variable.replace('operating_company_', '')
                        where_inv += " AND operational_stakeholder_%i.%s %s" % (i, variable, self.OPERATION_MAP[operation][operation_type] % v.replace("'", "\\'"))
                    elif 'parent_stakeholder_' in variable:
                        variable = variable.replace('parent_stakeholder_', '')
                        where_inv += " AND ivi_%i.role = '%s'" % (i, InvestorVentureInvolvement.STAKEHOLDER_ROLE)
                        where_inv += " AND parent_stakeholder_%i.%s %s" % (i, variable, self.OPERATION_MAP[operation][operation_type] % v.replace("'", "\\'"))
                    elif 'parent_investor_' in variable:
                        variable = variable.replace('parent_investor_', '')
                        where_inv += " AND ivi_%i.role = '%s'" % (i, InvestorVentureInvolvement.INVESTOR_ROLE)
                        where_inv += " AND parent_investor_%i.%s %s" % (i, variable, self.OPERATION_MAP[operation][operation_type] % v.replace("'", "\\'"))

        return where_inv

    def _tables_investor(self):
        # TODO: resuse previous joins. This duplicates a lot of SQLBuilderData
        investor_tables = []
        tags = self.filters.get("investor", {}).get("tags", {})

        for index, (tag, value) in enumerate(tags.items()):
            i = index + FilterToSQL.count_offset

            if value:
                variable = tag.split("__")[0]

            INVESTOR_JOINS = {
                'operating_company': [
                    join_expression(
                        'landmatrix_investoractivityinvolvement',
                        'iai_{count}'.format(count=i), 'a.id', 'fk_activity_id'),
                    join_expression(
                        'landmatrix_investor',
                        'operational_stakeholder_{count}'.format(count=i),
                        'iai_{count}.fk_investor_id'.format(count=i)),
                ],
                'parent_stakeholder': [
                    join_expression(
                        'landmatrix_investorventureinvolvement',
                        'ivi_{count}'.format(count=i),
                        'operational_stakeholder_{count}.id'.format(count=i),
                        'fk_venture_id'),
                    join_expression(
                        'landmatrix_investor',
                        'parent_stakeholder_{count}'.format(count=i),
                        'ivi_{count}.fk_investor_id'.format(count=i)),
                ],
                'parent_investor': [
                    join_expression(
                        'landmatrix_investorventureinvolvement',
                        'ivi_{count}'.format(count=i),
                        'operational_stakeholder_{count}.id'.format(count=i),
                        'fk_venture_id'),
                    join_expression(
                        'landmatrix_investor',
                        'parent_investor_{count}'.format(count=i),
                        'ivi_{count}.fk_investor_id'.format(count=i)),
                ],
            }
            role = re.match('^(operating_company|parent_stakeholder|parent_investor)_', variable).groups()[0]
            if role == 'operating_company':
                investor_tables.extend(INVESTOR_JOINS['operating_company'])
            elif role == 'parent_stakeholder':
                investor_tables.extend(INVESTOR_JOINS['operating_company'])
                investor_tables.extend(INVESTOR_JOINS['parent_stakeholder'])
            elif role == 'parent_investor':
                investor_tables.extend(INVESTOR_JOINS['operating_company'])
                investor_tables.extend(INVESTOR_JOINS['parent_investor'])

            if 'country' in variable:
                country_join = join_expression(
                    'landmatrix_country',
                    'investor_country_{count}'.format(count=i),
                    '{role}_{count}.fk_country_id'.format(count=i, role=role))
                investor_tables.append(country_join)
            elif 'region' in variable:
                region_join = join_expression(
                    'landmatrix_region',
                    'investor_region_{count}'.format(count=i),
                    '{role}_region_{count}.fk_region_id'.format(count=i, role=role))
                investor_tables.append(region_join)

        return '\n'.join(investor_tables)
