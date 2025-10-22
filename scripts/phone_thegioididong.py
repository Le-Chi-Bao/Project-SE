import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import random

service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service)

driver.get('https://www.thegioididong.com/dtdd#c=42&o=13&pi=6')
sleep(random.randint(5, 10))


#-------------------Trang chủ danh sách Sản Phẩm -----------------

#------------ ID / LINK / NAME / BRAND / PRICE / DISCOUNT_PERCENT
items = driver.find_elements(By.CSS_SELECTOR, '.main-contain[href]')
elements = driver.find_elements(By.CSS_SELECTOR, '.rating_Compare.has_compare.has_quantity')
data = []
links = []

for i in range(len(items)):
    try:
        item = items[i]
        product_id = item.get_attribute('data-id')
        link = item.get_attribute('href')
        title = item.get_attribute('data-name')
        brand = item.get_attribute('data-brand')
        price = item.get_attribute('data-price')    
        
        # discount_percent
        try:
            discount_percent = item.find_element(By.CSS_SELECTOR, '.percent').text 
        except NoSuchElementException:
            discount_percent = "NaN"
            
        #----------RATING / QUANTITY ----------
        try:
            element = elements[i]
            try:
                rating = element.find_element(By.CSS_SELECTOR, '.vote-txt').text 
            except NoSuchElementException:
                rating = "NaN"
            
            try:
                sold_quantity = element.find_element(By.TAG_NAME, 'span').text
            except NoSuchElementException:
                sold_quantity = "NaN"
        except Exception as e:
            print(f"Error processing rating & quantity: {e}")

        data.append([product_id, link, title, brand, price, discount_percent, rating, sold_quantity])
        links.append(link)
        
    except Exception as e:
        print(f"Error processing item: {e}")
        continue


df_products = pd.DataFrame(data, columns=[
    'ID', 'Link', 'Name', 'Brand', 'Discounted Price', 
    'Discounted Percent', 'Rating', 'SoldQuantity'
])     


#-------------------Chi tiết từng Sản phẩm--------------
all_specs = []

for idx, link in enumerate(links): 
    try:
        driver.get(link)
        sleep(random.randint(2, 4))

        product_specs = {
            'Link': link,
            'ID': data[idx][0],
            'Name': data[idx][2],
            'RAM': 'NaN',
            'ROM': 'NaN',
            'Battery': 'NaN',
            'BackCamera': 'NaN',
            'FrontCamera': 'NaN',
            'GPU': 'NaN',
            'ChargingPort': 'NaN',
            'Resolution': 'NaN',
            'ScreenSize': 'NaN',
            'WarrantyDuration': 'NaN',
            'NumberOfReview': 'NaN',
            'Description': 'NaN'
        }

        #Bảo hành
        try:
            warrantys = driver.find_element(By.CSS_SELECTOR, '.policy__list')
            warranty = warrantys.find_elements(By.TAG_NAME, 'li')[-1].text
            product_specs['WarrantyDuration'] = warranty
        except NoSuchElementException:
            pass

        # Number of review
        try:
            number_of_review = driver.find_element(By.CSS_SELECTOR, '.point-alltimerate').text
            product_specs['NumberOfReview'] = number_of_review
        except NoSuchElementException:
            pass
        #Thông số chi tiết
        try:
            spec_tabs = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.box-specifi > a')))

            for tab in spec_tabs:
                try:
                    ActionChains(driver).move_to_element(tab).click().perform()
                    sleep(0.5)

                    spec_items = driver.find_elements(By.CSS_SELECTOR, '.text-specifi.active li')

                    for item in spec_items:
                        try:
                            label = item.find_element(By.CSS_SELECTOR, 'aside:first-child').text.strip()
                            value = item.find_element(By.CSS_SELECTOR, 'aside:last-child').text.strip()

                            if 'RAM:' in label:
                                product_specs['RAM'] = value
                            elif 'Dung lượng lưu trữ:' in label:
                                product_specs['ROM'] = value
                            elif 'Dung lượng pin:' in label:
                                product_specs['Battery'] = value
                            elif 'Độ phân giải camera sau:' in label:
                                product_specs['BackCamera'] = value
                            elif 'Độ phân giải camera trước' in label:
                                product_specs['FrontCamera'] = value
                            elif 'Chip đồ họa (GPU)' in label:
                                product_specs['GPU'] = value
                            elif 'Cổng kết nối/sạc' in label:
                                product_specs['ChargingPort'] = value
                            elif 'Độ phân giải màn hình' in label:
                                product_specs['Resolution'] = value
                            elif 'Màn hình rộng' in label:
                                product_specs['ScreenSize'] = value.split('"')[0].strip()
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    print(f"Error processing tab: {e}")
                    continue
        except:
            print("Couldn't find specification tabs")

        all_specs.append(product_specs)

    except Exception as e:
        print(f"Error processing product page: {e}")
        continue

df_specs = pd.DataFrame(all_specs)

#-----------Description--------------
for idx, row in df_specs.iterrows():
    link = row['Link']
    try:
        driver.get(link)
        sleep(random.randint(2, 4))

        review_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="tab-spec"]/h2[2]'))
        )
        review_tab.click()
        sleep(1)

        h3_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tab-2 .text-detail h3"))
        )
        h3_contents = h3_element.text.strip()
        df_specs.at[idx, 'Description'] = h3_contents if h3_contents else "NaN"

    except Exception as e:
        print(f"Error getting description for {link}: {e}")
        df_specs.at[idx, 'Description'] = "NaN"

# Merge all data
df_combined = pd.merge(df_products, df_specs, on=['ID', 'Link', 'Name'], how='left')

final_columns = [
    'ID', 'Link', 'Name', 'Brand', 'Discounted Price', 'Discounted Percent',
    'Rating', 'SoldQuantity', 'RAM', 'ROM', 'Battery', 'BackCamera',
    'FrontCamera', 'GPU', 'ChargingPort', 'Resolution', 'ScreenSize', 'NumberOfReview',
    'WarrantyDuration', 'Description'
]

df_final = df_combined[final_columns]

df_final.to_csv('phone_thegioididong.csv', index=False, encoding='utf-8-sig')

driver.quit()
print("Completed! Data saved")


