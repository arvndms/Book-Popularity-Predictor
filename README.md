# Book-Popularity-Predictor
## 📖 About the Project
This project is a data-driven exploration and machine learning endeavor aimed at predicting the popularity of books within the Indian and Middle Eastern reading markets. Using a curated dataset of ~4,000 titles scraped from Goodreads, the project identifies the hidden drivers of a book's "reach" beyond just its average rating.

The core challenge addressed here is the extreme skewness of reader engagement. While thousands of books are published, only a small fraction achieve mainstream success. This project moves beyond simple regression to create a Categorical Popularity Metric, turning the problem into a robust classification task.

## 📊 The Dataset
The data encompasses books published from the 1800s to 2024, with a primary focus on contemporary titles (2000s–2010s).

Scope: Multi-lingual (English, Arabic, Hindi, Tamil, Telugu, Kannada, Malayalam, and more).

Features: Metadata including Author, Multi-label Genre tags, Page Count, Publication Year, and Retail Price.

Volume: ~3,965 unique records.

## 🎯 The Popularity Metric
Unlike traditional models that attempt to predict exact rating counts, this project defines success through a Quantile-Based Tier System. This ensures the model is trained on balanced classes and provides more actionable predictions:

Bestseller (Top 15%): Viral hits and mainstream successes.

Rising (50-85%): Books with solid market traction and growing readership.

Niche (Bottom 50%): Specialized titles with a focused or emerging audience.

## ⚠️ Legal & Ethical Note

This project uses only publicly available data and official APIs for educational and research purposes.

No personal or sensitive data is collected
No login-protected or private content is accessed
Data is used strictly for learning and academic analysis
Users should respect the Terms of Service of data sources (Goodreads and Google Books API)
