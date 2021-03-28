from datetime import datetime
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from typing import Dict
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from pyppeteer import launch

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
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime("%Y-%m-%d")
    try:
        await page.goto('https://www.darlux.co.tz/home.aspx', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    '''
        Locate Fields
    '''
    try:
        origin_feiled = await page.waitForXPath(
            '//input[@id="from_stn"]',
            {'visible': True, 'timeout': 10000})
        await origin_feiled.click()
        await origin_feiled.type(origin)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//input[@id="from_stn"] ..."{ENDE}')

    try:
        hint_city = await page.waitForXPath(
            f'//li[contains(text(), "{origin.upper()}")]',
            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Departure City Is Not Valid {ENDE}{INBOX}{LIGHT_BLUE}"ORIGIN"{ENDE}')
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
        destination_feiled = await page.waitForXPath(
            '//input[@id="to_stn"]',
            {'visible': True, 'timeout': 10000})
        await destination_feiled.click()
        await destination_feiled.type(destination)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//input[@id="to_stn"] ..."{ENDE}')   

    try:
        hint_city = await page.waitForXPath(
            f'//li[contains(text(), "{destination.upper()}")]',
            {'visible': True, 'timeout': 5000})
        await hint_city.click()
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Arrival City Is Not Valid {ENDE}{INBOX}{LIGHT_BLUE}"DESTINATION"{ENDE}')
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
            '//input[@id="journey_date"]',
            {'visible': True, 'timeout': 10000})
        await dep_date.click({'clickCount': 3})
        await dep_date.type(date_)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE} Not {ENDE}{INBOX}{LIGHT_BLUE}"found date"{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', 'button.btn-primary')

    try:
        await page.waitForXPath('//table[@id="example"]', {'visible': True, 'timeout': 50000})
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
        await page.waitForSelector('select[name="example_length"] option[value="100"]',
                                   {'timeout': 10000})
        await page.select('select[name="example_length"]', '100')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE} Failed {ENDE}{INBOX}{LIGHT_BLUE}"to show more tickets"{ENDE}')
    try:
        all_items = await page.xpath('//*[@id="search_result"]/tr')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE} Tikets {ENDE}{INBOX}{LIGHT_BLUE}"not found"{ENDE}')

    list_dict = []

    for item in all_items:
        tds = await item.querySelectorAll('td')

        if len(tds) > 1:
            price = await page.evaluate('(element) => element.textContent', tds[7])
            dep_time = await page.evaluate('(element) => element.textContent', tds[4])
            arr_time = await page.evaluate('(element) => element.textContent', tds[5])

            price_text = price.strip()
            dep_time_text = dep_time.strip().replace(' Hrs', '')
            arr_time_text = arr_time.strip().replace(' Hrs', '')

            list_dict.append({
                'date': date,
                'departure_time': dep_time_text.strip(),
                'arrival_time': arr_time_text.strip(),
                'price': price_text.strip(),
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
    return total_data
