__author__ = 'Michal'

import datetime
import os
import sys
import csv
import io
from unittest import TestCase

# Date,Payee,Category,Memo,Outflow,Inflow
# 17/10/2017,,,POL Wroclaw Brat Wurst,15.00,
# 17/10/2017,,,POL WROCLAW CARREFOUR EXPRESS 3721,,11.19

csv.register_dialect(u"alior_dialect", delimiter=u";")
csv.register_dialect(u"inteligo_dialect", delimiter=u",")
csv.register_dialect(u"millenium_dialect", delimiter=u",")

class YnabEntry(object):
    def __init__(self, date, payee, category, memo, amount, account):
        self.INTERNAL_TRANSFER_ALIOR_CREDIT = 'Transfer : Alior-czarna'
        self.INTERNAL_TRANSFER_ALIOR_DEBIT  = 'Transfer : Alior-biala'
        self.INTERNAL_TRANSFER_MILLENIUM  = 'Transfer : Milenium'
        self.INTERNAL_TRANSFER_ALIOR_KANTOR  = 'Transfer : Alior-kantor'

        assert date
        assert amount
        self.date = date
        self.memo = self._stripMemo(memo)
        # self.category = category
        self.category = self._deduceCategory(payee=payee, memo=self.memo, account=account)
        self.amount = amount
        self.payee = self._deducePayee(payee=payee, memo=self.memo, account=account)
        self.outflow = 0
        self.inflow = 0
        if amount > 0:
            self.inflow = amount
        else:
            self.outflow = amount

    def __str__(self):
        return '%s,%s,%s,%s,%s' % (self.date.strftime('%m/%d/%Y'), self.payee, self.category, self.memo, (str(abs(self.outflow))+',') if self.outflow else (','+str(abs(self.inflow))))


    def _stripMemo(self, memo):
        memo = memo.replace(';', ' ')
        memo = memo.replace(',', ' ')
        return memo

    def _deducePayee(self, payee, memo, account):
        if 'Mulewska' in payee:
            payee = self.INTERNAL_TRANSFER_MILLENIUM
        if 'ata karty kredytowej' in memo:
            payee = self.INTERNAL_TRANSFER_ALIOR_CREDIT
        if '29 24 9000 0500 0040 0076 8995 67' in account:
            payee = self.INTERNAL_TRANSFER_ALIOR_DEBIT

        # print '\n>%s<, >%s<, >%s<' % (payee, memo, account)
        return payee.strip()

    def _deduceCategory(self, payee, memo, account):
        misiu_jedzenie = \
        ['TRABOG Boguslaw',
        'WROCLAW KARDAMON',
        'ZAPOROSKA CHATA',
        'STAROPOLSKI SMAK',
        'Restauracja Atmosfera',
        'KONRAD JANOWICZ',
        'Cukiernia u Spychaly',
        'AD DISCOVERY DAWID']

        ret = ''
        if any( i in memo for i in misiu_jedzenie):
            ret = 'Eat.: Misiu jedzenie'
        return ret

# Date,Payee,Category,Memo,Outflow,Inflow
# 17/10/2017,,,POL Wroclaw Brat Wurst,15.00,
# 17/10/2017,,,POL WROCLAW CARREFOUR EXPRESS 3721,,11.19

class AbstractRorConverter(object):
    def __init__(self):
        self.list = []
        self.list.append('Date,Payee,Category,Memo,Outflow,Inflow')

    def load(self, alior_file):
        self.input_file = alior_file

    def getStr(self):
        return u'\n'.join(map(str, self.list)) + u'\n'

    def _getValidChars(self, string):
        # return ''.join([i if ord(i) < 128 else '.' for i in string])
        return string

    def getPayee(self, row):
        payee = row[self.FIELD_PAYEE].replace(',', '')
        return self._getValidChars(payee)

    def getAmount(self, row):
        amount = row[self.FIELD_AMOUNT]
        amount = amount.replace(',','.')
        try:
             amount = float(amount)
        except ValueError as e:
            print( 'amount: >>%s<<' % amount)
            print( 'row: %s' % row)
            print( 'pos: %s' % self.FIELD_AMOUNT)
        return amount

    def getAccountNumber(self, row):
        return row[self.FIELD_ACCOUNT_NUMBER].strip()

    def convertToYnab(self, start_from_row=0):
        with io.open(self.input_file, 'r', encoding=self.encoding) as csvfile:
            self.cvsreader = csv.reader(csvfile, dialect=self.dialect)
            for i, row in enumerate(self.cvsreader):
                if i == 0 or i < start_from_row:
                    continue
                try:
                    memo = self._getValidChars(self.getMemo(row))
                    date = self.getDate(row)
                    payee = self.getPayee(row)
                    entry = YnabEntry(date=date, payee=payee, category='', memo=memo, amount=self.getAmount(row), account=self.getAccountNumber(row))
                    self.list.append(entry)
                except:
                    print( 'Error while parsing row: {}\n{}'.format(i+1, row))
                    raise

class AliorNewRorConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'alior_dialect'
        self.encoding='windows-1250'
        self.FIELD_DELIMITER = ';'
        self.FIELD_DATE = 0
        self.FIELD_PAYEE = 2
        self.FIELD_PAYEE_TO = 3
        self.FIELD_AMOUNT = 7
        self.FIELD_MEMO1 = 4
        self.FIELD_ACCOUNT_NUMBER=8

    def getPayee(self, row):
        # If cash withdrawal than no payee set
        if 'bankoma' in self.getMemo(row):
            return ''

        payee = row[self.FIELD_PAYEE].replace(',', '').strip()
        payee_to = row[self.FIELD_PAYEE_TO].replace(',', '').strip()
        if payee_to:
            payee += ' -> ' + payee_to
        elif 'micha' in payee.lower() and 'nakiew' in payee.lower():
            return ''
        return self._getValidChars(payee)


    def getMemo(self, row):
        memo = row[self.FIELD_MEMO1].strip()
        return memo


    def getDate(self, row):
        print(row[self.FIELD_DATE])
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%d-%m-%Y')



class AliorNewCardConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'alior_dialect'
        self.encoding='windows-1250'
        self.FIELD_DELIMITER = ';'
        self.FIELD_DATE = 0
        self.FIELD_PAYEE = 2
        self.FIELD_AMOUNT = 7
        self.FIELD_MEMO1 = 4
        self.FIELD_ACCOUNT_NUMBER=0

    def getMemo(self, row):
        memo = row[self.FIELD_MEMO1].strip()
        return memo

    def getDate(self, row):
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%d-%m-%Y')



class AliorRorConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'alior_dialect'
        self.encoding='windows-1250'
        self.FIELD_DELIMITER = ';'
        self.FIELD_DATE = 0
        self.FIELD_PAYEE = 2
        self.FIELD_PAYEE_TO = 3
        self.FIELD_AMOUNT = 9
        self.FIELD_MEMO1 = 4
        self.FIELD_ACCOUNT_NUMBER=0

    def getPayee(self, row):
        # If cash withdrawal than no payee set
        if 'bankoma' in self.getMemo(row):
            return ''

        payee = row[self.FIELD_PAYEE].replace(',', '').strip()
        payee_to = row[self.FIELD_PAYEE_TO].replace(',', '').strip()
        if payee_to:
            payee += ' -> ' + payee_to
        elif 'micha' in payee.lower() and 'nakiew' in payee.lower():
            return ''
        return self._getValidChars(payee)

    def getMemo(self, row):
        memo = row[self.FIELD_MEMO1].strip()
        return memo

    def getDate(self, row):
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%Y%m%d')



class AliorCardConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'alior_dialect'
        self.encoding='windows-1250'
        self.FIELD_DELIMITER = ';'
        self.FIELD_DATE = 0
        self.FIELD_PAYEE = 9
        self.FIELD_AMOUNT = 3
        self.FIELD_MEMO1 = 7
        self.FIELD_ACCOUNT_NUMBER=0

    def getMemo(self, row):
        memo = '%s' % (row[self.FIELD_MEMO1].strip())
        if not memo:
            memo = "Przelew albo prowizja?"
        return memo

    def getDate(self, row):
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%Y-%m-%d')


class InteligoRorConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'inteligo_dialect'
        self.encoding='windows-1250'
        self.FIELD_DELIMITER = ','
        self.FIELD_DATE = 2
        self.FIELD_PAYEE = 8
        self.FIELD_AMOUNT = 4
        self.FIELD_TRANSACTION_TYPE = 3
        self.FIELD_MEMO = 9
        self.FIELD_ACCOUNT_NUMBER=7

    def getMemo(self, row):
        return '%s' % (row[self.FIELD_TRANSACTION_TYPE].strip().replace(',', ' ')).strip()

    def getDate(self, row):
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%Y-%m-%d')


class MilleniumRorConverter(AbstractRorConverter):
    def __init__(self):
        AbstractRorConverter.__init__(self)
        self.dialect = 'millenium_dialect'
        self.encoding='utf-8'
        self.FIELD_DELIMITER = ','
        self.FIELD_DATE = 1
        self.FIELD_PAYEE = 5
        self.FIELD_AMOUNT_OUTFLOW = 7
        self.FIELD_AMOUNT_INFLOW = 8
        self.FIELD_TRANSACTION_TYPE = 3
        self.FIELD_MEMO = 6
        self.FIELD_ACCOUNT_NUMBER=4

    def getMemo(self, row):
        # ret = '%s | %s' % (row[self.FIELD_TRANSACTION_TYPE], row[self.FIELD_MEMO].strip().replace(',', ' '))
        ret = row[self.FIELD_MEMO].strip().replace(',', ' ').strip()
        return ret

    def getDate(self, row):
        return datetime.datetime.strptime(row[self.FIELD_DATE], '%Y-%m-%d')

    def getAmount(self, row):
        amount = row[self.FIELD_AMOUNT_OUTFLOW] if row[self.FIELD_AMOUNT_OUTFLOW] else row[self.FIELD_AMOUNT_INFLOW]
        amount = amount.replace(',','.')
        return float(amount)


