__author__ = 'Michal'
#  coding: utf-8 -*-
# -*- coding: windows-1250 -*-

from unittest import TestCase
import os

from modules.alior2YNAB import AliorRorConverter

import sys
''' Reference import format from YNAB page.
Date,Payee,Category,Memo,Outflow,Inflow
01/25/12,Sample Payee,,Sample Memo for an outflow,100.00,
01/26/12,Sample Payee 2,,Sample memo for an inflow,,500.00
'''




class test_convert_alior_to_ynab(TestCase):

    def setUp(self):
        self.maxDiff = None
        pass

    def tearDown(self):
        pass

    #
    # def test_alior(self):
    #     converter = AliorRorConverter()
    #     converter.load(os.path.dirname(__file__) + '/ref_alior_ror1.csv')
    #     converter.convertToYnab()
    #     res = converter.getStr()
    #
    #     f = open(os.path.dirname(__file__) + '/ref_alior_ror1_ynab.csv')
    #     ref_ynab_format = f.read()
    #     self.assertMultiLineEqual(res, ref_ynab_format)
    #
    #
    # def test_inteligo(self):
    #     converter = AliorRorConverter()
    #     converter.load(os.path.dirname(__file__) + '/ref_inteligo_ror.csv')
    #     converter.convertToYnab()
    #     res = converter.getStr()
    #     with open(os.path.dirname(__file__) + '/ref_inteligo_ror_YNAB.csv', 'wb') as f:
    #         f.write(res)

  #   9 289 Alior
  # - 1 651 Karta
  #   4 507 Inteligo
  #  25 539 Milenium

