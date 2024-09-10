# main.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import spacy
import fitz
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer

# Load spaCy's pre-trained model
nlp = spacy.load("en_core_web_sm")

# Load pre-trained GPT-2 model and tokenizer
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Step 0: Collect User Input
def get_user_input():
    site_url = input("Enter the job site URL (e.g., linkedin.com): ")
    job_profile = input("Enter the job profile you are looking for (e.g., Software Engineer Intern): ")
    resume_path = input("Enter the path to your resume file: ")
    name = input("Enter your name: ")
    address = input("Enter your address: ")
    phone = input("Enter your phone number: ")
    email = input("Enter your email: ")
    return site_url, job_profile, resume_path, name, address, phone, email

# Step 1: Login to the Job Site
def login_to_site(driver, site_url, username, password):
    driver.get(site_url)
    time.sleep(2)  # Adjust sleep time as necessary

    # Example for LinkedIn login
    if 'linkedin' in site_url:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button.click()

        time.sleep(2)  # Adjust sleep time as necessary

# Step 2: Search for Job Listings
def search_jobs(driver, job_profile):
    # Example for LinkedIn job search
    if 'linkedin' in driver.current_url:
        job_search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Search jobs')]"))
        )
        job_search_bar.send_keys(job_profile)
        job_search_bar.send_keys(Keys.RETURN)
        
        time.sleep(2)  # Adjust sleep time as necessary

        job_listings = driver.find_elements(By.XPATH, "//ul[@class='jobs-search__results-list']/li")
        
        jobs = []
        for job in job_listings:
            title = job.find_element(By.XPATH, ".//a[@class='job-card-list__title']").text
            company = job.find_element(By.XPATH, ".//a[@class='job-card-container__link job-card-container__company-name ember-view']").text
            location = job.find_element(By.XPATH, ".//span[@class='job-card-container__metadata-item']").text
            job_link = job.find_element(By.XPATH, ".//a[@class='job-card-list__title']").get_attribute('href')
            jobs.append((title, company, location, job_link))

        return jobs

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

# Extract information using spaCy
def extract_info_from_text(text):
    doc = nlp(text)
    demographic_info = {}
    project_details = []

    # Extract demographic info
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            demographic_info["Name"] = ent.text
        elif ent.label_ == "GPE":
            demographic_info["Location"] = ent.text
        elif ent.label_ == "ORG":
            demographic_info["Organization"] = ent.text
        elif ent.label_ == "EMAIL":
            demographic_info["Email"] = ent.text
        elif ent.label_ == "PHONE":
            demographic_info["Phone"] = ent.text

    # Extract project details
    for sent in doc.sents:
        if "project" in sent.text.lower():
            project_details.append(sent.text)

    return demographic_info, project_details

# Generate answers using GPT-2
def generate_answer(question, context):
    input_text = f"Question: {question}\nContext: {context}\nAnswer:"
    response = generator(input_text, max_length=150, num_return_sequences=1)
    answer = response[0]['generated_text'].split('Answer:')[1].strip()
    return answer

# Apply to jobs
def apply_to_jobs(driver, jobs, resume_path, name, address, phone, email):
    text = extract_text_from_pdf(resume_path)
    demographic_info, project_details = extract_info_from_text(text)
    context = f"Name: {name}, Address: {address}, Phone: {phone}, Email: {email}, Projects: {', '.join(project_details)}"

    for job in jobs:
        driver.get(job[3])
        time.sleep(2)  # Adjust sleep time as necessary

        # Example for LinkedIn job application form filling
        try:
            apply_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Easy Apply')]"))
            )
            apply_button.click()

            time.sleep(2)  # Adjust sleep time as necessary

            # Extract questions from form (example assumes form contains input elements)
            form_fields = driver.find_elements(By.XPATH, "//form//input")
            for field in form_fields:
                question = field.get_attribute("aria-label")  # Assuming the question is in the aria-label attribute
                if "name" in question.lower():
                    answer = name
                elif "email" in question.lower():
                    answer = email
                elif "phone" in question.lower():
                    answer = phone
                else:
                    answer = generate_answer(question, context)
                field.send_keys(answer)

            # Upload the resume
            resume_upload_field = driver.find_element(By.XPATH, "//input[@type='file']")
            resume_upload_field.send_keys(resume_path)

            # Submit the form
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()

            time.sleep(2)  # Adjust sleep time as necessary

            print(f"Application submitted for {job[0]} at {job[1]}")

        except Exception as e:
            print(f"Failed to apply for {job[0]} at {job[1]}: {e}")

# Main function to run the steps
def main():
    site_url, job_profile, resume_path, name, address, phone, email = get_user_input()

    # Setup Selenium WebDriver
    driver = webdriver.Chrome()  # Make sure to have ChromeDriver installed and in PATH

    # Login (For this example, credentials are hardcoded, consider using a secure method)
    username = "your_username"
    password = "your_password"
    login_to_site(driver, site_url, username, password)

    # Search for jobs
    jobs = search_jobs(driver, job_profile)
    for job in jobs:
        print(f"Title: {job[0]}, Company: {job[1]}, Location: {job[2]}, Link: {job[3]}")

    # Apply to jobs
    apply_to_jobs(driver, jobs, resume_path, name, address, phone, email)

    driver.quit()

if __name__ == "__main__":
    main()
