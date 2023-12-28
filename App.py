from flask import Flask, render_template, request
from fuzzywuzzy import process
import pandas as pd
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import csv
import re

app = Flask(__name__)

stop_words = set(stopwords.words('english'))
porter = PorterStemmer()
product_data = pd.read_csv('products_details.csv')


@app.route('/')
def home():
    # top products
    top_rated_products = get_top_products(product_data)

    return render_template('chat.html', top_rated_products=top_rated_products)

@app.route('/user-response', methods=['POST'])

# chatbot interaction
def user_response():
    user_message = request.form.get('user_message', ' ')
    bot_response = get_response(user_message)
    return {'bot_response': bot_response, 'user_input': user_message}


def get_response(user_message):
    normalized_message = normalize_input(user_message)
    bot_response = find_product(normalized_message, product_data) 
    return bot_response



# Normalize user input
def normalize_input(user_message):
    
    normalized_message = user_message.lower()

    return normalized_message


# Find products based on user input

def find_product(normalized_message, product_data):


    # 1. Find the product with the highest rating

    if 'rating' in normalized_message:
        user_rating = [float(s) for s in normalized_message.split() if s.replace('.', '').isdigit()]
        print(f"User Rating: {user_rating}")

        if user_rating:
            user_rating = user_rating[0]
            print(f"User Rating (after extraction): {user_rating}")

            print("Columns in product_data:")
            print(product_data.columns)

            closest_rating_products = product_data.iloc[(product_data['Product Rating'] - user_rating).abs().argsort()[:2]]
            print("Closest Rating Products:")
            print(closest_rating_products)

            response = "I found products with the closest ratings:<br><br>"
            for index, row in closest_rating_products.iterrows():
                response += f"Name: {row['Product Name']}<br>Rating: {row['Product Rating']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
            return response
        
        elif user_rating > 5:
            return "Rating should be between 0 and 5."
        
        elif user_rating < 0:
            return "Rating should be between 0 and 5."
        
        elif 'best' in normalized_message:
            user_rating = 5
            print(f"User Rating (after extraction): {user_rating}")

            print("Columns in product_data:")
            print(product_data.columns)

            closest_rating_products = product_data.iloc[(product_data['Product Rating'] - user_rating).abs().argsort()[:2]]
            print("Closest Rating Products:")
            print(closest_rating_products)

            response = "I found products with the closest ratings:<br><br>"
            for index, row in closest_rating_products.iterrows():
                response += f"Name: {row['Product Name']}<br>Rating: {row['Product Rating']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
            return response
        else:
            return "No valid numeric rating found in the user input."



    # 2. Find the product with the price entered by the user

    elif 'price' in normalized_message:
        user_price_tokens = [int(s) for s in normalized_message.split() if s.isdigit()]
        if user_price_tokens:
            if len(user_price_tokens) == 1:
                user_price = user_price_tokens[0]
                
                # Convert 'Product Price' column to numeric
                product_data['Product Price'] = pd.to_numeric(product_data['Product Price'], errors='coerce')

                if 'above' in normalized_message:
                    filtered_products = product_data[product_data['Product Price'] > user_price]
                    comparison_operator = 'above'
                elif 'below' in normalized_message:
                    filtered_products = product_data[product_data['Product Price'] < user_price]
                    comparison_operator = 'below'
                elif 'under' in normalized_message:
                    filtered_products = product_data[product_data['Product Price'] < user_price]
                    comparison_operator = 'under'
                else:
                    products_matching_price = product_data[product_data['Product Price'] == user_price].head(2)
                    if not products_matching_price.empty:
                        response = "I found matching products:<br><br>"
                        for index, row in products_matching_price.iterrows():
                            response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                        return response

                    # If no exact match, find the nearest possible prices
                    nearest_prices = product_data.iloc[(product_data['Product Price'] - user_price).abs().argsort()[:2]]
                    response = "Here are products with the nearest prices:<br><br>"
                    for index, row in nearest_prices.iterrows():
                        response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                    return response

                if not filtered_products.empty:
                    response = f"I found products with prices {comparison_operator} {user_price}:<br><br>"
                    for index, row in filtered_products.iterrows():
                        response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                    return response
                else:
                    return f"Sorry, no products found {comparison_operator} the price {user_price}."
            elif len(user_price_tokens) == 2:
                lower_limit, upper_limit = sorted(user_price_tokens)
                filtered_products = product_data[(product_data['Product Price'] >= lower_limit) & (product_data['Product Price'] <= upper_limit)].head(2)
                
                if not filtered_products.empty:
                    response = f"I found products with prices between {lower_limit} and {upper_limit}:<br><br>"
                    for index, row in filtered_products.iterrows():
                        response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                    return response
                else:
                    return f"Sorry, no products found between {lower_limit} and {upper_limit}."
        else:
            return "Sorry, I couldn't find a valid price in your input."

            

    # 3. Find the product with the highest rating and lowest price

    elif 'best' in normalized_message:
        product_data['Score'] = product_data['Product Rating'] * product_data['Total reviews'] / product_data['Product Price']
        product_data['Score'] = product_data['Score'].fillna(0)
        best_products = product_data.sort_values(by=['Score'], ascending=False).head(2)
        response = "I have found the best products for you:<br><br>"
        for index, row in best_products.iterrows():
            response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
        return response
    


    # 4. Find the product with the lowest price and highest rating

    elif 'budget' in normalized_message:
        product_data['Score'] = product_data['Product Price'] / product_data['Product Rating']
        product_data['Score'] = product_data['Score'].fillna(0)
        best_products = product_data.sort_values(by=['Score'], ascending=True).head(2)
        response = "I found a budget friendly phone for:<br><br>"
        for index, row in best_products.iterrows():
            response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
        return response
    


    # 5. Find the product with the highest number of reviews

    elif 'reviews' in normalized_message:
        product_data['Score'] = product_data['Total reviews']
        product_data['Score'] = product_data['Score'].fillna(0)
        best_products = product_data.sort_values(by=['Score'], ascending=False).head(2)
        response = "I found phones based on rating:<br><br>"
        for index, row in best_products.iterrows():
            response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
        return response
    


    # 6. Find the product with the brand name
    elif 'brand' in normalized_message:
        result = find_products_by_brand(normalized_message, product_data)

        if isinstance(result, pd.DataFrame):
            response = "Found matching products:<br><br>"
            for index, row in result.iterrows():
                response += f"Name: {row['Product Name']}<br>Rating: {row['Product Rating']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
            return response
        else:
            return result
        
    # 7. Find the products with combinations
    elif 'price' in normalized_message and 'rating' in normalized_message:
        # Extract price and rating from user input
        price_keywords = ['above', 'below', 'under']
        rating_keywords = ['rating', 'best']

        user_price_tokens = [int(s) for s in normalized_message.split() if s.isdigit()]
        user_price = None

        for keyword in price_keywords:
            if keyword in normalized_message:
                if user_price_tokens:
                    user_price = user_price_tokens[0]

        user_rating = [float(s) for s in normalized_message.split() if s.replace('.', '').isdigit()]

        if user_rating:
            user_rating = user_rating[0]
        elif 'best' in normalized_message:
            user_rating = 5

        # Filter products based on price and rating
        if user_price is not None and user_rating is not None:
            product_data['Product Price'] = pd.to_numeric(product_data['Product Price'], errors='coerce')
            filtered_products = product_data[
                (product_data['Product Price'] < user_price) & (product_data['Product Rating'] >= user_rating)
            ].head(2)

            if not filtered_products.empty:
                response = f"I found products under the price of {user_price} and over or equal to a rating of {user_rating}:<br><br>"
                for index, row in filtered_products.iterrows():
                    response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Rating: {row['Product Rating']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                return response
            else:
                return f"Sorry, no products found under the price of {user_price} and over or equal to a rating of {user_rating}."

        else:
            return "Invalid combination of price and rating in the user input."


    # 8. Find the products with specs matching the query
    elif any(keyword in normalized_message for keyword in ['ram', 'storage', 'camera', 'display', 'rom']):
        query = normalized_message  # Adjust as needed based on your input processing
        # Assuming 'Product Specification' is the column containing detailed specifications
        matches = process.extract(query, product_data['Product Specification'], limit=10)

        threshold = 30
        valid_matches = [match for match in matches if match[1] >= threshold]

        if valid_matches:
            matched_specs = [match[0] for match in valid_matches]
            matched_rows = product_data[product_data['Product Specification'].isin(matched_specs)]

            response = "I found products with matching specifications:\n\n"
            for _, row in matched_rows.iterrows():
                response += f"Name: {row['Product Name']}<br>Price: {row['Product Price']}<br>Rating: {row['Product Rating']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
            return response

        else:
            return "Couldn't find a match based on specifications."
        
    # 9. Find the products with brand and price
    elif 'brand' in normalized_message and 'price' in normalized_message:
        # Extract brand and price from user input
        brand_keywords = ['apple', 'samsung', 'huawei', 'xiaomi']  # Add more brand keywords as needed
        price_keywords = ['above', 'below', 'under']

        user_brand = next((word for word in normalized_message.split() if word.lower() in brand_keywords), None)
        user_price_tokens = [int(s) for s in normalized_message.split() if s.isdigit()]

        if user_brand and user_price_tokens:
            user_price = user_price_tokens[0]
            comparison_operator = None

            for keyword in price_keywords:
                if keyword in normalized_message:
                    comparison_operator = keyword

            if comparison_operator:
                product_data['Product Price'] = pd.to_numeric(product_data['Product Price'], errors='coerce')
                if comparison_operator == 'above':
                    filtered_products = product_data[(product_data['Product Brand'].str.lower() == user_brand.lower()) & (product_data['Product Price'] > user_price)]
                elif comparison_operator == 'below':
                    filtered_products = product_data[(product_data['Product Brand'].str.lower() == user_brand.lower()) & (product_data['Product Price'] < user_price)]
                elif comparison_operator == 'under':
                    filtered_products = product_data[(product_data['Product Brand'].str.lower() == user_brand.lower()) & (product_data['Product Price'] < user_price)]
                else:
                    return "Invalid price comparison operator in the user input."

                if not filtered_products.empty:
                    response = f"I found {user_brand.capitalize()} products {comparison_operator} {user_price}:\n\n"
                    for index, row in filtered_products.iterrows():
                        response += f"Name: {row['Product Name']}<br>Rating: {row['Product Rating']}<br>Price: {row['Product Price']}<br>Product ID: {row['Product ID']}<br>Link: <a href='{row['Product URL']}'>{row['Product URL']}</a><br><br>"
                    return response
                else:
                    return f"Sorry, no {user_brand.capitalize()} products found {comparison_operator} the price {user_price}."
            else:
                return "No valid price comparison operator found in the user input."
        else:
            return "Invalid combination of brand and price in the user input."   



# function for finding the product brand

def find_products_by_brand(user_input, product_data):
    # Extract brand name from user input
    brand_keywords = ['from brand', 'brand']
    brand_name = None

    for keyword in brand_keywords:
        if keyword in user_input.lower():
            _, brand_name = user_input.lower().split(keyword, 1)
            brand_name = brand_name.strip().capitalize()
            break

    if brand_name:
        # Filter products by brand name
        filtered_products = product_data[product_data['Product Brand'] == brand_name]

        if not filtered_products.empty:
            return filtered_products
        else:
            return f"Sorry, can't find any products with the brand name {brand_name}."
    else:
        return "Brand information not found in the input."



# Top 5 products based on rating

def get_top_products(product_data):
    
    top_products = product_data.sort_values(by=['Product Rating'], ascending=False).head(5)
    
    return top_products

top_rated_products = get_top_products(product_data)

print(top_rated_products)


if __name__ == '__main__':

    app.run(debug=True)
