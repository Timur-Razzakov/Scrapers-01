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
    departure_time = []
    arrival_time = []
    prices = []
    list_dict = []
    translator = google_translator()
    origin = translator.translate(origin, lang_tgt='lv').strip()
    destination = translator.translate(
        destination, lang_tgt='lv').strip()
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime('%d.%m.%Y')
    try:
        await page.goto('https://www.pv.lv/en/', timeout=90000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')

    '''
        Locate Fields
    '''
    try:
        await page.waitForXPath('//*[@id="from-station"]', {'visible': True, 'timeout': 50000})
    except TimeoutError:
        (f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="from-station"] ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#from-station")
    await page.type('[id=from-station]', origin)
    try: 
        option = await page.waitForXPath(f'//ul/li[contains(text(),"{origin}")]',{'visible': True, 'timeout': 10000}) 
        await option.click() 
    except Exception: 
        logger.error(f'{DARK_PURPLE} No valid origin {ENDE}{INBOX}{LIGHT_BLUE}"FINAL RESULTS"{ENDE}')
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
        await page.waitForXPath('//*[@id="to-station"]', {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="to-station"] ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#to-station")
    await page.type('[id=to-station]', destination)
    try: 
        option2 = await page.waitForXPath(f'//ul/li[contains(text(),"{destination}")]',{'visible': True, 'timeout': 10000}) 
        await option2.click() 
    except Exception: 
        logger.error(f'{DARK_PURPLE} No valid destination {ENDE}{INBOX}{LIGHT_BLUE}"FINAL RESULTS"{ENDE}')
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
    date_ = date_.replace("-", ".")
    try:
        await page.waitForXPath('//*[@id="switch-date-f"]', {'visible': True, 'timeout': 50000})
        await page.evaluate('''(selector) => document.querySelector(selector).removeAttribute("readonly")''',
                            "#switch-date-f")
        await page.click('[id=switch-date-f]', {'clickCount': 3})
        await page.keyboard.press('Backspace')
        await page.type('#switch-date-f', date_)
        await page.keyboard.press('Enter')

    except Exception:
        logger.error(
            f'{DARK_PURPLE}Date input not found {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="switch-date-f"] ..."{ENDE}')



    try:
        await page.waitForXPath('//div[contains(@class,"row")]', {'visible': True, 'timeout': 50000})
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
        
    dep_time = await page.xpath('//div/div[contains(@class,"col-3 col-time")]')
    arr_time = await page.xpath('//div/div[contains(@class,"col-4 col-time")]')
    price = await page.xpath('//div/div[contains(@class,"col-6 col-ticket-price")]')
    for i in dep_time:
        dp_time_txt = await page.evaluate('(element) => element.textContent', i)
        departure_time.append(dp_time_txt)
    del departure_time[0]

    for a in arr_time:
        ar_time_txt = await page.evaluate('(element) => element.textContent', a)
        arrival_time.append(ar_time_txt)
    del arrival_time[0]

    for p in price:
        price_txt = await page.evaluate('(element) => element.textContent', p)
        prices.append(price_txt)
        prices = [x.replace('\n', '') for x in prices]
        prices = [x.strip('   ') for x in prices]
    del prices[0]
    prices = [x[-6:] for x in prices]
    for d, a, p in zip(departure_time, arrival_time, prices):
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
    return  total_data
