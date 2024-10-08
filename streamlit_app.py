import streamlit as st
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from ortools.linear_solver import pywraplp
import gdown
import os
import requests
from googlesearch import search
#from duckduckgo_search import DDGS
import webbrowser
import traceback
import streamlit.components.v1 as components
import traceback
import time
#git add tan_skin.jpg dark_skin.jpg wrinkles.jpg dark_circles.jpg redness.jpg acne.jpg fair_skin.jpg hyperpigmentation.jpg sensitive.jpg

# Streamlit app
st.title('Makeup Recommendations')

# User inputs
# User inputs
age_range = st.selectbox(
    'Select Age Range', 
    ['Under 20', '20-30', '30-40', '40-50', '50+']
)
skin_type = st.selectbox(
    'Select Skin Type', 
    ['Oily', 'Dry', 'Combination']
)
experience_level = st.selectbox(
    'Select Makeup Experience Level', 
    ['Beginner', 'Intermediate', 'Pro']
)
coverage = st.selectbox(
    'Select Makeup Coverage', 
    ['Light', 'Medium', 'Full']
)
max_budget = st.number_input(
    'Maximum Price Per Product', 
    min_value=0, 
    max_value=1000, 
    value=20
)


st.subheader('Select Skin Tone')
skin_tone_options =  {
    'Light': 'fair_skin.jpg',
    'Medium': 'tan_skin.jpg',
    'Deep': 'dark_skin.jpg'
}

# Create columns for displaying images
cols = st.columns(3)

# Display images in columns
for idx, (tone, image_path) in enumerate(skin_tone_options.items()):
    with cols[idx]:
        st.image(image_path, caption=tone, use_column_width=True)

# Radio button for selecting skin tone
selected_skin_tone = st.radio(
    'Select Your Skin Tone',
    options=list(skin_tone_options.keys())
)




# Checkbox options with images
conditions = {
    'Wrinkles': 'wrinkles.jpg',
    'Acne': 'acne.jpg',
    'Hyperpigmentation': 'hyperpigmentation.jpg',
    'Dark Circles': 'dark_circles.jpg',
    'Redness/Rosacea': 'redness.jpg',
    'Sensitive Skin': 'sensitive.jpg'
}

st.subheader('Skin Conditions')
# Create columns for skin concern images
user_conditions = {}
# Create columns for skin concern images (three per row)
num_conditions = len(conditions)
num_rows = (num_conditions + 2) // 3
for row in range(num_rows):
    cols_conditions = st.columns(3)
    for col in range(3):
        idx = row * 3 + col
        if idx >= num_conditions:
            break
        condition, image_path = list(conditions.items())[idx]
        with cols_conditions[col]:
            st.image(image_path, caption=condition, use_column_width=True, width=150)
            user_conditions[condition] = st.checkbox(condition)



st.subheader('Describe Yourself')
lifestyle = ['Working Professional', 'Mom/Parent', 'Student', 'Retired']

# Multiselect for selecting multiple options
lifestyle_options = st.multiselect(
    'What is Your Occupation? (You Can Select Multiple Options)',
    options=lifestyle
)

busy = ['1 - Not Busy/Active', '2 - Moderately Busy/Active', '3 - Super Busy/Active']

# Radio button for selecting skin tone
active_options = st.selectbox(
    'How Active/Busy Are You?',
    options= busy
)





# Define user profile with conditions
user_profile = {
    'professional_review': 1 if 'Working Professional' in lifestyle_options else 0, 
    'vibe_review': 1 if 'Retired' in lifestyle_options or age_range in ['40-50', '50+'] else 0, 
    'redness_review': 1 if user_conditions.get('Redness/Rosacea', True) else 0, 
    'dry_review': 1 if skin_type == 'Dry' else 0.5 if skin_type == 'Combination' else 0, 
    'light_coverage_review': 1 if coverage == 'Light' else 0, 
    'young_review': 1 if age_range in ['Under 20', '20-30'] or 'Student' in lifestyle_options else 0, 
    'mother_review': 1 if 'Busy Mom/Parent' in lifestyle_options else 0, 
    'skin_concerns_review': 1 if any(user_conditions.values()) else 0, 
    'white_review': 1 if selected_skin_tone == 'Light' else 0, 
    'tan_review': 1 if selected_skin_tone == 'Medium' else 0, 
    'acne_review': 1 if user_conditions.get('Acne', True) or skin_type == 'Oily' else 0.5 if skin_type == 'Combination' else 0,
    'black_review': 1 if selected_skin_tone == 'Deep' else 0, 
    'comfortable_wear_review': 1 if 'Working Professional' in lifestyle_options or active_options == '3 - Super Busy/Active'else 0.5 if active_options ==  '2 - Moderately Busy/Active'   else 0, 
    'coverage_review': 0 if coverage in ['Medium', 'Full'] else 1, 
    'medium_coverage_review': 1 if coverage == 'Medium' else 0, 
    'full_coverage_review': 1 if coverage == 'Full' else 0, 
    'easy_use_review': 1 if experience_level == 'Beginner' else 0, 
    'wrinkles_review': 1 if user_conditions.get('Wrinkles', True) else 0,
}

