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
    origin = translator.translate(origin, lang_src='en', lang_tgt='de').strip()
    destination = translator.translate(
        destination, lang_src='en', lang_tgt='de').strip()
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime("%d-%m-%Y")
    try:
        await page.goto('https://www.bahn.de/', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')
    '''
        Feeding elements with DATA !
    '''
    try:
        date_1 = await page.waitForXPath(' //*[@id="js-tab-auskunft"]/div/form/fieldset[1]/div[2]/div[1]/input',
                                         {'visable': True, 'timeout': 5000})
        await date_1.click({'clickCount': 3})
        await date_1.type(date_)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}date_ does not found {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="js-tab-auskunft"] ..."{ENDE}')

    '''
        Locate Fields
    '''
    await page.click('[id=js-auskunft-autocomplete-from]', {'clickCount': 2})
    await page.type('[id=js-auskunft-autocomplete-from]', origin)

    '''
        Wait for promts to appear
    '''
    try:
        departure_choice = await page.waitForXPath(f'//span[contains(text(), "{origin}")]',
                                                   {'visible': True, 'timeout': 5000})
        await departure_choice.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"ORIGIN"{ENDE}')
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
    await page.click('[id=js-auskunft-autocomplete-to]', {'clickCount': 1})
    await page.type('[id=js-auskunft-autocomplete-to]', destination)

    try:
        departure_choice = await page.waitForXPath(f'//span[contains(text(), "{destination}")]',
                                                   {'visible': True, 'timeout': 5000})
        await departure_choice.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"DESTINATION"{ENDE}')
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
    while True:
        try:
            await page.waitForSelector('input[value="Suchen"]', {'visible': True, 'timeout': 5000})
            await page.click('input[value="Suchen"]', {'clickCount': 1})
        except TimeoutError:
            break

    try:
        await page.waitForXPath('//*[@id="resultsOverview"]', {'visible': True, 'timeout': 20000})
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

    while True:
        try:
            find_later_button = await page.waitForXPath('//*[@class="buttonGreyBg later"]',
                                                        {'visible': True, 'timeout': 5000})
            await find_later_button.click()
        except Exception:
            break

    all_items = await page.xpath('//*[@class="boxShadow  scheduledCon "]')

    list_dict = []

    for item in all_items:
        price = await item.querySelector('tbody.boxShadow  span.fareOutput')
        times = await item.querySelectorAll('td[class="time"]')
        dep_time = times[0]
        arr_time = times[1]

        price_text = await page.evaluate('(element) => element.textContent', price)
        dep_time_text = await page.evaluate('(element) => element.textContent', dep_time)
        arr_time_text = await page.evaluate('(element )=> element.textContent', arr_time)

        list_dict.append({
            'date': date,
            'departure_time': dep_time_text.strip(),
            'arrival_time': arr_time_text.strip(),
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
