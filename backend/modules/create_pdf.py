from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts
from reportlab.lib.units import cm
from reportlab.lib import colors

from django.conf import settings
import os

class Pdf():
    def __init__(self, order):
        # Регистрируем шрифт с кириллцей
        font = ttfonts.TTFont('Arial', 'arial.ttf')
        pdfmetrics.registerFont(font)

        # Создаем путь к файлу
        self.file_name = f'Заказ_{order.id}.pdf'
        self.file_dir = os.path.join(settings.BASE_DIR, 'orders_pdf')
        if not os.path.exists(self.file_dir):
            os.makedirs(self.file_dir)
        self.path = os.path.join(self.file_dir, self.file_name)

        # Создаем файл
        self.pdf = canvas.Canvas(self.path, pagesize=A4)
        self.width, self.height = A4

        # Заголовок
        self.pdf.setFont('Arial', 18, leading=None)
        self.pdf.drawCentredString(self.width / 2, self.height - 2 * cm, f'Заказ №{order.id}')

        # Информация о заказчике
        self.pdf.setFont('Arial', 13, leading=None)
        if order.user.first_name and order.user.last_name:
            self.pdf.drawString(1 * cm, self.height - 4 * cm, f'Имя заказчика: {order.user.first_name} {order.user.last_name}')
        else:
            self.pdf.drawString(1 * cm, self.height - 4 * cm, 'Имя заказчика: не указано')

        address = f'г.{order.contact.city}, ул.{order.contact.street}, д.{order.contact.house},'
        if order.contact.structure:
            address += f'корп.{order.contact.structure},'
        if order.contact.building:
            address += f'стр.{order.contact.building},'
        if order.contact.apartment:
            address += f'кв.{order.contact.apartment}'

        self.pdf.drawString(1 * cm, self.height - 4.75 * cm, f'Адрес: {address}')
        self.pdf.drawString(1 * cm, self.height - 5.5 * cm, f'E-mail: {order.user.email}')
        if order.contact.phone:
            self.pdf.drawString(1 * cm, self.height - 6.25 * cm, f'Телефон: {order.contact.phone}')

    def draw_table(self, table_data):
        table = Table(table_data, colWidths=[1 * cm, 10 * cm, 3 * cm, 2 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -2), 0.25, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('SPAN', (0, -1), (-2, -1)),
            ('FONTSIZE', (0, -1), (-1, -1), 13),
            ('TOPPADDING', (0, -1), (-1, -1), 6),
        ]))

        w, h = table.wrapOn(self.pdf, self.height, 0)
        table.drawOn(self.pdf, 1 * cm, self.height - (7 * cm + h))

    def save(self):
        self.pdf.showPage()
        self.pdf.save()