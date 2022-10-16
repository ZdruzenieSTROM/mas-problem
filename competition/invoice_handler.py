"""API manual: https://www.faktury-online.com/faktury-online-api/manual"""

import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils.timezone import now


class InvoiceItem:
    def __init__(self, name: str, unit: str, price: float):
        self.name = name
        self.unit = unit
        self.price = price


class InvoiceSession:
    STROM_ID = 51636

    def __init__(self):
        self.session = requests.Session()
        self.__send_request('init', {})

    def __send_request(self, method: str, data: dict):
        """Request to Faktury"""
        return self.session.get(
            f'https://www.faktury-online.com/api/{method}',
            params={
                'data': json.dumps(
                    dict(
                        key=settings.FAKTURY_API_KEY,
                        email='info@strom.sk',
                        apitest=1 if settings.DEBUG else 0,
                        **data
                    )
                )
            },
            verify=True
        )

    def download_invoice(self, code):
        return self.__send_request(
            'detail-subor',
            params={'f': code}
        ).content

    def get_invoice(self, code):
        invoice_url = self.__send_request('zf', {'code': code}).json()['url']
        response = self.session.get(invoice_url)
        return response.content

    def create_invoice(self, customer: Dict[str, str], items: Dict[List[InvoiceItem], int], delivery_date):
        items_compiled = []
        for item, quantity in items.items():
            if quantity == 0 or quantity == '0':
                continue
            items_compiled.append(
                {
                    'p_text': item.name,
                    'p_unit': item.unit,
                    'p_price': str(item.price),
                    'p_quantity': quantity
                }
            )
        response = self.__send_request(
            'nf',
            {
                'd': {'d_id': self.STROM_ID},
                'o': customer,
                'f': {
                    'f_date_issue': now().strftime("%d.%m.%Y"),
                    'f_date_delivery': delivery_date.strftime("%d.%m.%Y"),
                    'f_date_due': (delivery_date-timedelta(2)).strftime("%d.%m.%Y"),
                    'f_issued_by': settings.INVOICE_ISSUER,
                },
                'p': items_compiled
            }

        )
        code = response.json()['code']
        return code

    @staticmethod
    def create_empty_template(file_name):
        fieldnames = [
            'o_name',
            'o_street',
            'o_city',
            'o_state',
            'o_zip',
            'o_ico',
            'o_dic',
            'o_icdph',
            'o_email'
        ]
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
