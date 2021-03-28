from datetime import datetime
from pyppeteer.page import PageError, Page
from pyppeteer.errors import TimeoutError
from logging import Logger
from configurations.settings import DARK_PURPLE, ENDE, INBOX, LIGHT_BLUE
from typing import Dict


async def get_info(page, country_id, origin, origin_id, destination, destination_id, total_size, hash_id, order, date,
                   logger: Logger) -> Dict:
    dep_times = []
    prices = []
    date_ = datetime.fromisoformat(date)
    date_ = date_.strftime('%m/%d/%Y')
    list_dict = []
    try:
        await page.goto('https://metickets.krc.co.ke/', timeout=50000)
    except (TimeoutError, PageError):
        logger.error(f'{DARK_PURPLE}Page either crushed or time exceeded{ENDE}')
    try:
        await page.waitForXPath('//select[@id="train_type"]', {'visible': True, 'timeout': 10000})
        await page.select('#train_type', 'inter_county')
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="train_type"] ..."{ENDE}')

    try:
        await page.waitForXPath('//div/select[contains(@class,"form-control terminal_id")]',
                                {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/select[contains(@class,"form-control terminal_id")]..."{ENDE}')
    await page.click('[name=terminal_id]', {'clickCount': 1})
    await page.type('[name=terminal_id]', origin)
    await page.keyboard.press('Enter')
    try:
        await page.waitForXPath('//div/select[@id="destination_references"]', {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="destination_references"] ..."{ENDE}')
    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#destination_references")
    await page.type('#destination_references', destination)
    await page.keyboard.press('Enter')

    try:
        await page.waitForXPath('//*[@id="dateInput"]', {'visible': True, 'timeout': 50000})
    except TimeoutError:
        logger.error(f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//*[@id="dateInput"] ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#dateInput")
    await page.type('#dateInput', date_)
    await page.keyboard.press('Enter')
    try:
        await page.waitForXPath('//div/select[contains(@class,"form-control depature_time")]', timeout=10000)
    except TimeoutError:
        logger.error(
            f'{DARK_PURPLE}Could not locate {ENDE}{INBOX}{LIGHT_BLUE}"XPATH=//div/select[contains(@class,"form-control depature_time")] ..."{ENDE}')

    await page.evaluate('''(selector) => document.querySelector(selector).click()''', "#depature_time")
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('Enter')
    try:
        await page.waitForXPath('//div[@class="tab-content"]', {'visible': True, 'timeout': 10000})
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
    times = await page.xpath('//div/small/span[contains(@class,"span")]')
    price = await page.xpath('//div[2]/div[1]/dl/dd[contains(text(),"KSH")]')
    for i in times:
        time_txt = await page.evaluate('(element) => element.textContent', i)
        dep_times.append(time_txt)
    departure_times = dep_times[::2]
    arrival_times = dep_times[1::1]
    for p in price:
        price_txt = await page.evaluate('(element) => element.textContent', p)
        prices.append(price_txt)
    for d, a, p in zip(departure_times, arrival_times, prices):
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
