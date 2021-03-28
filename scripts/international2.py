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
    list_dict = []
    currency = '€'

    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime('%d.%m.%Y')
    try:
        await page.goto('https://www.checkmybus.de/', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    '''
        Checking of cookies
    '''
    cookies_frame = page.frames[0]
    try:
        await cookies_frame.waitForSelector('#gdpr-c-acpt', {'visible': True})
        await cookies_frame.evaluate('''(selector) => document.querySelector(selector).click()''', "#gdpr-c-acpt")
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Cookies not found {ENDE}{INBOX}{LIGHT_BLUE}"#gdpr-c-acpt ..."{ENDE}')

    '''
        Locate Fields
    '''
    try:
        await page.waitForXPath('//*[@id="origincityname"]', {'visible': True, 'timeout': 10000})
        await page.click('[id=origincityname]', {'clickCount': 1})
        await page.type('[id=origincityname]', origin)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="origincityname"] ..."{ENDE}')

    try:
        departure_choice = await page.waitForXPath('//*[@id="searchform"]/fieldset/div/div/div',
                                                   {'visible': True, 'timeout': 50000})
        await departure_choice.click()
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
    await page.click('[id=destinationcityname]', {'clickCount': 1})
    await page.type('[id=destinationcityname]', destination)

    try:
        arrival_choice = await page.waitForXPath('//*[@id="searchform"]/fieldset/div[2]/div/div',
                                                 {'visible': True, 'timeout': 50000})
        await arrival_choice.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Arrival City  {ENDE}{INBOX}{LIGHT_BLUE}"Is Not Valid ..."{ENDE}')
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
        await page.waitForXPath('//*[@id="Date"]', {'visible': True, 'timeout': 50000})
        await page.evaluate('''(selector) => document.querySelector(selector).removeAttribute("readonly")''', "#Date")
        await page.click('[id=Date]', {'clickCount': 3})
        await page.keyboard.press('Backspace')
        await page.type('#Date', date_)
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Date input  {ENDE}{INBOX}{LIGHT_BLUE}"not found ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#execSearch")

    try:
        await page.waitForXPath('//*[@id="searchResults"]', {'visible': True, 'timeout': 50000})
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
        await page.waitForXPath('//div/div/span[contains(@class,"pricePrefix")]', {'visible': True, 'timeout': 50000})
    except Exception:
        logger.error('Timeout')

    time_departure = await page.xpath('//div[contains(@class,"time departure")]')
    time_arrival = await page.xpath('//div[contains(@class,"time arrival")]')

    price = await page.xpath(f'//div/span[contains(text(),"{currency}")]')
    for (i, k, p) in zip(time_departure, time_arrival, price):
        dep_time_txt = await page.evaluate('(element) => element.textContent', i)
        arr_time_txt = await page.evaluate('(element) => element.textContent', k)
        price_txt = await page.evaluate('(element) => element.textContent', p)
        list_dict.append({
            'date': date,
            'departure_time': dep_time_txt,
            'arrival_time': arr_time_txt,
            'price': price_txt.strip()
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
    return (total_data)
