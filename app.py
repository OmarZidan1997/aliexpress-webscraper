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
from flask_cors import CORS
load_dotenv()


app= Flask(__name__,template_folder='templates')
CORS(app)

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# Get environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

# Suppress logging below ERROR level for selenium-wire
logging.getLogger('seleniumwire').setLevel(logging.DEBUG)

@app.route('/')
def home():
    return render_template('index.html')
    
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
    # Assuming your function returns a dictionary that you want to send as a JSON response
    return jsonify({'html': response})

def selenium_crawl_page(url):
    chrome_options = Options()
    #chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('window-size=1200x600')
    chrome_options.add_argument("--disable-gpu")  # Disable GPU (optional, recommended for some environments)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, required on some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--page-load-strategy=none")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36")
    chrome_options.add_argument('log-level=3')
    #chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument(r"--user-data-dir=C:\Users\scraper\AppData\Local\Google\Chrome SxS\User Data");
    chrome_options.add_argument('--profile-directory=Default');
    chrome_options.add_argument("--page-load-strategy=eager")  # Don't wait for full page load, improving speed for tests that don't require complete page resources.
    chrome_options.binary_location=r'C:\Users\scraper\AppData\Local\Google\Chrome SxS\Application\chrome.exe'
    # chrome_options.set_capability('command_executor', 'http://10.154.0.2:4444')
    # Initialize the Remote WebDriver with Selenium Wire support
    browser = webdriver.Remote(command_executor='http://10.154.0.2:4444' , options=chrome_options)
    #browser = webdriver.Chrome(options=chrome_options)
    print("Crawler initiated on url:" + url)

    wait = WebDriverWait(browser, 10)
    browser.get(url)
    if check_for_captcha(browser):
        solve_captcha(browser)
    browser.save_screenshot('screenshot_before_finding_description.png')
    # Ensure the browser is always closed
    html_source = browser.page_source
    # Using with statement for file operations is recommended as it handles opening and closing the file automatically
    with open("page_source.html", 'w', encoding='utf-8') as file:
        file.write(html_source)
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
            browser.quit()
            
    return product_description
def check_for_captcha(browser):
    try:
        browser.find_element(By.TAG_NAME,"punish-component")
        print("Captcha page detected.")
        # Here you can add more actions, like solving the captcha or logging
        return True  # Captcha page is detected
    except NoSuchElementException:
        print("No captcha page detected.")
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
        return None
    finally:
        # Switch back to the default content
        driver.switch_to.default_content()

def solve_captcha(browser):
    try:
        retries = 0
        captcha_not_complete = True
        while  captcha_not_complete and retries != 3:
            retries += 1
            # Wait for the captcha slider to appear and be clickable
            slider = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.ID, "nc_1_n1z")))
            
            # Execute a script to drag the slider or simulate the sliding action
            # Note: This is a basic example and may need adjustment based on the captcha's specific requirements
            script = """
            var slider = arguments[0];
            var event = new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            slider.dispatchEvent(event);

            // Simulating the mouse move might require more complex logic depending on the captcha
            var moveEvent = new MouseEvent('mousemove', {
                clientX: slider.getBoundingClientRect().left + 100,
                clientY: slider.getBoundingClientRect().top + 10,
                bubbles: true,
                cancelable: true,
                view: window
            });
            document.dispatchEvent(moveEvent);

            var upEvent = new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            document.dispatchEvent(upEvent);
            """
            browser.execute_script(script, slider)
            refresh_elements = browser.find_elements(By.ID, "nc_1_refresh1")
            if refresh_elements:
                print("Error detected, refreshing page...")
                browser.refresh()
                WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.ID, "nc_1_n1z")))
                browser.save_screenshot('screenshot_page_refresh_done.png')
            captcha_not_complete = False
    except TimeoutException:
        print("Timed out waiting for captcha to be solved.")
    except NoSuchElementException:
        print("Captcha elements not found.")
    finally:
        # Switch back to the default content from iframe
        browser.switch_to.default_content()
    
if __name__ == '__main__':
    app.run()