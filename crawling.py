import os
import time
import re
import random
import requests
from datetime import datetime
import pandas as pd
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import csv

##### CONFIGURATION #####

base_save_dir = r'E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\data'

WEBSITES = {
    'elise': {
        'url': "https://elise.vn/",
        'category_selectors': {
            'menu_button': "div.action-menu-responsive", 
            'category_links': "li.static-menu.level0 > a, li.category-menu.level0 > a, li.level1 > a",
            'pagination': "div.bottom-pagination > div.toolbar.toolbar-products > div.pages.list-inline > ul.pagination > li.item.current > a, div.pager > div.pages.list-inline > ul.pagination > li.item.current > a",
            'product_container': "ol.products.list.items.product-items.row",
            'products': "li.item.product.product-item-info.product-item.col-xs-12.col-md-6, li.item.product.product-item-info.product-item.col-12.col-xs-6.col-md-4.col-lg-3",
            'product_link': "div.product-top.has > a, div.product-top > a",
            'product_images': "div.product-top.has > a.product.photo.product-item-photo > div.item-xmedia > div.product-image-wrapper > div.image-thumbnail > img, div.product-top > a.product.photo.product-item-photo > div.item-xmedia > div.product-image-wrapper > div.image-thumbnail.product-image-hover > img",
            'next_page': "div.bottom-pagination > div.toolbar.toolbar-products > div.pages.list-inline > ul.pagination > li.item.pages-item-next, div.pager > div.pages.list-inline > ul.pagination > li.item.pages-item-next"
        },
        'detail_selectors': {
            'sku': "div.product.attribute.sku",
            'name': "div.product-name-label h1",
            'sale_label': "span.product-label.sale-label span",
            'price_info': "div.product-info-price",
            'special_price': "span.special-price",
            'old_price': "span.old-price",
            'sizes': "div.swatch-option.text",
            'description': "div.value.std",
            'images': "div.product.item-image.imgzoom img"
        },
        'detail_attempt_fields': ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"],
        'keywords': ["dam", "vay", "ao", "quan", "giay", "tui", "phu-kien"]  
    },
    'pantio': {
        'url': "https://www.pantio.vn/",
        'category_selectors': {
            'category_links': "li.megamenu a, li.dropdown a",
            'pagination': "span.page.page-node.current",
            'products': "div.grid__item.large--one-third.medium--one-third.small--one-half.md-pd-left15, div.product-item",
            'product_link': "div.product-img a",
            'product_images': "div.product-img img",
            'next_page': "span.nextPage"
        },
        'detail_selectors': {
            'sku': "div.pro-sku span.sku-number",
            'name': "h1[itemprop='name']",
            'original_price': "div.pro-price.clearfix span.original-price.ComparePrice",
            'sale_price': "div.pro-price.clearfix span.current-price.ProductPrice",
            'colors_container': "div#variant-swatch-0",
            'color_elements': ".swatch-element",
            'sizes_container': "div#variant-swatch-1",
            'size_elements': ".swatch-element",
            'description': "div.pro-short-desc",
            'images_container': "div.slick-list.draggable",
            'images': "li.product-gallery.slick-slide img.product-image-feature2, div.product-gallery img"
        },
        'detail_attempt_fields': ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
    },
    'ivymoda': {
        'url': "https://ivymoda.com/",
        'category_selectors': {
            'menu': "ul.menu",
            'category_links': "a",
            'pagination': '//*[@id="products_active_ts"]',
            'products': "div.item-cat-product div.product div.thumb-product a, div.product a.product-link, div.product a",
            'next_page': '//li[@class="last-page"]/preceding-sibling::li[1]'
        },
        'detail_selectors': {
            'sku': "div.product-detail__sub-info p span",
            'name': "div.product-detail__information h1",
            'original_price': "div.product-detail__price del",
            'sale_price': "div.product-detail__price b",
            'regular_price': "div.product-detail__price b",
            'sizes': "div.product-detail__size__input span.text-uppercase",
            'tab_buttons': "div.product-detail__tab div.product-detail__tab-header div.tab-item",
            'show_more': "div.product-detail__tab div.product-detail__tab-body div.show-more a",
            'description': "div.product-detail__tab-body div.tab-content.active.showContent",
            'colors': "div.product-detail__color div.product-detail__color__input label span a",
            'color_text': "div.product-detail__color p",
            'images': "div.product-detail__gallery img.lazyloaded, div.product-detail__gallery img"
        },
        'detail_attempt_fields': ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
    }
}

##### UTILITY FUNCTIONS #####

def extract_website_name(url):
    """
    Extract website name from URL, e.g.: 'https://elise.vn/' -> 'elise'
    """
    match = re.search(r"https?://(?:www\.)?([^./]+)", url)
    return match.group(1) if match else "unknown"

def get_timestamp():
    """Get consistent timestamp for naming directories"""
    now = datetime.now()
    return {
        'year': now.strftime("%Y"),
        'month': now.strftime("%m"),
        'day': now.strftime("%d"),
        'hour_minute': now.strftime("%H_%M")
    }

