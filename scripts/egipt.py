from datetime import datetime
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from typing import Dict


async def get_info(page, country_id, origin, origin_id, destination, destination_id, total_size, hash_id, order, date,
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

    info = []
    trip1 = None
    trip2 = None
    trip3 = None
    trip4 = None
    list_dict = []
    # date = None
    try:
        await page.goto('https://ask-aladdin.com/egypt-transport-system/bus-timetables/', timeout=200000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    try:
        await page.waitForXPath('//div/div/div/h4/a[contains(@class,"accordion-toggle collapsed")]',
                                {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/div/div/h4/a[contains(@class,"accordion-toggle collapsed")] ..."{ENDE}')

    while True:
        try:
            trip1 = await page.waitForXPath(f'//div/h4/a[contains(text(),"{origin + " " + "to" + " " + destination}")]',
                                            timeout=1000)
        except TimeoutError:
            logger.error(
                f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/h4/a[contains(text() ...1"{ENDE}')

        if trip1:
            await trip1.click()
            break

        elif trip1 is None:
            try:
                trip2 = await page.waitForXPath(
                    f'//div/h4/a[contains(text(),"{"From" + " " + origin + " " + "to" + " " + destination}")]',
                    timeout=1000)
            except TimeoutError:
                logger.error(
                    f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/h4/a[contains(text() ...2"{ENDE}')

        if trip2:
            await trip2.click()
            break

        elif trip2 is None:
            try:
                trip3 = await page.waitForXPath(
                    f'//div/h4/a[contains(text(),"{origin + " " + "to" + " " + "the" + " " + destination}")]',
                    timeout=1000)
            except Exception:
                logger.error('Timeout3')

        if trip3:
            await trip3.click()
            break

        elif trip3 is None:
            try:
                trip4 = await page.waitForXPath(f'//div/h4/a[contains(text(),"{origin + "/" + destination}")]',
                                                timeout=1000)
                await trip4.click()
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
            break

    chosen = await page.xpath('//div/div[@aria-expanded="true"]/div/div/div/table/tbody/tr/td')
    for i in chosen:
        name = await page.evaluate('(element) => element.textContent', i)
        info.append(name)
    company = info[3::3]
    dep_time = info[4::3]
    price = info[5::3]

    for (c, d, p) in zip(company, dep_time, price):
        list_dict.append({
            'date': date,
            'departure_time': d,
            'arrival_time': 'None',
            'price': p
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
