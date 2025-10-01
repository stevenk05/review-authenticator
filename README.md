# BestBuy Review Scraper

This script collects reviews from a BestBuy product page, checks for biased reviews using some keywords, calculates average ratings with and without biased reviews, and saves everything to a CSV file.

---

## What it does

- Visits the review pages for a product
- Scrolls to load all reviews
- Pulls reviewer name, rating, and review text
- Marks reviews as biased or not based on keywords
- Calculates average rating normally and without biased reviews
- Saves everything, including a summary, to `proj2reviews.csv`