def initialize_directory_structure(base_save_dir, web_url, timestamp=None):
    """
    Create basic directory structure:
    website > year > month > day > hour_minute > list_view | detail_view | CSVs
    """
    if timestamp is None:
        timestamp = get_timestamp()
    
    website_name = extract_website_name(web_url)
    
    website_dir = os.path.join(base_save_dir, website_name)
    os.makedirs(website_dir, exist_ok=True)
    
    list_info_all_path = os.path.join(website_dir, "list_info_all.csv")
    if not os.path.exists(list_info_all_path):
        with open(list_info_all_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["url"])  
    
    year_dir = os.path.join(website_dir, timestamp['year'])
    month_dir = os.path.join(year_dir, timestamp['month'])
    day_dir = os.path.join(month_dir, timestamp['day'])
    time_dir = os.path.join(day_dir, timestamp['hour_minute'])
    
    os.makedirs(year_dir, exist_ok=True)
    os.makedirs(month_dir, exist_ok=True)
    os.makedirs(day_dir, exist_ok=True)
    os.makedirs(time_dir, exist_ok=True)
    
    list_view_dir = os.path.join(time_dir, "list_view")
    detail_view_dir = os.path.join(time_dir, "detail_view")
    
    os.makedirs(list_view_dir, exist_ok=True)
    os.makedirs(detail_view_dir, exist_ok=True)
    
    list_attempt_path = os.path.join(time_dir, "list_attempt.csv")
    list_add_path = os.path.join(time_dir, "list_add.csv")
    list_done_path = os.path.join(time_dir, "list_done.csv")
    detail_attempt_path = os.path.join(time_dir, "detail_attempt.csv")
    
    for path in [list_attempt_path, list_add_path, list_done_path]:
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["url"]) 
    
    fields = WEBSITES[website_name]['detail_attempt_fields']
    
    if not os.path.exists(detail_attempt_path):
        with open(detail_attempt_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
    
    print(f"Initialized directory structure for {website_name}")
    
    return {
        'website_dir': website_dir,
        'time_dir': time_dir,
        'list_view_dir': list_view_dir,
        'detail_view_dir': detail_view_dir,
        'list_attempt_path': list_attempt_path,
        'list_add_path': list_add_path,
        'list_done_path': list_done_path,
        'detail_attempt_path': detail_attempt_path,
        'list_info_all_path': list_info_all_path,
        'timestamp': timestamp,
        'website_name': website_name
    }

def load_csv(file_path):
    """Read data from CSV file and return a set."""
    if not os.path.exists(file_path):
        return set()
    
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None) 
        return {row[0] for row in reader if row and row[0] != "url"}

def append_csv(file_path, data):
    """Save data to CSV file in append mode."""
    file_exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
    
    with open(file_path, "a", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["url"])
        for item in data:
            writer.writerow([item])

def update_product_links(paths, product_links):
    """
    Update CSV files according to process:
    - Add all links to list_attempt
    - Add new links to list_add (links not already in list_info_all)
    - list_info_all is updated separately in scraper functions after successful scraping
    """
    list_info_all = load_csv(paths['list_info_all_path'])
    list_attempt = set(product_links) 
    
    list_add = list_attempt - list_info_all
    
    if list_add:
        append_csv(paths['list_add_path'], list_add)
    
    append_csv(paths['list_attempt_path'], list_attempt)
    
    print(f"Updated CSV files:")
    print(f"- Added {len(list_add)} new links to list_add.csv")
    print(f"- Added {len(list_attempt)} links to list_attempt.csv")
    
    return list_add

