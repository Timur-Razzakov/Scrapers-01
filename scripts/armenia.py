import asyncio

from google_trans_new import google_translator
from datetime import datetime

from pyppeteer import launch
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from typing import Dict
from currency_converter import CurrencyConverter


async def get_info(

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
    browser = await launch(headless=False, autoClose=False)
    page = await browser.newPage()

    translator = google_translator()
    origin = translator.translate(origin, lang_src='en', lang_tgt='ru').strip()
    destination = translator.translate(
        destination, lang_src='en', lang_tgt='ru').strip()
    # date_ = datetime.fromisoformat(date)
    # date_ = date_.strftime("%d-%m-%Y")
    try:
        await page.goto('https://www.railway.am/ru/table', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')
    '''
        Function fro select option in select tag
    '''

    async def selected(select, text):
        bool = await page.evaluate(''' 
            (sel, txt) => {
                for (let i = 0; i < sel.length; i++) {
                    if (sel[i].textContent.includes(txt))
                    {   
                        sel[i].selected = true;
                        return true;
                    }
                }
                return false;
            }
        ''', select, text)
        return bool

    try:
        await page.waitForSelector('#country', {'visible': True, 'timeout': 5000})
        await page.select('#country', '1')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"Selector=#country')

    try:
        await page.waitForSelector('#route_names option:nth-child(2)', {'timeout': 10000})
        await page.select('#route_names', '1')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Function not found {ENDE}{INBOX}{LIGHT_BLUE}')

    '''
        Locate Fields
    '''
    try:
        await page.waitForSelector('#From option:nth-child(2)', {'timeout': 10000})
        origin_select = await page.waitForSelector('#From', {'timeout': 10000})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Origin select not found {ENDE}{INBOX}{LIGHT_BLUE}"#From option:nth-child(2) ..."{ENDE}')

    if not (await selected(origin_select, origin)):
        logger.error(f'{DARK_PURPLE}Departure City Is Not Valid')
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
        await page.waitForSelector('#To option:nth-child(2)', {'timeout': 10000})
        destination_select = await page.waitForSelector('#To', {'timeout': 10000})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Destination select not found {ENDE}{INBOX}{LIGHT_BLUE}"#To option:nth-child(2) ..."{ENDE}')

    if not (await selected(destination_select, destination)):
        logger.error(f'{DARK_PURPLE}Arrival City Is Not Valid')
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

    """
        choose the date of departure
    """

    try:
        dep_date = await page.waitForSelector('#datepicker_from',
                                              {'visible': True, 'timeout': 10000})
        await page.evaluate(
            '''(selector) => document.querySelector(selector).removeAttribute("readonly")''',
            '#datepicker_from')
        await dep_date.click({'clickCount': 3})
        await dep_date.type(date)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Date input {ENDE}{INBOX}{LIGHT_BLUE}"not found ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', '#search')

    try:
        await page.waitForXPath('//div[@class="table-responsive"]',
                                {'visible': True, 'timeout': 20000})
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

    try:
        all_items = await page.querySelectorAll('.table tbody')
    except TimeoutError:
        logger.error('Tikets not found')

    list_dict = []

    for item in all_items:
        tds = await item.querySelectorAll('td')

        if len(tds) > 1:
            price = await page.evaluate('(element) => element.textContent', tds[-1])
            dep_time = await page.evaluate('(element) => element.textContent', tds[3])
            arr_time = await page.evaluate('(element) => element.textContent', tds[-3])

            price_text = float(price.strip().replace('драм', '').replace('\xa0', ' ')),
            dep_time_text = dep_time.strip().replace(':00', '')
            arr_time_text = arr_time.strip().replace(':00', '')
            converter = CurrencyConverter()
            for price in price_text:
                price_text = round(converter.convert(price, 'RUB', 'EUR'),2)
            list_dict.append({
                'date': date,
                'departure_time': dep_time_text.strip(),
                'arrival_time': arr_time_text.strip(),
                'price': price_text
            })

        else:
            logger.error(f'{DARK_PURPLE} No {ENDE}{INBOX}{LIGHT_BLUE}"TICKETS FOUND"{ENDE}')
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
    print( total_data)
asyncio.get_event_loop().run_until_complete(
    get_info(origin='Gyumri', country_id=None, origin_id=3, destination='Yerevan ', destination_id=5, date='15.03.2021',
             logger=None,
             total_size=None, order=None, hash_id=None, ))
