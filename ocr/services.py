"""
FinFlow - OCR сервис для распознавания чеков
Стратегия: Многоэтапное распознавание с предобработкой изображения,
использованием Tesseract OCR и постобработкой для извлечения структурированных данных
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from django.conf import settings

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Предобработка изображений для улучшения качества OCR"""
    
    def __init__(self):
        self.min_confidence = 0.6
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Предобработка изображения для улучшения качества распознавания
        Стратегия: Применение фильтров для улучшения контраста и четкости
        """
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Не удалось загрузить изображение: {image_path}")
            
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Увеличиваем контраст
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Убираем шум
            denoised = cv2.fastNlMeansDenoising(enhanced)
            
            # Бинаризация для улучшения читаемости текста
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Морфологические операции для очистки
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Ошибка предобработки изображения: {e}")
            # Возвращаем оригинальное изображение в оттенках серого
            image = cv2.imread(image_path)
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def enhance_pil_image(self, image_path: str) -> Image.Image:
        """
        Альтернативная предобработка с использованием PIL
        Стратегия: Улучшение яркости, контраста и резкости
        """
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Улучшаем контраст
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # Улучшаем резкость
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.3)
                
                # Улучшаем яркость
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)
                
                return img
                
        except Exception as e:
            logger.error(f"Ошибка улучшения PIL изображения: {e}")
            return Image.open(image_path)


class ReceiptParser:
    """Парсер для извлечения структурированных данных из распознанного текста"""
    
    def __init__(self):
        # Регулярные выражения для извлечения данных
        self.patterns = {
            'total_amount': [
                r'ИТОГО[:\s]*(\d+[.,]\d{2})',
                r'СУММА[:\s]*(\d+[.,]\d{2})',
                r'К\s*ОПЛАТЕ[:\s]*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*₽',
                r'(\d+[.,]\d{2})\s*руб',
            ],
            'receipt_number': [
                r'ЧЕК[:\s]*№?(\d+)',
                r'№[:\s]*(\d+)',
                r'ЧЕК[:\s]*(\d+)',
            ],
            'seller_name': [
                r'^([А-ЯЁ][А-ЯЁ\s]+(?:ООО|ИП|ЗАО|ОАО|АО))',
                r'^([А-ЯЁ][А-ЯЁ\s]+(?:ТОРГ|МАГАЗИН|СУПЕРМАРКЕТ))',
            ],
            'seller_inn': [
                r'ИНН[:\s]*(\d{10,12})',
                r'(\d{10,12})',
            ],
            'receipt_date': [
                r'(\d{2}[.,]\d{2}[.,]\d{4})',
                r'(\d{2}[.,]\d{2}[.,]\d{2})',
                r'(\d{4}[.,]\d{2}[.,]\d{2})',
            ],
        }
    
    def extract_data(self, text: str) -> Dict[str, Any]:
        """
        Извлечение структурированных данных из распознанного текста
        Стратегия: Поиск по регулярным выражениям с валидацией результатов
        """
        extracted = {}
        
        # Извлекаем общую сумму
        total_amount = self._extract_total_amount(text)
        if total_amount:
            extracted['total_amount'] = total_amount
        
        # Извлекаем номер чека
        receipt_number = self._extract_receipt_number(text)
        if receipt_number:
            extracted['receipt_number'] = receipt_number
        
        # Извлекаем название продавца
        seller_name = self._extract_seller_name(text)
        if seller_name:
            extracted['seller_name'] = seller_name
        
        # Извлекаем ИНН
        seller_inn = self._extract_seller_inn(text)
        if seller_inn:
            extracted['seller_inn'] = seller_inn
        
        # Извлекаем дату
        receipt_date = self._extract_receipt_date(text)
        if receipt_date:
            extracted['receipt_date'] = receipt_date
        
        return extracted
    
    def _extract_total_amount(self, text: str) -> Optional[Decimal]:
        """Извлечение общей суммы чека"""
        for pattern in self.patterns['total_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '.')
                    amount = Decimal(amount_str)
                    if 0 < amount < 1000000:  # Валидация разумного диапазона
                        return amount
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Извлечение номера чека"""
        for pattern in self.patterns['receipt_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_seller_name(self, text: str) -> Optional[str]:
        """Извлечение названия продавца"""
        lines = text.split('\n')
        for line in lines[:10]:  # Проверяем первые 10 строк
            line = line.strip()
            for pattern in self.patterns['seller_name']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return None
    
    def _extract_seller_inn(self, text: str) -> Optional[str]:
        """Извлечение ИНН продавца"""
        for pattern in self.patterns['seller_inn']:
            match = re.search(pattern, text)
            if match:
                inn = match.group(1)
                if len(inn) in [10, 12]:  # Валидация длины ИНН
                    return inn
        return None
    
    def _extract_receipt_date(self, text: str) -> Optional[datetime]:
        """Извлечение даты чека"""
        for pattern in self.patterns['receipt_date']:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    # Пробуем разные форматы даты
                    for fmt in ['%d.%m.%Y', '%d.%m.%y', '%Y.%m.%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None


class OCRService:
    """Основной сервис OCR для распознавания чеков"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.parser = ReceiptParser()
        
        # Настройка Tesseract
        if hasattr(settings, 'TESSERACT_CMD'):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
        # Конфигурация Tesseract для русского языка
        self.tesseract_config = '--oem 3 --psm 6 -l rus+eng'
    
    async def process_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Основной метод обработки чека
        Стратегия: Предобработка -> OCR -> Парсинг -> Валидация
        """
        try:
            logger.info(f"Начало обработки чека: {image_path}")
            
            # Предобработка изображения
            processed_image = self.preprocessor.preprocess_image(image_path)
            
            # OCR распознавание
            ocr_text = self._perform_ocr(processed_image)
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                # Пробуем альтернативную предобработку
                pil_image = self.preprocessor.enhance_pil_image(image_path)
                ocr_text = self._perform_ocr_pil(pil_image)
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                raise ValueError("Не удалось распознать текст на изображении")
            
            # Извлечение структурированных данных
            extracted_data = self.parser.extract_data(ocr_text)
            
            # Расчет уверенности распознавания
            confidence = self._calculate_confidence(ocr_text, extracted_data)
            
            result = {
                'text': ocr_text,
                'confidence': confidence,
                'extracted_data': extracted_data,
                'processing_time': datetime.now().isoformat(),
            }
            
            logger.info(f"Чек успешно обработан. Уверенность: {confidence:.2%}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки чека: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'extracted_data': {},
                'error': str(e),
                'processing_time': datetime.now().isoformat(),
            }
    
    def _perform_ocr(self, image: np.ndarray) -> str:
        """Выполнение OCR с использованием OpenCV изображения"""
        try:
            text = pytesseract.image_to_string(
                image, 
                config=self.tesseract_config,
                lang='rus+eng'
            )
            return text.strip()
        except Exception as e:
            logger.error(f"Ошибка OCR с OpenCV: {e}")
            return ""
    
    def _perform_ocr_pil(self, image: Image.Image) -> str:
        """Выполнение OCR с использованием PIL изображения"""
        try:
            text = pytesseract.image_to_string(
                image, 
                config=self.tesseract_config,
                lang='rus+eng'
            )
            return text.strip()
        except Exception as e:
            logger.error(f"Ошибка OCR с PIL: {e}")
            return ""
    
    def _calculate_confidence(self, text: str, extracted_data: Dict[str, Any]) -> float:
        """
        Расчет уверенности в распознавании
        Стратегия: Оценка на основе качества текста и количества извлеченных данных
        """
        confidence = 0.0
        
        # Базовая уверенность по длине текста
        if len(text) > 100:
            confidence += 0.3
        elif len(text) > 50:
            confidence += 0.2
        elif len(text) > 20:
            confidence += 0.1
        
        # Уверенность по количеству извлеченных полей
        extracted_fields = len([v for v in extracted_data.values() if v is not None])
        if extracted_fields >= 4:
            confidence += 0.4
        elif extracted_fields >= 2:
            confidence += 0.3
        elif extracted_fields >= 1:
            confidence += 0.2
        
        # Дополнительная уверенность за ключевые поля
        if extracted_data.get('total_amount'):
            confidence += 0.2
        if extracted_data.get('seller_name'):
            confidence += 0.1
        
        # Ограничиваем уверенность до 1.0
        return min(confidence, 1.0)
    
    def validate_receipt_data(self, extracted_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Валидация извлеченных данных чека
        Стратегия: Проверка корректности и полноты данных
        """
        errors = []
        
        # Проверка обязательных полей
        if not extracted_data.get('total_amount'):
            errors.append("Не удалось определить общую сумму чека")
        
        if not extracted_data.get('seller_name'):
            errors.append("Не удалось определить название продавца")
        
        # Валидация суммы
        if extracted_data.get('total_amount'):
            amount = extracted_data['total_amount']
            if amount <= 0:
                errors.append("Сумма чека должна быть больше нуля")
            elif amount > 1000000:
                errors.append("Сумма чека слишком большая")
        
        # Валидация ИНН
        if extracted_data.get('seller_inn'):
            inn = extracted_data['seller_inn']
            if len(inn) not in [10, 12]:
                errors.append("Некорректная длина ИНН")
            elif not inn.isdigit():
                errors.append("ИНН должен содержать только цифры")
        
        is_valid = len(errors) == 0
        return is_valid, errors


class ReceiptItemExtractor:
    """Извлечение позиций товаров из чека"""
    
    def __init__(self):
        # Паттерны для поиска позиций товаров
        self.item_patterns = [
            r'^([А-ЯЁ\w\s]+)\s+(\d+[.,]?\d*)\s*x?\s*(\d+[.,]\d{2})\s*(\d+[.,]\d{2})',
            r'^([А-ЯЁ\w\s]+)\s+(\d+[.,]?\d*)\s*(\d+[.,]\d{2})',
        ]
    
    def extract_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Извлечение позиций товаров из текста чека
        Стратегия: Поиск строк с названием товара, количеством и ценой
        """
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Пропускаем служебные строки
            if any(keyword in line.upper() for keyword in ['ИТОГО', 'СУММА', 'ЧЕК', 'ИНН', 'ДАТА']):
                continue
            
            item = self._parse_item_line(line)
            if item:
                items.append(item)
        
        return items
    
    def _parse_item_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Парсинг строки с позицией товара"""
        for pattern in self.item_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    name = match.group(1).strip()
                    quantity = float(match.group(2).replace(',', '.'))
                    
                    if len(match.groups()) >= 4:
                        # Формат: название количество x цена единицы общая_цена
                        unit_price = float(match.group(3).replace(',', '.'))
                        total_price = float(match.group(4).replace(',', '.'))
                    else:
                        # Формат: название количество цена
                        unit_price = float(match.group(3).replace(',', '.'))
                        total_price = unit_price * quantity
                    
                    return {
                        'name': name,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': total_price
                    }
                    
                except (ValueError, IndexError):
                    continue
        
        return None