@st.cache_resource
def load_model():
    with open('random_forest_model.pkl', 'rb') as file:
        return pickle.load(file)

@st.cache_data
def load_data():
    product_data = pd.read_csv('reddit_product_embeddings.csv')
    product_info = pd.read_csv('cleaned_makeup_products.csv')
    return product_data, product_info


# Load your pretrained Random Forest model
model = load_model()

# Load product data
product_data,  product_info = load_data()
product_copy = product_data.copy()
product_copy = product_copy.drop(columns=['product_link_id', 'overall_product_rating'])
le = LabelEncoder()
product_copy['category'] = le.fit_transform(product_copy['category'])

# Load additional product info
product_info = product_info[['product_link_id', 'product_name', 'brand', 'price', 'category', 'description', 'product_link']]
product_info.rename(columns={'category': 'category_name'}, inplace=True)


# Add user profile features to product data
for col, val in user_profile.items(): 
    product_copy[col] = user_profile[col]


# Feature names and predictions
feature_names = model.feature_names_in_
product_copy = product_copy[feature_names]



predictions = model.predict_proba(product_copy)
product_copy['predicted_score'] = predictions[:, 0] + 2 * predictions[:, 1] + 3 * predictions[:, 2] + 4 * predictions[:, 3] + 5 * predictions[:, 4]
product_copy['product_link_id'] = product_data['product_link_id']
top_products = product_copy.sort_values(by='predicted_score', ascending=False)

# Merge with product info
product_budget = product_copy.copy()
product_budget = pd.merge(product_budget, product_info, how='inner', on='product_link_id')

# Define categories
skin_categories = ['Foundation', 'Tinted Moisturizer', 'BB & CC Creams']
allowed_skin_categories = []
allowed_makeup_products = []

