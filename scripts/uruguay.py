from datetime import datetime
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from typing import Dict
from google_trans_new import google_translator


async def get_info(
        page: Page,
        country_id: int,
        origin: str,
        origin_id: int,
        destination: str,
        destination_id: int,
        total_size: int,
        hash_id: str,
        order: int,
        date: str,
        logger: Logger) -> Dict:

    """
    The Scraper which built on Pyppeteer. Finds info considering the given params.
    :param page: Page object used to navigate in Tab of Browser.
    :param origin: Starting point for scraping.
    :param destination: Endpoint for scraping.
    :param date: The date to scrape the info for.
    :param logger: Page level logger.
    :param country_id: ID of country being scraped. (Will be used to fetch the country form DB).
    :param origin_id: ID of origin city. Will be used to fetch the city object.
    :param destination_id: ID of destination city.
    :param order: Order of the split (partial) data. (Used in ordering the total data before producing).
    :param hash_id: Hash ID to determine to which data (the original whole data) this split belongs to.
    :param total_size: How many splits we need to collect before being sure that whole data is actually processed.
    :return: Dict
    """

    '''
        Correcting input data
    '''
    translator = google_translator()
    origin = translator.translate(origin, lang_tgt='en').strip()
    destination = translator.translate(
        destination, lang_tgt='en').strip()
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime("%d/%m/%Y")
    try:
        await page.goto('https://www.copsa.com.uy/es/', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    try:
        cookies = await page.waitForSelector('button.close', {'visible': True, 'timeout': 5000})
        await cookies.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Cookies button not found{ENDE}')
    """
        choose the date of departure
    """
    try:
        await page.waitForXPath('//input[@id="go_date"]',{'visible': True, 'timeout': 10000} )
        await page.evaluate('''(selector) => document.querySelector(selector).removeAttribute("readonly")''', "#go_date")
        await page.click('[id=go_date]',{'clickCount': 3})
        await page.keyboard.press('Backspace')
        await page.type('#go_date', date_)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Date input not found{ENDE}')

    '''
        Locate Fields
    '''
    try:
        await page.waitForXPath('//input[@id="ter_from_list"]', {'visible': True, 'timeout': 10000})
        await page.click('#ter_from_list', {'clickCount': 1})
        await page.type('#ter_from_list', origin)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"//input[@id="ter_from_list"] ..."{ENDE}')

    try:
        hint_city = await page.waitForXPath('/html/body/ul[2]/li[1]/a',
                                            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Departure City {ENDE}{INBOX}{LIGHT_BLUE}"Is Not Valid ..."{ENDE}')
        return {
            'country_id': country_id,
            'origin_id': origin_id,
            'destination_id': destination_id,

            'data': [],
            'total_size': total_size,
            'order': order,
            'hash_id': hash_id,
            'status': 400  # No data found
        }

    '''
        Locate Fields
    '''
    try:
        await page.waitForXPath('//input[@id="ter_to_list"]', {'visible': True, 'timeout': 10000})
        await page.click('#ter_to_list', {'clickCount': 1})
        await page.type('#ter_to_list', destination)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//input[@id="ter_to_list"] ..."{ENDE}')

    try:
        hint_city = await page.waitForXPath('/html/body/ul[1]/li/a',
                                            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Arrival City {ENDE}{INBOX}{LIGHT_BLUE}"Is Not Valid ..."{ENDE}')
        return {
            'country_id': country_id,
            'origin_id': origin_id,
            'destination_id': destination_id,

            'data': [],
            'total_size': total_size,
            'order': order,
            'hash_id': hash_id,
            'status': 400  # No data found
        }

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', '.btn-primary ')
    try:
        await page.waitForXPath('//ul[@class="booking-list"]', {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(f'{DARK_PURPLE} No {ENDE}{INBOX}{LIGHT_BLUE}"FINAL RESULTS"{ENDE}')
        return {
            'country_id': country_id,
            'origin_id': origin_id,
            'destination_id': destination_id,

            'data': [],
            'total_size': total_size,
            'order': order,
            'hash_id': hash_id,
            'status': 400  # No data found
        }

    all_items = await page.xpath('//div[@class="booking-item"]')

    list_dict = []

    for item in all_items:
        price = await item.querySelector('.results_buy_button a')
        dep_time = await item.querySelector('div.booking-item div.booking-item-departure > h5:nth-child(2)')
        arr_time = await item.querySelector('div.booking-item div.booking-item-arrival > h5:nth-child(2)')

        price_text = await page.evaluate('(element) => element.textContent', price)
        dep_time_text = await page.evaluate('(element) => element.textContent', dep_time)
        arr_time_text = await page.evaluate('(element) => element.textContent', arr_time)

        list_dict.append({
            'date': date,
            'departure_time': dep_time_text.strip(),
            'arrival_time': arr_time_text.strip(),
            'price': price_text.strip(),
        })
    total_data = {
        'country_id': country_id,
        'origin_id': origin_id,
        'destination_id': destination_id,
        'data': list_dict,
        'total_size': total_size,
        'order': order,
        'hash_id': hash_id,
        'status': 200  # Success
    }
    return total_data
