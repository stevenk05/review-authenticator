from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import random

# List of keywords for detecting biased reviews
BIAS_KEYWORDS = {
    "terrible", "horrible", "hate", "worst",
    "amazing", "best", "perfect", "flawless"
    }

def scroll(driver): 
    # Scroll down the page slowly to load all content
    scroll_pause_time = 1
    scroll_increment = 300

    last_height = driver.execute_script("return document.body.scrollHeight")
    consecutive_no_change = 0

    while consecutive_no_change < 15:
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            consecutive_no_change += 1
        else:
            consecutive_no_change = 0
        last_height = new_height

    print("Finished scrolling.")

def init_driver():
    # Initialize driver
    service = Service('./drivers/chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('start-maximized')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=service, options=options)

def scrape_reviews(driver, base_url):
    # Page number for which page of reviews we are on
    page_number = 1
    # Declare reviews as a list to append data to
    reviews = []

    # Loop until we have a break
    while True:
        # Declare loop for chromedriver, use f type string to include the base url and page index
        reviews_url = f"{base_url}&page={page_number}"
        # Debug statement
        print(f"Scraping page {page_number}...")

        driver.get(reviews_url)
        # Wait for page
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'review-item')]"))
            )
        except:
            print(f"Error: Reviews did not load on page {page_number}.")
            break

        # Extra random waiting to not be suspicious to website
        time.sleep(random.randint(1, 3))

        # Go down the page
        scroll(driver)

        review_elements = driver.find_elements(By.XPATH, "//li[contains(@class, 'review-item')]")
        print(f"Found {len(review_elements)} review items on page {page_number}")

        for review in review_elements:
            try:
                # Review comment
                try:
                    review_text = review.find_element(By.XPATH, ".//p[contains(@class, 'pre-white-space')]").text
                except:
                    review_text = "No review text found"

                # Review rating
                try:
                    rating_text = review.find_element(By.XPATH, ".//div[contains(@class, 'c-ratings-reviews')]/p[contains(@class, 'visually-hidden')]").text
                    if rating_text:
                        rating = float(rating_text.split()[1])
                except:
                    rating = None

                # Rating author name
                try:
                    reviewer = review.find_element(By.XPATH, ".//div[contains(@class, 'ugc-author')]/strong").text.strip()
                except:
                    reviewer = "Anonymous"

                # Rating bias as a string for the csv file
                if bias_check(review_text):
                    is_biased = "Yes"
                else:
                    is_biased = "No"

                reviews.append((reviewer, rating, is_biased, review_text))

            except Exception as e:
                print(f"Error extracting review on page {page_number}: {e}")
                continue

        # Rating bias as a string for the csv file
        if len(review_elements) < 20:
            print(f"Reached the end of available reviews on page {page_number}.")
            break

        page_number += 1

    return reviews

def bias_check(review_text):
    # Check if the review text contains any bias keywords
    return any(keyword in review_text.lower() for keyword in BIAS_KEYWORDS)

def calculate_ratings(reviews):
    # Calculate original and adjusted average ratings
    ratings = []
    for review in reviews:
        _, rating, _, _ = review
        if rating is not None:
            ratings.append(rating)
    else:
        rating = 0

    original_avg_rating = sum(ratings) / len(ratings)

    non_biased_ratings = [rating for _, rating, is_biased, _ in reviews if rating is not None and is_biased == "No"]
    non_biased_ratings = []
    for review in reviews:
        _, rating, is_biased, _ = review
        if rating is not None and is_biased == "No":
            non_biased_ratings.append(rating)

    adjusted_avg_rating = sum(non_biased_ratings) / len(non_biased_ratings)

    return original_avg_rating, adjusted_avg_rating

def save_to_csv(reviews, original_avg_rating, adjusted_avg_rating):
    # Save reviews and ratings to a single csv file
    filename = "proj2reviews.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Reviewer', 'Rating', 'Biased', 'Review Text'])
        writer.writerows(reviews)

        original_avg_rating = round(original_avg_rating, 2)
        adjusted_avg_rating = round(adjusted_avg_rating, 2)

        # Add a blank line and summary at the end
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Original Average Rating', original_avg_rating])
        writer.writerow(['Adjusted Average Rating (Non-Biased)', adjusted_avg_rating])

    print(f"Results saved to {filename}")

def main():
    # Main function to scrape, analyze, and save reviews
    base_url = "https://www.bestbuy.com/site/reviews/lg-65-class-ut70-series-led-4k-uhd-smart-webos-tv-2024/6593578?variant=A"

    print("Scraping reviews...")
    driver = init_driver()

    # Get list of reviews holding the review's text, author, rating, and bias (Yes/No)
    reviews = scrape_reviews(driver, base_url)
    driver.quit()

    # As long as the item has reviews
    if reviews:
        print(f"Scraped {len(reviews)} reviews.")
        original_avg_rating, adjusted_avg_rating = calculate_ratings(reviews)
        save_to_csv(reviews, original_avg_rating, adjusted_avg_rating)
    else:
        print("No reviews found.")

main()