''' Reference import format from YNAB page.
Date,Payee,Category,Memo,Outflow,Inflow
01/25/12,Sample Payee,,Sample Memo for an outflow,100.00,
01/26/12,Sample Payee 2,,Sample memo for an inflow,,500.00
'''


class test_converters_to_ynab(TestCase):

    def setUp(self):
        self.maxDiff = None
        pass

    def tearDown(self):
        pass

    def test_alior(self):
        converter = AliorRorConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_alior_ror1.csv')
        converter.convertToYnab()
        res = converter.getStr()

        gen_temp = os.path.dirname(__file__) + '/../tests/gen_alior_ror1.csv'
        with io.open(gen_temp, mode='w', encoding='windows-1250') as of:
            of.write(res)

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_alior_ror1_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)

    def test_new_alior(self):
        converter = AliorNewRorConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_alior_new.csv')
        converter.convertToYnab(2)
        res = converter.getStr()

        gen_temp = os.path.dirname(__file__) + '/../tests/gen_alior_new.csv'
        with io.open(gen_temp, mode='w', encoding='windows-1250') as of:
            of.write(res)

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_alior_new_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)



    def test_alior_card(self):
        converter = AliorCardConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_alior_card.csv')
        converter.convertToYnab()
        res = converter.getStr()

        gen_temp = os.path.dirname(__file__) + '/../tests/gen_alior_card.csv'
        with io.open(gen_temp, mode='w', encoding='utf-8') as of:
            of.write(res)

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_alior_card_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)


    def test_alior_new_card(self):
        converter = AliorNewCardConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_alior_new_card.csv')
        converter.convertToYnab(2)
        res = converter.getStr()

        gen_temp = os.path.dirname(__file__) + '/../tests/gen_alior_new_card.csv'
        with io.open(gen_temp, mode='w', encoding='utf-8') as of:
            of.write(res)

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_alior_new_card_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)


    def test_inteligo(self):
        converter = InteligoRorConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_inteligo_ror.csv')
        converter.convertToYnab()
        res = converter.getStr()

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_inteligo_ror_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)

    def test_millenium(self):
        converter = MilleniumRorConverter()
        converter.load(os.path.dirname(__file__) + '/../tests/ref_millenium_ror.csv')
        converter.convertToYnab()
        res = converter.getStr()

        ref_f = io.open(os.path.dirname(__file__) + '/../tests/ref_millenium_ror_ynab.csv', mode='r', encoding='windows-1250')
        ref_ynab = ref_f.read()
        self.assertMultiLineEqual(ref_ynab, res)

if __name__ == '__main__':


    converter = AliorNewRorConverter()
    converter.load(os.path.dirname(__file__) + '/alior.csv')
    converter.convertToYnab(start_from_row=2)
    res = converter.getStr()


    gen_f = os.path.dirname(__file__) + '/YNAB_alior.csv'
    with io.open(gen_f, mode='w', encoding='utf-8') as of:
        of.write(res)

    converter = AliorNewCardConverter()
    converter.load(os.path.dirname(__file__) + '/alior_card.csv')
    converter.convertToYnab(start_from_row=2)
    res = converter.getStr()
    gen_f = os.path.dirname(__file__) + '/YNAB_alior_card.csv'
    with io.open(gen_f, mode='w', encoding='utf-8') as of:
        of.write(res)

    converter = MilleniumRorConverter()
    converter.load(os.path.dirname(__file__) + '/millenium.csv')
    converter.convertToYnab()
    res = converter.getStr()
    gen_f = os.path.dirname(__file__) + '/YNAB_millenium.csv'
    with io.open(gen_f, mode='w', encoding='utf-8') as of:
        of.write(res)

    converter = InteligoRorConverter()
    converter.load(os.path.dirname(__file__) + '/inteligo.csv')
    converter.convertToYnab()
    res = converter.getStr()
    gen_f = os.path.dirname(__file__) + '/YNAB_inteligo.csv'
    with io.open(gen_f, mode='w', encoding='utf-8') as of:
        of.write(res)


    print('Success!')
    print('Press enter to exit...')
    sys.stdin.readline()