def create_collection_directory(list_view_dir, collection_name, pagination_text):
    """
    Create collection_{pagination} directory in list_view
    """
    collection_dir = os.path.join(list_view_dir, f"{collection_name}_{pagination_text}")
    images_dir = os.path.join(collection_dir, "images")
    
    os.makedirs(collection_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    print(f"Created collection directory: {collection_dir}")
    
    return collection_dir, images_dir

def create_category_directory(list_view_dir, category_name, pagination_text):
    """
    Create category_{pagination} directory in list_view
    """
    category_dir = os.path.join(list_view_dir, f"{category_name}_{pagination_text}")
    images_dir = os.path.join(category_dir, "images")
    
    os.makedirs(category_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
        
    return category_dir, images_dir

def create_detail_directory(detail_view_dir, sku, product_name, timestamp=None):
    """
    Create directory in detail_view with structure:
    part_X > {year_month_day_hour_minute}_{sku}_{name}
    """
    if timestamp is None:
        timestamp = get_timestamp()
        
    part_folders = [f for f in os.listdir(detail_view_dir) if f.startswith("part_")]
    
    if not part_folders:
        part_folder = os.path.join(detail_view_dir, "part_1")
        os.makedirs(part_folder, exist_ok=True)
    else:
        part_folder = os.path.join(detail_view_dir, sorted(part_folders)[-1])
        if len(os.listdir(part_folder)) >= 300:
            part_num = len(part_folders) + 1
            part_folder = os.path.join(detail_view_dir, f"part_{part_num}")
            os.makedirs(part_folder, exist_ok=True)
    
    clean_product_name = re.sub(r'[\\/*?:"<>|]', "", product_name.replace(" ", "_"))
    
    time_str = f"{timestamp['year']}_{timestamp['month']}_{timestamp['day']}_{timestamp['hour_minute']}"
    item_folder = os.path.join(part_folder, f"{time_str}_{sku}_{clean_product_name}")
    os.makedirs(item_folder, exist_ok=True)
    
    image_folder = os.path.join(item_folder, "images")
    os.makedirs(image_folder, exist_ok=True)
    
    return item_folder, image_folder

def save_html_source(folder_path, driver, filename="html.txt"):
    """Save current page HTML source to file."""
    html_content = driver.page_source
    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)

##### SITE-SPECIFIC FUNCTIONS #####

##### ELISE FUNCTIONS #####

def save_elise_collection_product_data(folder_path, products, actions):
    """Save product data from Elise collection view and return list of links."""
    image_folder = os.path.join(folder_path, "images")
    
    product_links = []
    
    for product in products:
        try:
            product_element = product.find_element(By.CSS_SELECTOR, "div.product-top a")
            product_href = product_element.get_attribute('href')
            product_links.append(product_href)
            
            try:
                image_name = product.find_element(By.CSS_SELECTOR, "div.product.details.product-item-details h5.product.name.product-item-name").text
                image_name = re.sub(r'[\\/*?:"<>|]', "", image_name.replace(" ", "_")) + ".jpg"
            except:
                image_name = f"product_{len(product_links)}.jpg"
            
            image_element = product.find_element(By.CSS_SELECTOR, "div.product-top img")
            image_url = image_element.get_attribute("src")
            
            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_path = os.path.join(image_folder, image_name)
                    with open(image_path, "wb") as file:
                        file.write(response.content)
        except Exception as e:
            print(f"Error processing collection product")
    
    json_path = os.path.join(folder_path, "data.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(product_links, json_file, ensure_ascii=False, indent=4)
    print(f"Saved Collection JSON: {json_path}")
    
    return product_links

def save_elise_product_data(folder_path, products, actions):
    """Save product data from Elise list view and return list of links."""
    image_folder = os.path.join(folder_path, "images")
    
    product_links = []

    for product in products:
        try:
            actions.move_to_element(product).perform()
            time.sleep(1)
            
            product_element = product.find_element(By.CSS_SELECTOR, "div.product-top.has > a, div.product-top > a")
            product_href = product_element.get_attribute('href')
            product_links.append(product_href)
            
            product_images = product.find_elements(By.CSS_SELECTOR, "div.product-top.has > a.product.photo.product-item-photo > div.item-xmedia > div.product-image-wrapper > div.image-thumbnail > img, div.product-top > a.product.photo.product-item-photo > div.item-xmedia > div.product-image-wrapper > div.image-thumbnail.product-image-hover > img")
            image_counters = {}
            
            for img in product_images:
                img_url = img.get_attribute("src")
                if "data:image" in img_url:  
                    img_url = img.get_attribute("data-src")
                    
                if not img_url or "data:image" in img_url:
                    continue
                
                alt_text = img.get_attribute("alt") or f"product_{len(product_links)}"
                clean_name = re.sub(r'[\\/*?:"<>|]', "", alt_text.replace(" ", "_").replace("-", "_"))
                
                if clean_name not in image_counters:
                    image_counters[clean_name] = 1
                else:
                    image_counters[clean_name] += 1
                
                image_name = f"{clean_name}_{image_counters[clean_name]}.jpg"
                image_path = os.path.join(image_folder, image_name)
                
                try:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        with open(image_path, "wb") as file:
                            file.write(response.content)
                except Exception as e:
                    print(f"Error saving image {img_url}")
                    
        except Exception as e:
            print(f"Error processing product")
    
    json_path = os.path.join(folder_path, "data.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(product_links, json_file, ensure_ascii=False, indent=4)
    print(f"Saved JSON: {json_path}")
    
    return product_links

def scrape_elise_product_detail(driver, product_url, paths):
    """
    Get product details from Elise detail page and save to corresponding directory.
    Update list_done.csv and detail_attempt.csv
    """
    try:
        driver.get(product_url)
        time.sleep(10)
        
        sku_value = driver.find_element(By.CSS_SELECTOR, "div.product.attribute.sku").text.strip()
        name_value = driver.find_element(By.CSS_SELECTOR, "div.product-name-label h1").text.strip()
        
        if ":" in sku_value:
            sku_value = sku_value.split(":")[1].strip()
        
        try:
            sale_value = driver.find_element(By.CSS_SELECTOR, "span.product-label.sale-label span").text
        except:
            sale_value = None
        
        product_info_price = driver.find_element(By.CSS_SELECTOR, "div.product-info-price")
        try:
            special_price_value = product_info_price.find_element(By.CSS_SELECTOR,"span.special-price").text
            old_price_value = product_info_price.find_element(By.CSS_SELECTOR,"span.old-price").text
        except:
            old_price_value = product_info_price.text
            special_price_value = None
        
        size_elements = driver.find_elements(By.CSS_SELECTOR, "div.swatch-option.text")
        sizes_value = "_".join([size.text for size in size_elements])
        
        try:
            description_element = driver.find_element(By.CSS_SELECTOR, "div.value.std")
            description_value = description_element.text.replace("\n", " _ ")
            time.sleep(2)
        except:
            description_value = None
        
        image_urls = []
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div.product.item-image.imgzoom img")
        for image_element in image_elements:
            image_url = image_element.get_attribute('src')
            if image_url:
                image_urls.append(image_url)
        
        item_folder, image_folder = create_detail_directory(
            paths['detail_view_dir'], 
            sku_value, 
            name_value,
            paths['timestamp']
        )
        
        save_html_source(item_folder, driver)
        
        product_data = {
            "sku": sku_value,
            "name": name_value,
            "sale": sale_value,
            "original_price": old_price_value,
            "sale_price": special_price_value,
            "colors": None,  
            "sizes": sizes_value,
            "description": description_value,
            "url": product_url,
            "images": image_urls
        }
        
        json_path = os.path.join(item_folder, "data.json")
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)
        
        for idx, image_url in enumerate(image_urls, start=1):
            image_name = f"{sku_value}_{idx:02}.jpg"
            image_path = os.path.join(image_folder, image_name)
            
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(image_path, "wb") as file:
                        file.write(response.content)
            except Exception as e:
                print(f"Error saving image {image_url}")
        
        append_csv(paths['list_done_path'], [product_url])
        append_csv(paths['list_info_all_path'], [product_url])
        
        detail_attempt_exists = os.path.isfile(paths['detail_attempt_path']) and os.path.getsize(paths['detail_attempt_path']) > 0
        
        with open(paths['detail_attempt_path'], "a", encoding="utf-8", newline='') as f:
            fieldnames = ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not detail_attempt_exists:
                writer.writeheader()
            
            data_to_write = product_data.copy()
            data_to_write["images"] = json.dumps(product_data["images"], ensure_ascii=False)
            
            writer.writerow(data_to_write)
        
        print(f"Successfully scraped product: {name_value} ({sku_value})")
        return True
        
    except Exception as e:
        print(f"Error scraping {product_url}")
        return False

##### PANTIO FUNCTIONS #####

def save_pantio_product_data(folder_path, products, actions):
    """Save product data from Pantio list view and return list of links."""
    image_folder = os.path.join(folder_path, "images")
    
    product_links = []
    
    for product in products:
        try:
            actions.move_to_element(product).perform()
            time.sleep(1)
            
            product_element = product.find_element(By.CSS_SELECTOR, "div.product-img a")
            product_href = product_element.get_attribute('href')
            product_links.append(product_href)
            
            product_images = product.find_elements(By.CSS_SELECTOR, "div.product-img img")
            image_counters = {}
            
            for img in product_images:
                img_url = img.get_attribute("src")
                if "data:image" in img_url:  
                    img_url = img.get_attribute("data-src")
                    
                if not img_url or "data:image" in img_url:
                    continue
                
                alt_text = img.get_attribute("alt") or f"product_{len(product_links)}"
                clean_name = re.sub(r'[\\/*?:"<>|]', "", alt_text.replace(" ", "_").replace("-", "_"))
                
                if clean_name not in image_counters:
                    image_counters[clean_name] = 1
                else:
                    image_counters[clean_name] += 1
                
                image_name = f"{clean_name}_{image_counters[clean_name]}.jpg"
                image_path = os.path.join(image_folder, image_name)
                
                try:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        with open(image_path, "wb") as file:
                            file.write(response.content)
                except Exception as e:
                    print(f"Error saving image {img_url}")
                    
        except Exception as e:
            print(f"Error processing product")
    
    json_path = os.path.join(folder_path, "data.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(product_links, json_file, ensure_ascii=False, indent=4)
    print(f"Saved JSON with {len(product_links)} product links: {json_path}")
    
    return product_links

def scrape_pantio_product_detail(driver, product_url, paths):
    """
    Get product details from Pantio detail page and save to corresponding directory.
    Update list_done.csv and detail_attempt.csv
    """
    try:
        driver.get(product_url)
        time.sleep(5)
        
        try: 
            sku_element = driver.find_element(By.CSS_SELECTOR, 'div.pro-sku span.sku-number')
            sku_value = sku_element.text.strip()
            time.sleep(1)
        except: 
            sku_value = f"unknown_sku_{int(time.time())}"
            print("Không tìm thấy SKU, sử dụng mã tạm thời")
        
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]')
            name_value = name_element.text.strip()
            time.sleep(1)
        except: 
            name_value = f"Unknown Product {int(time.time())}"
            print("Không tìm thấy tên sản phẩm, sử dụng tên tạm thời")
        
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, 'div.pro-price.clearfix span.original-price.ComparePrice')
            original_price_value = price_element.text.strip()
            
            sale_element = driver.find_element(By.CSS_SELECTOR, 'div.pro-price.clearfix span.current-price.ProductPrice')
            sale_price_value = sale_element.text.strip()
        except:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, 'div.pro-price.clearfix span.current-price.ProductPrice')
                original_price_value = price_element.text.strip()
                sale_price_value = None
            except:
                original_price_value = None
                sale_price_value = None
                print("Không tìm thấy thông tin giá")
        
        try:
            swatch_element = driver.find_element(By.ID, 'variant-swatch-0')
            color_elements = swatch_element.find_elements(By.CSS_SELECTOR, '.swatch-element')
            colors_value = [element.get_attribute('data-value') for element in color_elements]
            colors_string = "_".join(colors_value)
        except:
            colors_value = []
            colors_string = None
            print("Không tìm thấy thông tin màu sắc")
        
        try: 
            swatch_element = driver.find_element(By.ID, 'variant-swatch-1')
            size_elements = swatch_element.find_elements(By.CSS_SELECTOR, '.swatch-element')
            sizes_value = [element.get_attribute('data-value') for element in size_elements]
            sizes_string = "_".join(sizes_value)
        except:
            sizes_value = []
            sizes_string = None
            print("Không tìm thấy thông tin kích thước")
        
        try:
            description_element = driver.find_element(By.CSS_SELECTOR, 'div.pro-short-desc')
            description_value = description_element.text.strip().replace("\n", " _ ")
            time.sleep(1)
        except:
            description_value = None
            print("Không tìm thấy mô tả sản phẩm")
        
        image_urls = []
        try:
            list_image_element = driver.find_element(By.CSS_SELECTOR, 'div.slick-list.draggable')
            image_elements = list_image_element.find_elements(By.CSS_SELECTOR, 'li.product-gallery.slick-slide img.product-image-feature2')
            
            for image_element in image_elements:
                image_url = image_element.get_attribute('src')
                if image_url and "data:image" not in image_url:
                    image_urls.append(image_url)
                    
            if not image_urls:
                image_elements = driver.find_elements(By.CSS_SELECTOR, 'div.product-gallery img')
                for image_element in image_elements:
                    image_url = image_element.get_attribute('src')
                    if image_url and "data:image" not in image_url:
                        image_urls.append(image_url)
        except Exception as e:
            print(f"Lỗi khi lấy ảnh sản phẩm")
        
        item_folder, image_folder = create_detail_directory(
            paths['detail_view_dir'], 
            sku_value, 
            name_value,
            paths['timestamp']
        )
        
        save_html_source(item_folder, driver)
        
        product_data = {
            "sku": sku_value,
            "name": name_value,
            "sale": None, 
            "original_price": original_price_value,
            "sale_price": sale_price_value,
            "colors": colors_string,
            "sizes": sizes_string,
            "description": description_value,
            "url": product_url,
            "images": image_urls
        }
        
        json_path = os.path.join(item_folder, "data.json")
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)
        
        for idx, image_url in enumerate(image_urls, start=1):
            image_name = f"{sku_value}_{idx:02}.jpg"
            image_path = os.path.join(image_folder, image_name)
            
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(image_path, "wb") as file:
                        file.write(response.content)
            except Exception as e:
                print(f"Error saving image {image_url}")
        
        append_csv(paths['list_done_path'], [product_url])
        append_csv(paths['list_info_all_path'], [product_url])
        
        detail_attempt_exists = os.path.isfile(paths['detail_attempt_path']) and os.path.getsize(paths['detail_attempt_path']) > 0
        
        with open(paths['detail_attempt_path'], "a", encoding="utf-8", newline='') as f:
            fieldnames = ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not detail_attempt_exists:
                writer.writeheader()
            
            data_to_write = product_data.copy()
            data_to_write["images"] = json.dumps(product_data["images"], ensure_ascii=False)
            
            writer.writerow(data_to_write)
        
        print(f"Successfully scraped product: {name_value} ({sku_value})")
        return True
        
    except Exception as e:
        print(f"Error scraping {product_url}")
        return False


