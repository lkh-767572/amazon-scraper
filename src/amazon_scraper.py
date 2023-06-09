from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import csv


def load_proxies(file):
    """
    load the given proxy file and return all proxies in it
    """
    with open(file, 'r') as f:
        proxies = f.read().splitlines()
    return proxies


def getdata(url, proxies):
    """
    request data with random proxies and return the soup
    """
    while True:
        proxy = random.choice(proxies)
        proxies_dict = {
            'http': 'http://' + proxy,  # Change 'https' to 'http' for the proxy URL
            'https': 'http://' + proxy  # Change 'https' to 'http' for the proxy URL
        }
        try:
            r = s.get(url, headers=headers, proxies=proxies_dict, timeout=timeout)
            r.html.render(sleep=0.1)
            soup = BeautifulSoup(r.html.html, 'html.parser')
            return soup
        except (requests.exceptions.RequestException, ConnectionError) as e:
            print(f"Request error: {e}")
            print("Retrying with a different proxy...")
            proxies.remove(proxy)
            if not proxies:
                print("No more proxies available. Exiting.")
                return None


def getnextpage(soup):
    """
    find the link to the next page and return it. return nothing if no next page.
    """
    pages = soup.find("span", {"class": "s-pagination-strip"})
    if pages:
        next_page = pages.find("a", {
            "class": "s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"})
        if next_page:
            url = f"https://www.amazon.com{next_page['href']}"
            return url
    return None


def get_page_products(soup, keyword):
    """
    get all the product information displayed at search
    """

    product_divs = soup.find_all("div", {"data-component-type": "s-search-result"})
    for product in product_divs:
        asin = product["data-asin"]

        price = product.find("span", {"class": "a-price-whole"})
        price2 = product.find("span", {"class": "a-price-fraction"})
        if price:
            price = price.text
        if price2:
            price2 = price2.text
        price = f"{price}{price2}$"

        link = product.find("a", {"class": "a-link-normal"})["href"]
        link = f"https://www.amazon.com/{link}"

        product_details = search_product(link)

        current_datetime = datetime.now()
        current_date = current_datetime.date()
        # Write the product data to CSV file
        write_product_to_csv({"Title": product_details[3], "Price": price, "Date": current_date, "ASIN": asin,
                              "Rating": product_details[0], "Amazon Best Seller": product_details[1],
                              "Img Link": product_details[2], "Link": link}, keyword)


def search_product(url):
    """
    get all the product data that is displayed at product site
    """

    soup = getdata(url, proxies)

    bsr = ""
    image_url = ""
    rating = ""

    product_title = soup.find("h1", {"id": "title"})
    if product_title:
        product_title = product_title.text
        product_title = product_title.strip()

    image_element = soup.find('img', {'id': 'landingImage'})
    if image_element:
        image_url = image_element['src']

    rating_element = soup.find('div', {'id': 'averageCustomerReviews'})
    if rating_element:
        rating = rating_element.find("span", {"class": "a-size-base a-color-base"})
        if rating:
            rating = rating.text.strip()

    possible_best_seller_label = soup.find_all("th", {"class": "a-color-secondary a-size-base prodDetSectionEntry"})
    if possible_best_seller_label:
        for possible in possible_best_seller_label:
            if possible:
                if possible.text == " Best Sellers Rank ":
                    bsr = possible.find_next_sibling("td").text.strip()

    return [rating, bsr, image_url, product_title]


def write_product_to_csv(product_data, keyword):
    """
    write the scraped data live to csv
    """
    with open(f"{keyword}.csv", 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(product_data.values())


if __name__ == '__main__':
    keyword = str(input("Enter the keyword: "))
    keyword = keyword.replace(" ", "+")  # replace keyword spaces for url

    while True:

        retries = 20  # Number of retries for each page

        s = HTMLSession()
        url = f'https://www.amazon.com/s?k={keyword}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        proxies_file = "http_proxies.txt"
        timeout = 20

        while True:
            proxies = load_proxies(proxies_file)
            data = getdata(url, proxies)

            if data is None:
                retries -= 1
                if retries == 0:
                    break
                continue

            get_page_products(data, keyword)
            url = getnextpage(data)

            if not url:
                break

            retries = 20  # Reset the number of retries for the next page
