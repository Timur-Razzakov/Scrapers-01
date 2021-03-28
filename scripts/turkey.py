from datetime import datetime
from pyppeteer.page import PageError, Page
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from pyppeteer.errors import TimeoutError
from logging import Logger
from typing import Dict


async def get_info(page,country_id,origin,origin_id, destination,destination_id,total_size,hash_id,order,date,logger:Logger) -> Dict:

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

    times = []
    prices = []
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime('%d.%m.%Y')
    list_dict = []
    try:
        await page.goto('https://www.metroturizm.com.tr/en/', timeout=99000)
    except (TimeoutError, PageError):
        logger.error('Page either crushed or time exceeded')
    try:
        orgin_input = await page.waitForXPath('//div/button[@title="İSTANBUL ANADOLU"]',{'visible': True, 'timeout': 50000})
        await orgin_input.click()
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/button[contains(text() ..."{ENDE}')
    try:
        write_orgin = await page.waitForXPath('//div/input[@class="form-control"]',{'visible': True, 'timeout': 50000})
        await write_orgin.type(origin)
        await page.keyboard.press('Enter')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not write {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/button[contains(text() ..."{ENDE}')
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
        dest_input = await page.waitForXPath('//div/button[@data-id="selectLandingTerminal"]',{'visible': True, 'timeout': 50000})
        await dest_input.click()
        write_dest = await page.xpath('//div/input[@aria-label="Search"]')
        await write_dest[0].type(destination)
        await page.keyboard.press('Enter')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/button[contains(text() ..."{ENDE}')
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
        await page.waitForXPath('//*[@id="inpSearchJourneyBusBoardingDate"]',{'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error('Can not find the date table')
    await page.evaluate('''(selector) => document.querySelector(selector).removeAttribute("readonly")''', "#inpSearchJourneyBusBoardingDate")
    await page.click('[id=inpSearchJourneyBusBoardingDate]',{'clickCount': 3})
    await page.keyboard.press('Backspace')
    await page.type('#inpSearchJourneyBusBoardingDate', date_)
    await page.keyboard.press('Enter')
    await page.evaluate('''(selector) => document.querySelector(selector).click()''',"#btnIndexSearchJourneys")
    try:
        await page.waitForXPath('//div[contains(@class,"journey-item")]',{'visible': True, 'timeout': 90000})
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
    time_info = await page.xpath('//div/span[contains(@class,"journey-item-hour ng-binding")]')
    price = await page.xpath('//div/span[contains(@class,"price ng-binding")]')
    for t in time_info:
        time_txt = await page.evaluate('(element) => element.textContent', t)
        times.append(time_txt)
        times = [x.replace('\n', '') for x in times]
        times = [x.strip('                  ') for x in times]
    departure_times = times[::2]
    arrival_times = times[1::2]
    string = "TL"
    for p in price:
        price_txt = await page.evaluate('(element) => element.textContent', p)
        prices.append(price_txt)
    prices = ["{}{}".format(i,string) for i in prices]
    for d, a, p in zip(departure_times,arrival_times, prices):
        list_dict.append({
            'date': date,
            'departure_time': d,
            'arrival_time': a,
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
