import asyncio
import logging
import requests
from bs4 import BeautifulSoup
import threading

from data.entities.product import Product
from data.repositories.productRepository import ProductRepository
from service.productService import ProductService
from service.telegramService import TelegramService

import requests

class LoggingConfigurator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler('application.log')
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

class GatherPagesItems(LoggingConfigurator):
    def __init__(self, product_repo,url):
        self.base_url=url
        self.page_count=0
        self.item_count=0
        self.product_repo = product_repo

    async def gather_page_number(self, base_url, i):
        try:
            response = requests.get(base_url + str(i))
            
            if response.status_code == 200:
                print("Page retrieved")
                soup = BeautifulSoup(response.content, 'html.parser')
                conteiner = soup.find('div', class_="wrapper-product-main")
                products = conteiner.find_all('div',class_="product-list product-list--list-page")
                
                for div in products:
                    product_name = div.find('div', class_='product-list__product-name')
                    h3 = product_name.find('h3')
                    prc_box_dscntd = div.find('span', class_='product-list__price')
                    a = div.find('a',"product-list__image-safe-link sld")
                    
            
                    if h3 and a:
                        title = h3.get_text(strip=True)
                        
                        href = a['href']
                        

                        item =  self.product_repo.get_product_by_link(href)
                        price_text = prc_box_dscntd.text.strip()
                        price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                        price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))                        
                        
                        if item is False:
                            product = Product(id=None,title=title, link=href, price=price)
                            self.product_repo.add_product(product)                    

                    else:
                        
                        print("Incomplete data found in div, skipping.")
                
                div_count = len(products)
                if div_count != 24:
                    self.item_count = (i * 24) + div_count
                    self.page_count = i
                    return False
            else:
                print("Failed to retrieve page:", response.status_code)
                
                return False
        except Exception as err:
            print("Error occurred:", err)
            return False
        
        return True

    async def gather_page_numbers(self):
        base_url = self.base_url
        loop_var = True
        i = 1
        while loop_var:
            
            #threads = []
            #for _ in range(50):
            #    t = threading.Thread(target=self.gather_page_number, args=(base_url, i))
            #    t.start()
            #    threads.append(t)
            #    i += 1
            #for t in threads:
            #    t.join()

            loop_var = await self.gather_page_number(base_url, i)
            i = i + 1

async def Main():
    product_repo = ProductRepository()

    smartphones = GatherPagesItems(product_repo,"https://www.vatanbilgisayar.com/akilli-telefon/?page=")
    
    await smartphones.gather_page_numbers()

    #dysonproducts = GatherPagesItems(product_repo,"https://www.trendyol.com/dyson-dik-supurge-x-b102989-c109454?pi=")
    #await dysonproducts.gather_page_numbers()
    
    telegram_service = TelegramService(bot_token='7393980187:AAGJHwoW6DY98jZOvTzdq0o7Ojt8X1VO28Q', chat_id='-1002203530212')

    productService = ProductService(product_repo, telegram_service)
    
    while True:
        await productService.updateProduct()

asyncio.run(Main())