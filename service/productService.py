from decimal import Decimal
from data.repositories.productRepository import ProductRepository
from data.entities.product import Product

import requests
from bs4 import BeautifulSoup
import re

from service.telegramService import TelegramService

class ProductService:
    def __init__(self, repository: ProductRepository, telegram_service: TelegramService):
        self.repository = repository
        self.telegram_service = telegram_service
        self.base_url = "https://www.vatanbilgisayar.com/"
    async def updateProduct(self):
        links = self.repository.get_all_product_links()

        for link in links:

            response = requests.get(str(self.base_url) + str(link))
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                product_detail_div = soup.find('div', class_='product-list__cost product-list__description')
                if product_detail_div:
                    price_span = product_detail_div.find('span', class_='product-list__price')

                    if price_span:
                        price_text = price_span.text.strip()
                        price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                        price_numeric = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))
                        price_numeric = Decimal(price_numeric)
                        product = self.repository.get_product_by_link(link)

                        if product:
                            if product.price != price_numeric :
                                print("existing price: ", product.price, '\n', "new price: ", price_numeric)
                                
                                old_price = Decimal(product.price)
                                
                                price_numeric = Decimal(price_numeric)
                                 
                                isInstallment = Decimal(price_numeric) <= Decimal(old_price) * Decimal(0.92) 
                                product.price = Decimal(price_numeric)
                                self.repository.update_product(product)

                                if(isInstallment):
                                    print("installment catched, product link: ", product.link)
                                    installment_rate = ((old_price - Decimal(price_numeric)) / old_price) * 100
                                    old_price = "{:.2f}".format(old_price) 
                                    price_numeric = "{:.2f}".format(price_numeric)
                                    installment_rate = "{:.1f}".format(installment_rate)
                                    message = f"{str(self.base_url) + str(link)} linkli, {product.title} başlıklı ürünün fiyatında indirim oldu. Önceki fiyat: {old_price}, Yeni fiyat: {price_numeric}. İndirim oranı: %{installment_rate}"

                                    await self.telegram_service.send_message(message)
                                   
                                
                            else:
                                print("Product price is remaining the same")
                        else:
                            print("Product not found in the database:", link)
                    else:
                        print("No price span found.")
                else:
                    print("Price box not found on the page:", link)
            else:
                print("Failed to retrieve page:", response.status_code)

        