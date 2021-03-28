from google_trans_new import google_translator
from datetime import datetime
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from typing import Dict

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
    origin = translator.translate(origin, lang_src='en', lang_tgt='ru').strip()
    destination = translator.translate(destination, lang_src='en', lang_tgt='ru').strip()
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime("%d-%m-%Y")
    try:
        await page.goto('https://bilet.railways.kz/', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    '''
        Locate Fields
    '''
    try:
        origin_feiled = await page.waitForSelector(
            '.route-search-form-departure-station input.search',
            {'visible': True, 'timeout': 10000})
        await origin_feiled.click()
        await origin_feiled.type(origin)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}".route-search-form-departure-station  ..."{ENDE}')

    try:
        hint_city = await page.waitForXPath(f'//div[@data-text="{origin.upper()}"]',
                                            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Departure City {ENDE}{INBOX}{LIGHT_BLUE}"Is Not Valid ..."{ENDE}')
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
        destination_feiled = await page.waitForSelector(
            '.route-search-form-arrival-station > input.search',
            {'visible': True, 'timeout': 10000})
        await destination_feiled.click()
        await destination_feiled.type(destination)
    except TimeoutError:
        logger.error(
                f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}".route-search-form-departure-station > ..."{ENDE}')

    try:
        hint_city = await page.waitForXPath(f'//div[@data-text="{destination.upper()}"]',
                                            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Arrival City {ENDE}{INBOX}{LIGHT_BLUE}"Is Not Valid ..."{ENDE}')
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
        dep_date = await page.waitForXPath(
            '//input[@id="route_search_form_forwardDepartureDate"]',
            {'visible': True, 'timeout': 10000})
        await page.evaluate('''(selector) =>
            document.querySelector(selector).value=""
        ''', '#route_search_form_forwardDepartureDate')
        await dep_date.type(date_)
    except TimeoutError:
        pass

    await page.evaluate('''(selector) => document.querySelector(selector).click()''',
                        '[name="route_search_form"] > button')
    try:
        await page.waitForXPath('//div[@class="ui existing segment"]', {'visible': True, 'timeout': 50000})
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
        await page.waitForXPath('//div[@id="forward-direction-trains"]', {'visible': True, 'timeout': 10000})
    except TimeoutError:
        logger.error('Tikets not found')
        

    all_items = await page.xpath('//tr[contains(@class, "item")]')

    list_dict = []

    for item in all_items:
        price = await item.querySelector('h4.ui.apple.header')
        dep_time = await item.querySelector('h2.departure-time')
        arr_time = await item.querySelector('h2.arrival-time')

        price_text = await page.evaluate('(element) => element.textContent', price)
        dep_time_text = await page.evaluate('(element) => element.textContent', dep_time)
        arr_time_text = await page.evaluate('(element) => element.textContent', arr_time)

        list_dict.append({
            'date': date,
            'departure_time': dep_time_text.strip()[:5],
            'arrival_time': arr_time_text.strip()[:5],
            'price': price_text.strip().replace('\xa0', ' '),
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