##### IVYMODA FUNCTIONS #####

def save_ivymoda_product_data(folder_path, products, actions):
    """Save product data from IvyModa list view and return list of links."""
    image_folder = os.path.join(folder_path, "images")
    
    product_links = []
    
    for product in products:
        try:
            actions.move_to_element(product).perform()
            
            product_href = product.get_attribute('href')
            if product_href:
                product_links.append(product_href)
                
                parent_product = product.find_element(By.XPATH, "./..")
                product_images = parent_product.find_elements(By.CSS_SELECTOR, "img")
                
                image_counters = {}
                
                for img in product_images:
                    img_url = img.get_attribute("src") or img.get_attribute("data-original")
                    if not img_url or "data:image" in img_url:
                        continue
                    
                    alt_text = img.get_attribute("alt") or f"product_{len(product_links)}"
                    clean_name = re.sub(r'[\\/*?:"<>|]', "", alt_text.replace(" ", "_").replace("-", "_"))
                    
                    if clean_name not in image_counters:
                        image_counters[clean_name] = 1
                    else:
                        image_counters[clean_name] += 1
                    
                    image_name = f"{clean_name}_{image_counters[clean_name]}.jpg"
                    image_path = os.path.join(image_folder, image_name)
                    
                    try:
                        response = requests.get(img_url)
                        if response.status_code == 200:
                            with open(image_path, "wb") as file:
                                file.write(response.content)
                    except Exception as e:
                        print(f"Error saving image {img_url}")
        except Exception as e:
            print(f"Error processing product")
    
    json_path = os.path.join(folder_path, "data.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(product_links, json_file, ensure_ascii=False, indent=4)
    print(f"Saved JSON with {len(product_links)} product links: {json_path}")
    
    return product_links

def scrape_ivymoda_product_detail(driver, product_url, paths):
    """
    Get product details from IvyModa detail page and save to corresponding directory.
    Update list_done.csv and detail_attempt.csv
    """
    try:
        driver.get(product_url)
        time.sleep(5)
        
        actions = ActionChains(driver)
        
        try: 
            sku_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__sub-info p span')
            sku_value = sku_element.text.strip()
            time.sleep(1)
        except Exception as e: 
            print(f"Error getting SKU")
            sku_value = f"unknown_sku_{int(time.time())}"
        
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__information h1')
            name_value = name_element.text.strip()
            time.sleep(1)
        except Exception as e: 
            print(f"Error getting name")
            name_value = f"Unknown Product {int(time.time())}"
        
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__price del')
            original_price_value = price_element.text.strip()
            
            sale_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__price b')
            sale_price_value = sale_element.text.strip()
        except:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__price b')
                original_price_value = price_element.text.strip()
                sale_price_value = None
            except Exception as e:
                print(f"Error getting price")
                original_price_value = None
                sale_price_value = None
        
        try:
            size_elements = driver.find_elements(By.CSS_SELECTOR, 'div.product-detail__size__input span.text-uppercase')
            sizes_value = [element.text for element in size_elements]
            sizes_string = "_".join(sizes_value)
        except Exception as e:
            print(f"Error getting sizes")
            sizes_value = []
            sizes_string = None
        
        introduction_value = []
        try:
            description_buttons = driver.find_elements(By.CSS_SELECTOR, 'div.product-detail__tab div.product-detail__tab-header div.tab-item')
            for description_button in description_buttons: 
                actions.move_to_element(description_button).click().perform()
                time.sleep(2)
                
                try:
                    show_more_button = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__tab div.product-detail__tab-body div.show-more a')
                    actions.move_to_element(show_more_button).click().perform()
                    time.sleep(2)
                except:
                    pass
                
                introduction_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__tab-body div.tab-content.active.showContent')
                
                p_elements = introduction_element.find_elements(By.TAG_NAME, 'p')
                tr_elements = introduction_element.find_elements(By.TAG_NAME, 'tr')                
                all_elements = p_elements + tr_elements
                
                value = [element.text for element in all_elements]
                introduction_value.extend(value)
        except Exception as e:
            print(f"Error getting description")
        
        description_value = " _ ".join([text for text in introduction_value if text.strip()]) if introduction_value else None
        
        color_values = []
        image_urls = []
        
        try: 
            image_elements_current = driver.find_elements(By.CSS_SELECTOR, 'div.product-detail__gallery img.lazyloaded, div.product-detail__gallery img')
            for image_element in image_elements_current:
                image_url = image_element.get_attribute('src') or image_element.get_attribute('data-src')
                if image_url and not "data:image" in image_url and image_url not in image_urls:
                    image_urls.append(image_url)
            
            button_color_elements = driver.find_elements(By.CSS_SELECTOR, 'div.product-detail__color div.product-detail__color__input label span a')
            for button_color_element in button_color_elements:
                color_href = button_color_element.get_attribute('href')
                if not color_href:
                    continue
                
                print(f"Checking color variant: {color_href}")
                
                driver.execute_script(f"window.open('{color_href}');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(5)
                
                try:
                    color_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail__color p')
                    color_value = color_element.text
                    color_values.append(color_value)
                    
                    image_elements = driver.find_elements(By.CSS_SELECTOR, 'div.product-detail__gallery img.lazyloaded, div.product-detail__gallery img')
                    for image_element in image_elements:
                        image_url = image_element.get_attribute('src') or image_element.get_attribute('data-src')
                        if image_url and not "data:image" in image_url and image_url not in image_urls:
                            image_urls.append(image_url)
                except Exception as e:
                    print(f"Error getting color info")
                
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(1)
        except Exception as e:
            print(f"Error getting colors and images")
        
        colors_string = "_".join(color_values) if color_values else None
        
        item_folder, image_folder = create_detail_directory(
            paths['detail_view_dir'], 
            sku_value, 
            name_value,
            paths['timestamp']
        )
        
        save_html_source(item_folder, driver)
        
        product_data = {
            "sku": sku_value,
            "name": name_value,
            "sale": None,  
            "original_price": original_price_value,
            "sale_price": sale_price_value,
            "colors": colors_string,
            "sizes": sizes_string,
            "description": description_value,
            "url": product_url,
            "images": image_urls
        }
        
        json_path = os.path.join(item_folder, "data.json")
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)
        
        for idx, image_url in enumerate(image_urls, start=1):
            image_name = f"{sku_value}_{idx:02}.jpg"
            image_path = os.path.join(image_folder, image_name)
            
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(image_path, "wb") as file:
                        file.write(response.content)
            except Exception as e:
                print(f"Error saving image {image_url}")
        
        append_csv(paths['list_done_path'], [product_url])
        append_csv(paths['list_info_all_path'], [product_url])
        
        detail_attempt_exists = os.path.isfile(paths['detail_attempt_path']) and os.path.getsize(paths['detail_attempt_path']) > 0
        
        with open(paths['detail_attempt_path'], "a", encoding="utf-8", newline='') as f:
            fieldnames = ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not detail_attempt_exists:
                writer.writeheader()
            
            data_to_write = product_data.copy()
            data_to_write["images"] = json.dumps(product_data["images"], ensure_ascii=False)
            
            writer.writerow(data_to_write)
        
        print(f"Successfully scraped product: {name_value} ({sku_value})")
        return True
        
    except Exception as e:
        print(f"Error scraping {product_url}")
        return False

##### CRAWLER FUNCTIONS #####

def crawl_elise_categories(timestamp=None):
    """Crawl all product links from Elise categories"""
    if timestamp is None:
        timestamp = get_timestamp()
        
    website_config = WEBSITES['elise']
    web_url = website_config['url']
    
    paths = initialize_directory_structure(base_save_dir, web_url, timestamp)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    time.sleep(5)
    
    driver.get(web_url)
    time.sleep(5)
    
    try: 
        close_button = driver.find_element(By.CSS_SELECTOR, "div[id='close-button-1454703513200']")
        actions = ActionChains(driver)
        actions.move_to_element(close_button).click().perform()
    except:
        print("Không có thông báo popup")
    
    actions = ActionChains(driver)
    
    menu_button = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['menu_button'])
    actions.move_to_element(menu_button).perform()
    time.sleep(3)
    
    categorys = driver.find_elements(By.CSS_SELECTOR, website_config['category_selectors']['category_links'])
    keywords = website_config['keywords']
    pattern = r"/([^/]+?)(?:\.html)?$"
    
    for category in categorys:
        category_href = category.get_attribute('href')
        
        if any(keyword in category_href for keyword in keywords):
            match = re.search(pattern, category_href)
            category_name = match.group(1) if match else "unknown"
            
            print(f"Opening: {category_href} (Category: {category_name})")
            
            driver.execute_script(f"window.open('{category_href}');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            while True:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['pagination'])
                    pagination_text = pagination.text
                except:
                    pagination_text = "1"
                
                print(f"Processing: {category_name} - Page {pagination_text}")
                
                category_dir, _ = create_category_directory(paths['list_view_dir'], category_name, pagination_text)
                
                save_html_source(category_dir, driver)
                
                main = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['product_container'])
                products = main.find_elements(By.CSS_SELECTOR, website_config['category_selectors']['products'])
                
                product_links = save_elise_product_data(category_dir, products, actions)
                
                update_product_links(paths, product_links)
                
                try:
                    next_page = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['next_page'])
                    
                    actions.move_to_element(next_page).click().perform()
                    time.sleep(3) 
                except:
                    print(f"Đã hoàn thành cào danh mục: {category_name}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    break
    
    print("Hoàn thành quá trình cào tất cả links sản phẩm Elise")
    driver.quit()
    
    return paths

def crawl_elise_lookbooks(paths=None, timestamp=None):
    """Crawl all product links from Elise lookbooks"""
    if timestamp is None:
        timestamp = get_timestamp()
        
    if paths is None:
        paths = initialize_directory_structure(base_save_dir, WEBSITES['elise']['url'], timestamp)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    time.sleep(5)
    
    lookbook_url = f"{WEBSITES['elise']['url'].rstrip('/')}/lookbook"
    driver.get(lookbook_url)
    time.sleep(5)
    
    actions = ActionChains(driver)
    
    visited_collections = set()
    collection_page = 1 
    
    while True:    
        collections = driver.find_elements(By.CSS_SELECTOR, "li.item-lookbook")
        print(f"Found {len(collections)} collections on page {collection_page}")
        
        for index, collection in enumerate(collections):
            if index > 100:
                break
            try:
                url_element = collection.find_element(By.CSS_SELECTOR, "div.item-image a")
                url_value = url_element.get_attribute('href')
                
                if url_value in visited_collections:
                    continue
                
                visited_collections.add(url_value)
                
                name_element = collection.find_element(By.CSS_SELECTOR, "div.item-content-info div.content h1")
                name_value = name_element.text
                clean_name = re.sub(r'[\\/*?:"<>|]', "", name_value.replace(" ", "_"))
                
                print(f"Processing collection ({index+1}/{len(collections)}): {name_value} - {url_value}")
                
                driver.execute_script(f"window.open('{url_value}');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)
                
                collection_dir, _ = create_collection_directory(paths['list_view_dir'], clean_name, "1")
                
                save_html_source(collection_dir, driver)
                
                products = driver.find_elements(By.CSS_SELECTOR, "div.item div.item-content-wrapper")
                print(f"Found {len(products)} products in collection: {name_value}")
                
                product_links = save_elise_collection_product_data(collection_dir, products, actions)
                
                update_product_links(paths, product_links)
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing collection")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        
        try:
            see_more = driver.find_element(By.CSS_SELECTOR, "div.lookbook-actions span.button")
            driver.execute_script("arguments[0].scrollIntoView(true);", see_more)
            time.sleep(1)
            see_more.click()
            print("Clicked 'Xem thêm' button")
            time.sleep(3)  
            collection_page += 1
        except Exception as e:
            print(f"Không tìm thấy nút 'Xem thêm' hoặc đã hết collections")
            break
    
    print(f"Hoàn thành quá trình cào collections, đã cào {len(visited_collections)} bộ sưu tập")
    driver.quit()
    
    return paths

def crawl_detail_products(paths, scraper_function):
    """
    Generic function to crawl product details
    Only scrapes links that are not already in list_info_all
    Closes and reopens Chrome browser for each product detail to avoid memory issues
    """
    list_add_path = paths['list_add_path']
    list_info_all_path = paths['list_info_all_path']
    
    links_to_scrape = load_csv(list_add_path)
    links_info_all = load_csv(list_info_all_path)
    
    links_to_scrape = links_to_scrape - links_info_all
    
    if not links_to_scrape:
        print("Không có links mới cần cào chi tiết")
        return
    
    print(f"Bắt đầu cào chi tiết cho {len(links_to_scrape)} sản phẩm mới")
    
    # for i, link in enumerate(links_to_scrape):
    #     print(f"Cào chi tiết sản phẩm {i+1}/{len(links_to_scrape)}: {link}")
        
    #     driver = webdriver.Chrome(options=options)
    #     driver.maximize_window()
    #     time.sleep(15) 
        
    #     success = scraper_function(driver, link, paths)
        
    #     if success:
    #         print(f"Hoàn thành cào chi tiết: {link}")
    #     else:
    #         print(f"Thất bại khi cào chi tiết: {link}")
        
    #     driver.quit()
        
    #     time.sleep(3)
    
    # print(f"Hoàn thành cào chi tiết cho {len(links_to_scrape)} sản phẩm")

    ############################################################################
    links_list = list(links_to_scrape)
    if links_list:
        link = links_list[0]
        print(f"Cào chi tiết sản phẩm 1/{len(links_to_scrape)}: {link}")
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        time.sleep(15)
        success = scraper_function(driver, link, paths)
        if success:
            print(f"Hoàn thành cào chi tiết: {link}")
        else:
            print(f"Thất bại khi cào chi tiết: {link}")
        driver.quit()
        print(f"Hoàn thành cào chi tiết cho sản phẩm")
        ############################################################################

def crawl_pantio_categories(timestamp=None):
    """Crawl all product links from Pantio categories"""
    if timestamp is None:
        timestamp = get_timestamp()
        
    website_config = WEBSITES['pantio']
    web_url = website_config['url']
    
    paths = initialize_directory_structure(base_save_dir, web_url, timestamp)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    time.sleep(5)
    
    driver.get(web_url)
    time.sleep(5)
    
    actions = ActionChains(driver)
    
    categorys = driver.find_elements(By.CSS_SELECTOR, website_config['category_selectors']['category_links'])
    
    for index, category in enumerate(categorys):
        if index > 100: 
            break
        category_href = category.get_attribute('href')
        if 'collections' in category_href:
            pattern = r"collections/([^/?#]+)"
            match = re.search(pattern, category_href)
            if match:
                category_name = match.group(1).replace("-", "_")
            else:
                category_name = re.sub(r'[\\/*?:"<>|]', "", category_href.replace(" ", "_").replace("-", "_"))
            
            print(f"Opening: {category_href} (Category: {category_name})")
            
            driver.execute_script(f"window.open('{category_href}');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(5)
            
            has_next_page = True
            
            while has_next_page:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['pagination'])
                    pagination_text = pagination.text
                except:
                    pagination_text = "1"
                
                print(f"Processing: {category_name} - Page {pagination_text}")
                
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                category_dir, _ = create_category_directory(paths['list_view_dir'], category_name, pagination_text)
                
                save_html_source(category_dir, driver)
                
                products = driver.find_elements(By.CSS_SELECTOR, website_config['category_selectors']['products'])
                
                if products:
                    product_links = save_pantio_product_data(category_dir, products, actions)
                    
                    update_product_links(paths, product_links)
                else:
                    print(f"Không tìm thấy sản phẩm nào trong trang {pagination_text}")
                
                try:
                    next_page = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['next_page'])
                    actions.move_to_element(next_page).click().perform()
                    time.sleep(5) 
                except Exception as e:
                    print(f"Không tìm thấy nút next page hoặc đã hết trang")
                    has_next_page = False
            
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
    driver.quit()
    
    return paths

def crawl_ivymoda_categories(timestamp=None):
    """Crawl all product links from IvyModa categories"""
    if timestamp is None:
        timestamp = get_timestamp()
        
    website_config = WEBSITES['ivymoda']
    web_url = website_config['url']
    
    paths = initialize_directory_structure(base_save_dir, web_url, timestamp)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    time.sleep(5)
    
    driver.get(web_url)
    time.sleep(5)
    
    try:  
        close_button = driver.find_element(By.CSS_SELECTOR, "div.popup-content div.action-close")
        actions = ActionChains(driver)
        actions.move_to_element(close_button).click().perform()
        time.sleep(1)
    except:
        print("Không có thông báo nào.")
    
    actions = ActionChains(driver)
    
    menu_element = driver.find_element(By.CSS_SELECTOR, website_config['category_selectors']['menu'])
    categorys = menu_element.find_elements(By.TAG_NAME, website_config['category_selectors']['category_links'])
    
    for index,category in enumerate(categorys):
        if index > 100:  
            category_href = category.get_attribute('href')
            if category_href and ('danh-muc' in category_href or 'lookbook' in category_href):
                pattern = r"(?:danh-muc|lookbook)/([^/?#]+)"
                match = re.search(pattern, category_href)
                
                if match:
                    category_name = match.group(1).replace("-", "_")
                else:
                    category_text = category.text.strip()
                    category_name = re.sub(r'[\\/*?:"<>|]', "", category_text.replace(" ", "_").replace("-", "_"))
                
                print(f"Opening: {category_href} (Category: {category_name})")
                
                driver.execute_script(f"window.open('{category_href}');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(5)
                
                page = 1
                has_next_page = True
                
                while has_next_page:
                    try:
                        pagination = driver.find_element(By.XPATH, website_config['category_selectors']['pagination'])
                        pagination_text = pagination.text
                    except:
                        pagination_text = str(page)
                    
                    print(f"Processing: {category_name} - Page {pagination_text}")
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    category_dir, _ = create_category_directory(paths['list_view_dir'], category_name, pagination_text)
                    
                    save_html_source(category_dir, driver)
                    
                    products = driver.find_elements(By.CSS_SELECTOR, website_config['category_selectors']['products'])
                    
                    if products:
                        product_links = save_ivymoda_product_data(category_dir, products, actions)
                        
                        update_product_links(paths, product_links)
                    else:
                        print(f"Không tìm thấy sản phẩm nào trong trang {pagination_text}")
                    
                    try:
                        next_page = driver.find_element(By.XPATH, website_config['category_selectors']['next_page'])
                        actions.move_to_element(next_page).click().perform()
                        page += 1
                        time.sleep(5) 
                    except Exception as e:
                        print(f"Không tìm thấy nút next page hoặc đã hết trang")
                        has_next_page = False
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
    driver.quit()
    return paths

##### CHROME OPTIONS #####

options = Options()
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
prefs = {
    "credentials_enable_service": False, 
    "profile.password_manager_enabled": False, 
}
options.add_experimental_option("prefs", prefs)

##### MAIN FUNCTION #####

def main():
    """
    Main function to execute all scraping processes in sequence:
    1. Elise categories
    2. Elise lookbooks 
    3. Elise product details
    4. Pantio categories
    5. Pantio product details
    6. IvyModa categories
    7. IvyModa product details
    """
    print("===== Bắt đầu quá trình cào dữ liệu tổng hợp =====")
    
    timestamp = get_timestamp()
    
    # print("\n===== Crawling Elise Categories =====")
    # elise_paths = crawl_elise_categories(timestamp)
    
    # print("\n===== Crawling Elise Lookbooks =====")
    # crawl_elise_lookbooks(elise_paths, timestamp)
    
    # print("\n===== Crawling Elise Product Details =====")
    # crawl_detail_products(elise_paths, scrape_elise_product_detail)
    
    print("\n===== Crawling Pantio Categories =====")
    pantio_paths = crawl_pantio_categories(timestamp)
    
    print("\n===== Crawling Pantio Product Details =====")
    crawl_detail_products(pantio_paths, scrape_pantio_product_detail)
    
    print("\n===== Crawling IvyModa Categories =====")
    ivymoda_paths = crawl_ivymoda_categories(timestamp)
    
    print("\n===== Crawling IvyModa Product Details =====")
    crawl_detail_products(ivymoda_paths, scrape_ivymoda_product_detail)
    
    print("\n===== Hoàn thành toàn bộ quá trình cào dữ liệu tổng hợp! =====")

if __name__ == "__main__":
    main()