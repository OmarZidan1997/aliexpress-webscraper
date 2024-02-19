import time
import logging
from selenium.webdriver.chrome.options import Options
# from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os  
import sys
from flask_cors import CORS
# for debugging remotely
import debugpy
debugpy.listen(("0.0.0.0", 5678))
load_dotenv()

app= Flask(__name__,template_folder='templates')
CORS(app)

logging.basicConfig(handlers=[logging.FileHandler('app.log'), logging.StreamHandler(sys.stdout)],
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# Get environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')


@app.route('/')
def home():
    return render_template('index.html')
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/crawl', methods= ['POST'])
def crawlUrl():
    data = request.json  # Get the JSON data sent to the API
    url = data.get('url') if data else None  # Extract the 'url' value from the JSON data
    if not url:
        # Return an error message if no URL is provided
        return jsonify({'error': 'No URL provided'}), 400
    # Call your function with the URL
    response = selenium_crawl_page(url)  # Make sure your function accepts a URL parameter
    print("returning this response" +response)
    logging.info("returning this response" +response)
    # Assuming your function returns a dictionary that you want to send as a JSON response
    return jsonify({'html': response})

def selenium_crawl_page(url):
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=chromedriver.log")
    chrome_options.add_argument("--disable-gpu")  # Disable GPU (optional, recommended for some environments)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, required on some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--page-load-strategy=none")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('log-level=3')
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument("--page-load-strategy=eager")  # Don't wait for full page load, improving speed for tests that don't require complete page resources.

    # Connect to Selenium Hub
    selenium_hub_url = 'http://selenium-hub:4444/wd/hub'
    browser = webdriver.Remote(command_executor=selenium_hub_url, options=chrome_options)
    #browser = webdriver.Chrome(options=chrome_options)
    print("Crawler initiated on url:" + url)
    logging.info("Crawler initiated on url:" + url)

    wait = WebDriverWait(browser, 10)
    browser.get(url)
    if check_for_captcha(browser):
        solve_captcha(browser)

    try:
        while True:
            try:
                # Attempt to find and click the "View More" button
                view_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'extend--btn--aAOvo5q')))
                view_more_button.click()
                #time.sleep(3)  # Adjust sleep time as needed
            except TimeoutException:
                # If the button is not clickable within the wait time
                print("No more 'View More' buttons to click or button not clickable.")
                logging.info("No more 'View More' buttons to click or button not clickable.")
                break
            except NoSuchElementException:
                # If the button is not found on the page
                print("No more 'View More' buttons found on the page.")
                logging.info("No more 'View More' buttons found on the page.")
                
                break
            except Exception as e:
                # For any other exceptions, log and break
                print(f"An unexpected error occurred: {e}")
                logging.critical(f"An unexpected error occurred: {e}")
                break
    finally:
        # This block executes regardless of what happens above
        try:
            # Attempt to capture content here
            div_element = browser.find_element(By.ID, 'nav-description')
            browser.execute_script("arguments[0].scrollIntoView(true);", div_element)
            wait.until(EC.presence_of_element_located((By.ID, 'nav-description')))
            product_description = browser.find_element(By.ID, 'nav-description').get_attribute('innerHTML')
        except NoSuchElementException:
            print("Product description not found.")
            product_description = "Product description not found."
        except Exception as e:
            print(f"An unexpected error occurred while trying to capture the product description: {e}")

            product_description = "An error occurred."
        finally:
            # Ensure the browser is always closed
            browser.quit()
            
    return product_description
def check_for_captcha(browser):
    try:
        browser.find_element(By.TAG_NAME,"punish-component")
        print("Captcha page detected.")
        logging.info("Captcha page detected.")
        # Here you can add more actions, like solving the captcha or logging
        return True  # Captcha page is detected
    except NoSuchElementException:
        print("No captcha page detected.")
        logging.info("No captcha page detected.")
        return False  # No captcha page detected
def wait_for_iframe_and_element(driver, iframe_locator, element_locator, timeout=30):
    try:
        # Wait for the iframe to be present and switch to it
        WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

        # Now wait for the element to be present in the iframe
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located(element_locator))

        # If the element is found, return it
        return driver.find_element(*element_locator)
    except Exception as e:
        # Handle the exception if the iframe or element is not found
        print(f"An exception occurred: {e}")
        logging.log(f"An exception occurred: {e}")
        return None
    finally:
        # Switch back to the default content
        driver.switch_to.default_content()
def solve_captcha(browser):
    try:
        retries = 0
        captcha_not_complete = True
        while  captcha_not_complete and retries != 2:
            retries += 1

            # Wait for the captcha slider to appear and be clickable
            slider = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.ID, "nc_1_n1z")))
            # Execute a script to drag the slider or simulate the sliding action
            # Note: This is a basic example and may need adjustment based on the captcha's specific requirements
            script = """
            var slider = arguments[0];
            var startX = slider.getBoundingClientRect().left + window.scrollX;
            var endX = window.innerWidth; // Get the width of the browser window
            var startY = slider.getBoundingClientRect().top + window.scrollY;

            // Start drag
            slider.dispatchEvent(new MouseEvent('mousedown', {clientX: startX, clientY: startY, bubbles: true}));

            // Calculate the move distance based on current slider position and window width
            var moveX = endX - startX;

            // Simulate smoother dragging to the edge
            let step = 2; // Smaller step for smoother movement
            let delay = 5; // Shorter delay for each step
            for(let i = 0; i <= moveX; i += step) {
            setTimeout(() => {
                slider.dispatchEvent(new MouseEvent('mousemove', {clientX: startX + i, clientY: startY, bubbles: true}));
            }, i * delay / step);
            }

            // End drag near the edge of the window
            setTimeout(() => {
            slider.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            }, moveX * delay / step + 100);
            """
            browser.execute_script(script, slider)
            found = False
            try:
                WebDriverWait(browser, 2).until(EC.presence_of_element_located((By.CLASS_NAME, "errloading")))
                found = True
                print("Element appeared.")
            except TimeoutException:
                print("No error raised, element not found within 2 seconds.")
            if found:
                captcha_not_complete = True
                print("Error detected, refreshing page...")
                logging.critical("Error detected, refreshing page...")
                browser.refresh()
            else:
                captcha_not_complete = False
    except TimeoutException:
        print("Timed out waiting for captcha to be solved.")
        logging.critical("Timed out waiting for captcha to be solved.")
    except NoSuchElementException:
        print("Captcha elements not found.")
        logging.critical("Captcha elements not found.")
    finally:
        # Switch back to the default content from iframe
        browser.switch_to.default_content()

if __name__ == '__main__':
    app.run()