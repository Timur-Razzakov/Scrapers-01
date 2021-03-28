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

    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime("%Y-%m-%d")
    try:
        await page.goto('https://www.busbud.com/en-gb', timeout=20000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')
        
    """
        button to prevent booking.com from opening
    """
    try:
        await page.waitForXPath('//*[@id="booking_com_checkbox"]', {'visible': True, 'timeout': 10000})
        await page.click('#booking_com_checkbox', {'clickCount': 1})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id=booking_com_checkbox] ..."{ENDE}')

    '''
        Locate Fields
    '''
    await page.click('#origin-c1ty-input', {'clickCount': 1})
    await page.type('#origin-c1ty-input', origin)

    '''
        Wait for prompts to appear
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
    await page.click('#destination-c1ty-input', {'clickCount': 1})
    await page.type('#destination-c1ty-input', destination)

    '''
        Wait for promts to appear
    '''
    try:
        arrival_choice = await page.waitForXPath(f'//span[contains(text(), "{destination}")]',
                                                 {'visible': True, 'timeout': 5000})
        await arrival_choice.click()
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

    """
        choose the date of departure
    """

    try:
        await page.waitForXPath('//*[@id="outbound-date-input"]', {'visible': True, 'timeout': 10000})
    except TimeoutError:
        logger.error('Can not find the date table')

    await page.evaluate('''(selector) => document.querySelector(selector).removeAttribute("readonly")''',
                        "#outbound-date-input")
    await page.click('[id=outbound-date-input]', {'clickCount': 3})
    await page.keyboard.press('Backspace')
    await page.type('#outbound-date-input', date_)
    await page.keyboard.press('Enter')
    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#outbound-date-input")

    try:
        cite_ver_1 = await page.waitForSelector('.departure-list', {'visible': True, 'timeout': 15000})
        ver_1 = True
    except Exception:
        ver_1 = False

    if ver_1:
        try:
            await page.waitForXPath('//*[@class="departure-list--flipper"]',
                                    {'visible': True, 'timeout': 15000})
        except Exception:
            logger.error(f'{DARK_PURPLE} No {ENDE}{INBOX}{LIGHT_BLUE}"FINAL RESULTS 1"{ENDE}')

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
        all_items = await page.xpath('//div[@data-portal-key="portal"]')

        list_dict = []

        for item in all_items:
            price = await item.querySelector('div.departure-card--price')
            times = await item.querySelectorAll('.text-std.text-right')
            dep_time = times[0]
            arr_time = times[1]

            price_text = await page.evaluate('(element) => element.textContent', price)
            dep_time_text = await page.evaluate('(element) => element.textContent', dep_time)
            arr_time_text = await page.evaluate('(element )=> element.textContent', arr_time)

            list_dict.append({
                'date': date,
                'departure_time': dep_time_text.strip(),
                'arrival_time': arr_time_text.strip(),
                'price': price_text.strip().replace('\xa0', ' ')
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

    else:
        try:
            all_items = await page.waitForXPath('//*[@data-cy="departure-card"]', {'visible': True, 'timeout': 15000})
        except TimeoutError:
            logger.error(f'{DARK_PURPLE} No {ENDE}{INBOX}{LIGHT_BLUE}"FINAL RESULTS 2"{ENDE}')

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
        list_dict = []
        prices = await all_items.xpath('//*[@data-cy="displayed-price"]')
        times = await all_items.xpath('//span[contains(text(),":")]')

        times_txt = [await page.evaluate('(element) => element.textContent', time) for time in times]
        prices_text = [await page.evaluate('(element) => element.textContent', price) for price in prices]
        dep_times_text = times_txt[0::2]
        arr_times_text = times_txt[1::2]

        for price, dep_time, arr_time in zip(prices_text, dep_times_text, arr_times_text):
            list_dict.append({
                'date': date,
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'price': price.strip().replace('\xa0', ' ')
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