if user_profile['light_coverage_review']:
    allowed_makeup_products = ['Blush', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
    if user_profile['easy_use_review']:
        allowed_skin_categories = ['Foundation', 'Tinted Moisturizer']
    elif user_profile['acne_review']:
        allowed_skin_categories = ['Foundation', 'BB & CC Creams']
    elif user_profile['comfortable_wear_review']:
        allowed_skin_categories = ['Tinted Moisturizer', 'BB & CC Creams']
    else: 
        allowed_skin_categories = ['Foundation', 'Tinted Moisturizer', 'BB & CC Creams']
elif user_profile['medium_coverage_review']:
    allowed_makeup_products = ['Face Primer', 'Blush', 'Bronzer', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
    allowed_skin_categories = ['Foundation', 'BB & CC Creams']
elif user_profile['full_coverage_review']:
    allowed_makeup_products = ['Face Primer', 'Blush', 'Bronzer', 'Contouring', 'Highlighter', 'Color Correcting', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
    allowed_skin_categories = ['Foundation']

# Optimization
B = max_budget # Using the upper bound of the budget slider

# Create the solver
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    st.error("Solver not created.")
    st.stop()

# Create variables
product_vars = {}
for i, row in product_budget.iterrows():
    product_vars[i] = solver.BoolVar(f'product_{row["product_link_id"]}')

# Create constraints
budget_constraints = []
for i, row in product_budget.iterrows():
    budget_constraint = solver.Constraint(0, B)
    budget_constraint.SetCoefficient(product_vars[i], row['price'])
    budget_constraints.append(budget_constraint)

categories = product_budget['category_name'].unique()
cat_constraints = []
allowed_skin_constraint = solver.Constraint(0, 1)
disallowed_constraint = solver.Constraint(0, 0)

for cat in allowed_skin_categories:
    cat_df = product_budget[product_budget['category_name'] == cat]
    for i, row in cat_df.iterrows():
        allowed_skin_constraint.SetCoefficient(product_vars[i], 1)

for cat in skin_categories:
    if cat in allowed_skin_categories: continue
    cat_df = product_budget[product_budget['category_name'] == cat]
    for i, row in cat_df.iterrows():
        disallowed_constraint.SetCoefficient(product_vars[i], 1)

for cat in categories:
    if cat in allowed_makeup_products: continue
    if cat in allowed_skin_categories: continue
    cat_df = product_budget[product_budget['category_name'] == cat]
    for i, row in cat_df.iterrows():
        disallowed_constraint.SetCoefficient(product_vars[i], 1)
            
for cat in categories:
    if cat in skin_categories: continue
    if cat not in allowed_makeup_products: continue
    cat_constraint = solver.Constraint(0, 1)
    cat_df = product_budget[product_budget['category_name'] == cat]
    for i, row in cat_df.iterrows():
        cat_constraint.SetCoefficient(product_vars[i], 1)
    cat_constraints.append(cat_constraint)

# Objective function
objective = solver.Objective()
for i, row in product_budget.iterrows():
    objective.SetCoefficient(product_vars[i], row['predicted_score'])
objective.SetMaximization()

# Solve the problem
status = solver.Solve()

# Display results
selected_products = {}
total_price = 0




@st.cache_resource
def get_first_google_result(product_name, info, max_retries=5, backoff_factor=2):
    retry_count = 0
    query = f'{product_name} {info}  site:amazon.com OR site:ulta.com OR site:sephora.com'

    while retry_count < max_retries:
        try:
            # Assuming `search` is a function that returns a generator or iterable of results
            result = search(query, num_results=1, safe=None, advanced=True)

            for r in result:
                if r.url and r.title and r.description:
                    link = r.url
                    title = r.title
                    description = r.description
                    print(link, title, description)
                    return link, title, description
            
            break  # Exit loop if successful

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                retry_count += 1
                wait_time = backoff_factor * (2 ** retry_count)
                print(f"429 error: Retry {retry_count}/{max_retries} in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise  # Re-raise exception if it's not a 429 error

        except Exception as e:
            # Handle other exceptions that might occur during the search
            print(f"An error occurred: {e}")
            retry_count += 1
            wait_time = backoff_factor * (2 ** retry_count)
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    # If all retries are exhausted
    print("Max retries exceeded. Unable to get Google result.")
    return None, None, None
    '''
    time.sleep(5)
    query = f'{product_name} {info}  site:amazon.com OR site:ulta.com OR site:sephora.com'
    q = product_name + ' amazon.com ulta.com sephora.com'# + info 
    result = search( query, num_results=1, safe=None,advanced=True)
    #result = DDGS().text(query,  region='us-en', safesearch='off', timelimit='y', max_results=3)
    for r in result:
        if r.url and r.title and r.description:
            link = r.url
            title = r.title
            description = r.description
            print(link, title, description)
            return link, title, description
    return None, None, None
    '''
 
    
def make_clickable(url):
    return f'<a href="{url}" target="_blank">View Product</a>'


if status == pywraplp.Solver.OPTIMAL:
    selected_products = []
    for i, row in product_budget.iterrows():
        if product_vars[i].solution_value() == 1:
            formatted_price = f"${float(row['price']):,.2f}"
            name = row['product_name']
            info = row['description']
            url = row['product_link']
            #link, title, description = get_first_google_result(name, info)
            #clickable = make_clickable(url)
            clickable = make_clickable(url)
            
            
            selected_products.append({
                'Category': row['category_name'],
                'Product Name': row['product_name'],
                'Price': formatted_price, 
                'URL': clickable
            })

else:
    st.write('The problem does not have an optimal solution.')



result_df = pd.DataFrame(selected_products)
result_df = result_df[result_df['Category'].notna()]

#st.write('Your Selected Products')
#st.write(result_df)

# Display each product with a clickable link and image in Streamlit

if not result_df.empty:
    st.write(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)



#formatted_total_price = f"${total_price:,.2f}"
#st.write(f"Total Price: {formatted_total_price}")
