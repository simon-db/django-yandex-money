# -*- coding: utf-8 -*-

from uuid import uuid4
from django.db import models
from django.conf import settings
from .signals import payment_process
from .signals import payment_completed
from django.contrib.auth import get_user_model

User = get_user_model()


class Payment(models.Model):
    class STATUS:
        PROCESSED = 'processed'
        SUCCESS = 'success'
        FAIL = 'fail'

        CHOICES = (
            (PROCESSED, 'Processed'),
            (SUCCESS, 'Success'),
            (FAIL, 'Fail'),
        )

    class PAYMENT_TYPE:
        PC = 'pc'
        AC = 'ac'
        GP = 'gp'
        MC = 'mc'

        CHOICES = (
            (PC, u'Яндекс.Деньги'),
            (AC, u'Банковская карта'),
            (GP, u'По коду через терминал'),
            (MC, u'со счета мобильного телефона'),
        )

    class CURRENCY:
        RUB = 643
        TEST = 10643

        CHOICES = (
            (RUB, u'Рубли'),
            (TEST, u'Тестовая валюта'),
        )

    user = models.ForeignKey(User, blank=True, null=True,
                             verbose_name=u'Пользователь')
    custome_number = models.CharField(u'Номер заказа',
                                      unique=True, max_length=64,
                                      default=lambda: str(uuid4()).replace('-', ''))
    status = models.CharField(u'Результат', max_length=16,
                              choices=STATUS.CHOICES,
                              default=STATUS.PROCESSED)

    scid = models.PositiveIntegerField(u'Номер витрины',
                                       default=settings.YANDEX_MONEY_SCID)
    shop_id = models.PositiveIntegerField(u'ID магазина',
                                          default=settings.YANDEX_MONEY_SHOP_ID)
    payment_type = models.CharField(u'Способ платежа', max_length=2,
                                    default=PAYMENT_TYPE.PC,
                                    choices=PAYMENT_TYPE.CHOICES)
    invoice_id = models.PositiveIntegerField(u'Номер транзакции оператора',
                                             blank=True, null=True)
    order_amount = models.FloatField(u'Сумма заказа')
    shop_amount = models.DecimalField(u'Сумма полученная на р/с',
                                      max_digits=5,
                                      decimal_places=2,
                                      blank=True, null=True,
                                      help_text=u'За вычетом процента оператора')

    order_currency = models.PositiveIntegerField(u'Валюта',
                                                 default=CURRENCY.RUB,
                                                 choices=CURRENCY.CHOICES)
    shop_currency = models.PositiveIntegerField(u'Валюта полученная на р/с',
                                                blank=True, null=True,
                                                default=CURRENCY.RUB,
                                                choices=CURRENCY.CHOICES)
    payer_code = models.CharField(u'Номер виртуального счета',
                                  max_length=33,
                                  blank=True, null=True)

    success_url = models.URLField(u'URL успешной оплаты',
                                  default=settings.YANDEX_MONEY_SUCCESS_URL)
    fail_url = models.URLField(u'URL неуспешной оплаты',
                               default=settings.YANDEX_MONEY_FAIL_URL)

    cps_email = models.EmailField(u'Почты плательщика', blank=True, null=True)
    cps_phone = models.CharField(u'Телефон плательщика', max_length=15, blank=True, null=True)

    pub_date = models.DateTimeField(u'Время создания', auto_now_add=True)
    performed_datetime = models.DateTimeField(u'Выполнение запроса', blank=True, null=True)

    @property
    def is_payed(self):
        return getattr(self, 'status', '') == self.STATUS.SUCCESS

    def send_signals(self):
        status = self.status
        if status == self.STATUS.PROCESSED:
            payment_process.send(sender=self)
        if status == self.STATUS.SUCCESS:
            payment_completed.send(sender=self)

    class Meta:
        ordering = ('pub_date',)
        verbose_name = u'Платеж'
        verbose_name_plural = u'Платежи'
