import time
import logging
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
import os  
from flask_cors import CORS

ChromeDriverManager().install() 

load_dotenv()
app= Flask(__name__, template_folder='Template')
CORS(app)

# Get environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

# Suppress logging below ERROR level for selenium-wire
logging.getLogger('seleniumwire').setLevel(logging.ERROR)

@app.route('/crawl', methods= ['POST'])
def crawlUrl():
    data = request.json  # Get the JSON data sent to the API
    url = data.get('url') if data else None  # Extract the 'url' value from the JSON data
    if not url:
        # Return an error message if no URL is provided
        return jsonify({'error': 'No URL provided'}), 400
    print("visiting" + url)
    # Call your function with the URL
    response = selenium_crawl_page(url)  # Make sure your function accepts a URL parameter
    print("returning this response" +response)
    # Assuming your function returns a dictionary that you want to send as a JSON response
    return jsonify(response)


def selenium_crawl_page(url):

    chrome_options = Options()
    #proxy_server_url = "72.10.160.170"
    #chrome_options.add_argument(f'--proxy-server={proxy_server_url}')
    chrome_options.add_argument("--headless")  # Enable headless mode
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")  # Disable GPU (optional, recommended for some environments)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, required on some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    #chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36")
    chrome_options.add_argument('log-level=3')
    chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument("--disable-setuid-sandbox")

    browser = webdriver.Chrome(    options=chrome_options)
    print("Crawler initiated on url:" + url)

    wait = WebDriverWait(browser, 10)  
    browser.get(url)
    browser.save_screenshot('screenshot_before_finding_description.png')
    # Ensure the browser is always closed
    html_source = browser.page_source
    with open('page_source.html', 'w', encoding='utf-8') as file:
        file.write(html_source)
    try:
        while True:
            try:
                # Attempt to find and click the "View More" button
                view_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'extend--btn--aAOvo5q')))
                view_more_button.click()
                time.sleep(5)  # Adjust sleep time as needed
            except TimeoutException:
                # If the button is not clickable within the wait time
                print("No more 'View More' buttons to click or button not clickable.")
                break
            except NoSuchElementException:
                # If the button is not found on the page
                print("No more 'View More' buttons found on the page.")
                break
            except Exception as e:
                # For any other exceptions, log and break
                print(f"An unexpected error occurred: {e}")
                break
    finally:

        browser.save_screenshot('screenshot_before_closing_browser.png')
        # This block executes regardless of what happens above
        try:
            # Attempt to capture content here
            div_element = browser.find_element(By.ID, 'nav-description')
            browser.execute_script("arguments[0].scrollIntoView(true);", div_element)
            wait.until(EC.presence_of_element_located((By.ID, 'nav-description')))
            product_description = browser.find_element(By.ID, 'nav-description').get_attribute('innerHTML')
            print(product_description)
        except NoSuchElementException:
            print("Product description not found.")
            product_description = "Product description not found."
        except Exception as e:
            print(f"An unexpected error occurred while trying to capture the product description: {e}")
            product_description = "An error occurred."
        finally:
            # Ensure the browser is always closed
            html_source = browser.page_source
            with open("page_source.html", "w") as file:
                file.write(html_source)

            browser.quit()

    return product_description

if __name__ == '__main__':
    app.run()